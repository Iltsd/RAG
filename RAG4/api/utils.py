import re


def strip_markdown(text: str) -> str:
    text = re.sub(r'\*\*|__|~~|`', '', text)
    text = re.sub(r'[*_~#>]', '', text)
    text = re.sub(r'^[\s]*-[\s]', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text
