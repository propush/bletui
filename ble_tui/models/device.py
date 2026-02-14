from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    name: str
    address: str
    rssi: int
