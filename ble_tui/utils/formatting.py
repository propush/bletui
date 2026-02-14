import json
import re
from typing import Optional


def hex_groups(data: bytes) -> str:
    if not data:
        return ""
    h = data.hex()
    return " ".join(h[i : i + 2] for i in range(0, len(h), 2))


def try_parse_json(data: bytes) -> Optional[str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return None
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":"))


def pretty_json_with_highlighting(data: bytes, indent: int = 2) -> Optional[str]:
    """Return pretty JSON with Rich markup for syntax highlighting."""
    try:
        text = data.decode("utf-8")
        obj = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    pretty = json.dumps(obj, indent=indent, ensure_ascii=True)

    # Escape only opening brackets to prevent Rich/Textual from interpreting
    # them as markup tags. Closing brackets ] don't need escaping (only [
    # starts a markup tag). Escaping ] with \] causes a visible backslash.
    pretty = pretty.replace("[", r"\[")

    # Apply Rich markup for color-coding:
    # - Keys (quoted strings before colons): cyan
    # - String values: green
    # - Numbers: yellow
    # - Booleans/null: magenta
    pretty = re.sub(r'"([^"]+)"\s*:', r'[cyan]"\1"[/]:', pretty)
    pretty = re.sub(r':\s*"([^"]*)"', r': [green]"\1"[/]', pretty)
    pretty = re.sub(r':\s*(\d+\.?\d*)', r': [yellow]\1[/]', pretty)
    pretty = re.sub(r':\s*(true|false|null)', r': [magenta]\1[/]', pretty)

    return pretty
