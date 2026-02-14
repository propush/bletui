#!/usr/bin/env python3
"""Backward-compatible app entry point.

Primary implementation now lives in `ble_tui` package.
"""

from ble_tui import BleTui
from ble_tui.models import CharacteristicInfo, DeviceInfo, LogEntry
from ble_tui.utils.formatting import hex_groups as _hex_groups
from ble_tui.utils.formatting import try_parse_json as _try_parse_json

__all__ = [
    "BleTui",
    "DeviceInfo",
    "CharacteristicInfo",
    "LogEntry",
    "_hex_groups",
    "_try_parse_json",
]


if __name__ == "__main__":
    BleTui().run()
