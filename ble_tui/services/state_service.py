from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, Optional

from ble_tui.models import CharacteristicInfo, DeviceInfo, LogEntry
from ble_tui.utils import LOG_MAX, hex_groups, try_parse_json


class StateService:
    def __init__(self) -> None:
        self.devices: Dict[str, DeviceInfo] = {}
        self.device_order: list[str] = []
        self.services: Dict[str, list[CharacteristicInfo]] = {}
        self.key_by_handle: Dict[int, str] = {}
        self.logs: Dict[str, Deque[LogEntry]] = {}
        self.subscribed: set[str] = set()
        self.latest_data: Dict[str, bytes] = {}

    def replace_devices(self, devices: list[DeviceInfo]) -> None:
        self.devices.clear()
        self.device_order.clear()
        for dev in devices:
            self.devices[dev.address] = dev
            self.device_order.append(dev.address)

    def clear_connection_state(self) -> None:
        self.services.clear()
        self.key_by_handle.clear()
        self.subscribed.clear()
        self.latest_data.clear()
        self.logs.clear()

    def set_gatt(
        self,
        services: Dict[str, list[CharacteristicInfo]],
        key_by_handle: Dict[int, str],
    ) -> None:
        self.services = services
        self.key_by_handle = key_by_handle

    def find_char(self, key: str) -> Optional[CharacteristicInfo]:
        for chars in self.services.values():
            for info in chars:
                if info.key == key:
                    return info
        return None

    def append_value(self, key: str, data: bytes) -> LogEntry:
        entry = LogEntry(
            ts=datetime.now().strftime("%H:%M:%S.%f")[:-3],
            size=len(data),
            hex_str=hex_groups(data),
            json_str=try_parse_json(data),
        )
        log = self.logs.setdefault(key, deque(maxlen=LOG_MAX))
        log.append(entry)
        self.latest_data[key] = data  # Store original bytes
        return entry

    @staticmethod
    def char_target(info: CharacteristicInfo) -> str | int:
        handle = getattr(info.char, "handle", None)
        return handle if handle is not None else info.uuid

    @staticmethod
    def connected_address(client: Any) -> Optional[str]:
        if client and getattr(client, "is_connected", False):
            return str(client.address)
        return None
