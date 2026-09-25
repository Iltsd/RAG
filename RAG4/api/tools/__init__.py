from .shell import run_shell
from .file_ops import read_file, write_file
from .web import fetch_url


def register_all_tools():
    return [run_shell, read_file, write_file, fetch_url]
