import subprocess
from langchain_core.tools import tool


@tool
def run_shell(command: str) -> str:
    """Execute a shell command and return its output. Use this for file operations, system queries, and any command-line tasks."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout or "(no output)"
        else:
            return f"Error (code {result.returncode}): {result.stderr or result.stdout}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {e}"
