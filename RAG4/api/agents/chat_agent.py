from .base_agent import BaseAgent
from langchain_utils import get_rag_chain, retriever
from db_utils import get_chat_history, insert_application_logs
import uuid
from typing import AsyncIterator, List
from langchain_core.messages import HumanMessage, AIMessage
from tools.tool_executor import build_tools_map, run_tool_loop, run_tool_loop_stream
from tools import register_all_tools
from db_utils import insert_tool_log, get_tool_logs

class ChatAgent(BaseAgent):
    def __init__(self, provider=None, preprocessing_enabled=True, retrieval_enabled=True):
        super().__init__("ChatAgent")
        self.provider = provider
        self.preprocessing_enabled = preprocessing_enabled
        self.retrieval_enabled = retrieval_enabled

    def _dicts_to_messages(self, chat_history):
        messages = []
        for msg in chat_history:
            role = msg.get("role", "human")
            content = msg.get("content", "")
            if role == "human":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        return messages

    def _format_history(self, chat_history):
        formatted = []
        for msg in chat_history:
            role = msg.get("role", "human")
            content = msg.get("content", "")
            formatted.append((role, content))
        return formatted

    def process(self, query_input):
        self.log(f"Processing: {query_input.question[:50]}...")

        session_id = query_input.session_id or str(uuid.uuid4())
        chat_history = get_chat_history(session_id)
        formatted_history = self._format_history(chat_history)
        preprocessing = getattr(query_input, 'preprocessing_enabled', self.preprocessing_enabled)
        retrieval = getattr(query_input, 'retrieval_enabled', self.retrieval_enabled)
        tools_enabled = getattr(query_input, 'tools_enabled', False)

        if hasattr(self.provider, 'llm') and self.provider.llm is not None:
            llm = self.provider.llm
            history_messages = self._dicts_to_messages(chat_history) if preprocessing else []

            if tools_enabled:
                tools_map = build_tools_map(register_all_tools())
                messages = history_messages + [HumanMessage(content=query_input.question)]
                answer, tool_calls = run_tool_loop(llm, tools_map, messages)
                for tc in tool_calls:
                    self.log(f"Tool: {tc['tool']} → {tc['result'][:100]}")
                    insert_tool_log(session_id, tc["tool"], tc["args"], tc["result"])
            elif retrieval:
                chain = get_rag_chain(llm, with_preprocessing=preprocessing, retrieval_enabled=True)
                result = chain.invoke({
                    "input": query_input.question,
                    "chat_history": history_messages
                })
                answer = result["answer"]
                for i, doc in enumerate(result.get("context", [])):
                    self.log(f"Source {i+1}: {doc.page_content[:100]}...")
            else:
                chain = get_rag_chain(llm, with_preprocessing=preprocessing, retrieval_enabled=False)
                result = chain.invoke({
                    "input": query_input.question,
                    "chat_history": history_messages,
                    "context": []
                })
                answer = result if isinstance(result, str) else result["answer"]
        else:
            if retrieval:
                context_docs = retriever.invoke(query_input.question)
                context = "\n\n".join([d.page_content for d in context_docs])
            else:
                context = ""
            answer = self.provider.ainvoke(query_input.question, context, formatted_history)

        insert_application_logs(session_id, query_input.question, answer, query_input.model.value if hasattr(query_input.model, 'value') else str(query_input.model))
        self.log(f"Response generated for session {session_id}")

        return {
            "answer": answer,
            "session_id": session_id,
            "model": query_input.model
        }

    async def stream_process(self, query_input) -> AsyncIterator[str]:
        self.log(f"Stream processing: {query_input.question[:50]}...")

        session_id = query_input.session_id or str(uuid.uuid4())
        chat_history = get_chat_history(session_id)
        formatted_history = self._format_history(chat_history)
        preprocessing = getattr(query_input, 'preprocessing_enabled', self.preprocessing_enabled)
        retrieval = getattr(query_input, 'retrieval_enabled', self.retrieval_enabled)
        tools_enabled = getattr(query_input, 'tools_enabled', False)

        full_response = ""

        if hasattr(self.provider, 'llm') and self.provider.llm is not None:
            llm = self.provider.llm
            history_messages = self._dicts_to_messages(chat_history) if preprocessing else []

            if tools_enabled:
                tools_map = build_tools_map(register_all_tools())
                messages = history_messages + [HumanMessage(content=query_input.question)]
                async for event in run_tool_loop_stream(llm, tools_map, messages):
                    if event.startswith("[TOOL_CALL:"):
                        yield event
                    elif event.startswith("[TOOL_RESULT:"):
                        yield event
                    elif event.startswith("[TOOL_ERROR:"):
                        yield event
                    else:
                        full_response += event
                        yield event
            elif retrieval:
                chain = get_rag_chain(llm, with_preprocessing=preprocessing, retrieval_enabled=True)
                async for chunk in chain.astream({
                    "input": query_input.question,
                    "chat_history": history_messages
                }):
                    if "answer" in chunk:
                        token = chunk["answer"]
                        full_response += token
                        yield token
            else:
                chain = get_rag_chain(llm, with_preprocessing=preprocessing, retrieval_enabled=False)
                async for chunk in chain.astream({
                    "input": query_input.question,
                    "chat_history": history_messages,
                    "context": []
                }):
                    if isinstance(chunk, dict) and "answer" in chunk:
                        token = chunk["answer"]
                    elif isinstance(chunk, str):
                        token = chunk
                    else:
                        continue
                    full_response += token
                    yield token
        else:
            if retrieval:
                context_docs = await retriever.ainvoke(query_input.question)
                context = "\n\n".join([d.page_content for d in context_docs])
            else:
                context = ""
            async for token in self.provider.stream_chat(query_input.question, context, formatted_history):
                full_response += token
                yield token

        insert_application_logs(session_id, query_input.question, full_response, query_input.model.value if hasattr(query_input.model, 'value') else str(query_input.model))
        self.log(f"Streaming complete for session {session_id}")
        yield f"[SESSION_ID:{session_id}]"