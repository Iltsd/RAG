import os
from langchain_core.tools import tool


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_path(path: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(BASE_DIR, path))


@tool
def read_file(path: str) -> str:
    """Read the contents of a file. Path is relative to project root unless absolute."""
    full = _resolve_path(path)
    try:
        with open(full, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at {full}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Path is relative to project root unless absolute. Overwrites existing files."""
    full = _resolve_path(path)
    try:
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content.encode('utf-8'))} bytes to {full}"
    except Exception as e:
        return f"Error writing file: {e}"
