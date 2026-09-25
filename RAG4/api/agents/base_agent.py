# api/agents/base_agent.py
from abc import ABC, abstractmethod
import logging
from typing import AsyncIterator

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def process(self, data):
        """Основной метод обработки данных"""
        pass

    async def stream_process(self, data) -> AsyncIterator[str]:
        """Async generator for streaming responses.
        Override in subclasses that support streaming."""
        raise NotImplementedError
        # This line is never reached but satisfies the async generator type
        if False:
            yield ""

    def log(self, message: str):
        print(f"[{self.name}] {message}")