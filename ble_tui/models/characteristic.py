from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CharacteristicInfo:
    key: str
    uuid: str
    properties: tuple[str, ...]
    service_uuid: str
    char: Any
