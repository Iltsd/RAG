from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Dict
import os
import yaml
from dotenv import load_dotenv


def load_config(path: str = None) -> dict:
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.yaml")
    load_dotenv()
    with open(path) as f:
        config = yaml.safe_load(f)

    def _sub_env(val):
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            return os.getenv(val[2:-1], "")
        return val

    def _apply_recursive(obj):
        if isinstance(obj, dict):
            return {k: _apply_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_apply_recursive(v) for v in obj]
        elif isinstance(obj, str):
            return _sub_env(obj)
        return obj

    return _apply_recursive(config)


PROVIDER_MAP = {}


def register_provider(name: str):
    def decorator(cls):
        PROVIDER_MAP[name] = cls
        return cls
    return decorator


class LLMProvider(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    async def stream_chat(self, prompt: str, context: str, history: list) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def ainvoke(self, prompt: str, context: str, history: list) -> str:
        pass

    @staticmethod
    def _build_messages(prompt: str, context: str, history: list, system_prompt: str = None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        for msg in history:
            if isinstance(msg, tuple):
                role = "user" if msg[0] == "human" else "assistant"
                messages.append({"role": role, "content": msg[1]})
            elif isinstance(msg, dict):
                messages.append(msg)
        messages.append({"role": "user", "content": prompt})
        return messages


@register_provider("ollama")
class OllamaProvider(LLMProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        from langchain_community.chat_models import ChatOllama
        self.llm = ChatOllama(
            model=config["model"],
            temperature=config.get("temperature", 0.7),
            num_predict=config.get("max_tokens", 2048),
            options=config.get("options", {})
        )

    async def stream_chat(self, prompt: str, context: str, history: list) -> AsyncIterator[str]:
        messages = self._build_messages(prompt, context, history)
        async for chunk in self.llm.astream(messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    async def ainvoke(self, prompt: str, context: str, history: list) -> str:
        messages = self._build_messages(prompt, context, history)
        result = await self.llm.ainvoke(messages)
        return result.content


@register_provider("openai")
class OpenAIProvider(LLMProvider):
    def __init__(self, config: dict):
        super().__init__(config)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=config["api_key"],
            base_url=config.get("base_url", "https://api.openai.com/v1")
        )
        self.model = config["model"]

    async def stream_chat(self, prompt: str, context: str, history: list, system_prompt: str = None) -> AsyncIterator[str]:
        messages = self._build_messages(prompt, context, history, system_prompt)
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def ainvoke(self, prompt: str, context: str, history: list, system_prompt: str = None) -> str:
        messages = self._build_messages(prompt, context, history, system_prompt)
        result = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False
        )
        return result.choices[0].message.content


def create_provider(config: dict = None) -> LLMProvider:
    if config is None:
        config = load_config()
    llm_config = config["llm"]
    provider_name = llm_config["provider"]
    if provider_name not in PROVIDER_MAP:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(PROVIDER_MAP.keys())}")
    return PROVIDER_MAP[provider_name](llm_config)
