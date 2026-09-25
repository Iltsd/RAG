import json
from typing import AsyncIterator, List, Callable
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def _build_tools_description(tools_map: dict) -> str:
    lines = [
        "You have access to the following tools. When you need to use one, respond with:",
        'TOOL_CALL: {"tool": "tool_name", "args": {...}}',
        "",
        "Available tools:",
    ]
    for name, fn in tools_map.items():
        doc = (fn.__doc__ or fn.description or "").strip()
        lines.append(f"- {name}: {doc}")
    lines.extend([
        "",
        "After calling a tool, you will receive the result. Then continue your response normally.",
        "You can call multiple tools in sequence. Never make up tool results — always wait for the actual output.",
    ])
    return "\n".join(lines)


def _parse_tool_call(text: str):
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("TOOL_CALL:"):
            try:
                payload = json.loads(line[len("TOOL_CALL:"):])
                return payload.get("tool"), payload.get("args", {})
            except (json.JSONDecodeError, TypeError):
                return None, None
    return None, None


def _execute_tool(tools_map: dict, tool_name: str, tool_args: dict) -> str:
    tool_fn = tools_map.get(tool_name)
    if not tool_fn:
        return f"Error: Unknown tool '{tool_name}'"
    try:
        result = tool_fn.invoke(tool_args)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


async def _execute_tool_async(tools_map: dict, tool_name: str, tool_args: dict) -> str:
    tool_fn = tools_map.get(tool_name)
    if not tool_fn:
        return f"Error: Unknown tool '{tool_name}'"
    try:
        if hasattr(tool_fn, 'ainvoke'):
            result = await tool_fn.ainvoke(tool_args)
        else:
            result = tool_fn.invoke(tool_args)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {e}"


def build_tools_map(tools: List[Callable]) -> dict:
    return {t.name: t for t in tools}


def _is_tool_call(text: str) -> bool:
    return "TOOL_CALL:" in text


def run_tool_loop(llm, tools_map: dict, messages: list, max_iterations: int = 5) -> tuple:
    tools_desc = _build_tools_description(tools_map)
    sys_msg = SystemMessage(content=tools_desc)
    current_messages = [sys_msg] + list(messages)
    all_tool_calls = []

    for _ in range(max_iterations):
        result = llm.invoke(current_messages)
        content = result.content or ""

        tool_name, tool_args = _parse_tool_call(content)
        if not tool_name:
            return content, all_tool_calls

        current_messages.append(result)
        output = _execute_tool(tools_map, tool_name, tool_args)
        all_tool_calls.append({
            "tool": tool_name,
            "args": json.dumps(tool_args),
            "result": output[:500],
        })
        current_messages.append(HumanMessage(content=f"Tool result ({tool_name}): {output[:2000]}"))

    return "Error: Max tool iterations reached", all_tool_calls


async def run_tool_loop_stream(
    llm, tools_map: dict, messages: list, max_iterations: int = 5,
) -> AsyncIterator[str]:
    tools_desc = _build_tools_description(tools_map)
    sys_msg = SystemMessage(content=tools_desc)
    current_messages = [sys_msg] + list(messages)

    for iteration in range(max_iterations):
        collected = ""
        tool_name = None

        async for chunk in llm.astream(current_messages):
            token = chunk.content if hasattr(chunk, 'content') else str(chunk)
            collected += token

            if "TOOL_CALL:" in collected and tool_name is None:
                name, args = _parse_tool_call(collected)
                if name:
                    tool_name = name
                    tool_args = args

        if not tool_name:
            yield collected
            return

        yield f"[TOOL_CALL:{tool_name}|{json.dumps(tool_args)}]"
        current_messages.append(AIMessage(content=collected))

        output = await _execute_tool_async(tools_map, tool_name, tool_args)
        if output.startswith("Error:"):
            yield f"[TOOL_ERROR:{tool_name}|{output[:500]}]"
        else:
            yield f"[TOOL_RESULT:{tool_name}|{output[:500]}]"

        current_messages.append(HumanMessage(content=f"Tool result ({tool_name}): {output[:2000]}"))

    yield "Error: Max tool iterations reached"
