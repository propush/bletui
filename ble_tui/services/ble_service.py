from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from bleak import BleakClient, BleakScanner

from ble_tui.models import CharacteristicInfo, DeviceInfo
from ble_tui.utils import CONNECT_TIMEOUT_S, SCAN_TIMEOUT_S


class BleService:
    async def scan(self) -> list[DeviceInfo]:
        found = await BleakScanner.discover(timeout=SCAN_TIMEOUT_S, return_adv=True)
        devices: list[DeviceInfo] = []
        for d, adv in found.values():
            rssi = adv.rssi if adv.rssi is not None else -999
            name = d.name or adv.local_name or ""
            devices.append(DeviceInfo(name=name, address=d.address, rssi=rssi))
        devices.sort(key=lambda x: x.rssi, reverse=True)
        return devices

    async def connect(
        self,
        address: str,
        disconnected_callback: Optional[Callable[[BleakClient], None]] = None,
    ) -> BleakClient:
        client = BleakClient(address, disconnected_callback=disconnected_callback)
        await client.connect(timeout=CONNECT_TIMEOUT_S)
        return client

    async def disconnect(self, client: Optional[BleakClient]) -> None:
        if client and client.is_connected:
            await client.disconnect()

    async def discover_gatt(
        self, client: BleakClient
    ) -> tuple[Dict[str, list[CharacteristicInfo]], Dict[int, str], int, int]:
        services = client.services
        mapped: Dict[str, list[CharacteristicInfo]] = {}
        key_by_handle: Dict[int, str] = {}

        service_count = 0
        char_count = 0
        for svc in services:
            service_count += 1
            chars: list[CharacteristicInfo] = []
            for char in svc.characteristics:
                char_count += 1
                props = tuple(sorted(char.properties))
                handle = getattr(char, "handle", None)
                if handle is not None:
                    key = f"{svc.uuid}:{char.uuid}:{handle}"
                    key_by_handle[handle] = key
                else:
                    key = f"{svc.uuid}:{char.uuid}"
                chars.append(
                    CharacteristicInfo(
                        key=key,
                        uuid=char.uuid,
                        properties=props,
                        service_uuid=svc.uuid,
                        char=char,
                    )
                )
            mapped[svc.uuid] = chars

        return mapped, key_by_handle, service_count, char_count

    async def read_char(self, client: BleakClient, target: str | int) -> bytes:
        return await client.read_gatt_char(target)

    async def start_notify(
        self,
        client: BleakClient,
        target: str | int,
        callback: Callable[[Any, bytearray], None],
    ) -> None:
        await client.start_notify(target, callback)

    async def stop_notify(self, client: BleakClient, target: str | int) -> None:
        await client.stop_notify(target)
