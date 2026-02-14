from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LogEntry:
    ts: str
    size: int
    hex_str: str
    json_str: Optional[str]
