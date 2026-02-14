"""
Mock BLE device and service builders for testing.

Provides builder patterns for constructing mock BLE devices, services,
and characteristics with configurable properties.
"""
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock


class MockCharacteristicBuilder:
    """Builder for mock BLE characteristics."""

    def __init__(self, uuid: str, properties: list[str], handle: Optional[int] = None):
        self.uuid = uuid
        self.properties = properties
        self.handle = handle
        self._value = b"mock value"

    def with_value(self, value: bytes) -> "MockCharacteristicBuilder":
        """Set the characteristic value."""
        self._value = value
        return self

    def build(self) -> Mock:
        """Build and return the mock characteristic."""
        char = Mock()
        char.uuid = self.uuid
        char.properties = self.properties
        if self.handle is not None:
            char.handle = self.handle
        return char


class MockServiceBuilder:
    """Builder for mock BLE GATT services."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        self._characteristics: list[Mock] = []

    def add_char(
        self,
        uuid: str,
        properties: list[str],
        handle: Optional[int] = None,
    ) -> "MockServiceBuilder":
        """Add a characteristic to this service."""
        char = MockCharacteristicBuilder(uuid, properties, handle).build()
        self._characteristics.append(char)
        return self

    def add_characteristic(self, char: Mock) -> "MockServiceBuilder":
        """Add a pre-built characteristic to this service."""
        self._characteristics.append(char)
        return self

    def build(self) -> Mock:
        """Build and return the mock service."""
        svc = Mock()
        svc.uuid = self.uuid
        svc.characteristics = self._characteristics
        return svc


class MockBLEDeviceBuilder:
    """Builder for mock BLE devices with services and characteristics.

    Usage:
        builder = MockBLEDeviceBuilder("LongBuddy-EMU", "AA:BB:CC:DD:EE:FF", -45)
        builder.add_service("00001800-0000-1000-8000-00805f9b34fb") \\
               .add_char("00002a00-0000-1000-8000-00805f9b34fb", ["read"], handle=100)
        device, adv_data = builder.build_device_and_adv()
        client = builder.build_client()
    """

    def __init__(self, name: str, address: str, rssi: int = -50):
        self.name = name
        self.address = address
        self.rssi = rssi
        self._services: list[Mock] = []
        self._current_service: Optional[MockServiceBuilder] = None

    def add_service(self, uuid: str) -> "MockBLEDeviceBuilder":
        """Add a new service to this device."""
        if self._current_service is not None:
            # Finalize previous service
            self._services.append(self._current_service.build())
        self._current_service = MockServiceBuilder(uuid)
        return self

    def add_char(
        self,
        uuid: str,
        properties: list[str],
        handle: Optional[int] = None,
    ) -> "MockBLEDeviceBuilder":
        """Add a characteristic to the current service."""
        if self._current_service is None:
            raise ValueError("Must call add_service() before add_char()")
        self._current_service.add_char(uuid, properties, handle)
        return self

    def _finalize(self) -> None:
        """Finalize the current service if any."""
        if self._current_service is not None:
            self._services.append(self._current_service.build())
            self._current_service = None

    def build_device_and_adv(self) -> tuple[Mock, Mock]:
        """Build and return a (BLEDevice, AdvertisementData) tuple."""
        self._finalize()

        device = Mock()
        device.name = self.name
        device.address = self.address

        adv = Mock()
        adv.rssi = self.rssi
        adv.local_name = self.name

        return device, adv

    def build_client(self) -> AsyncMock:
        """Build and return a mock BleakClient for this device."""
        self._finalize()

        client = AsyncMock()
        client.address = self.address
        client.is_connected = True
        client.services = self._services

        # Setup async methods
        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"test data")
        client.start_notify = AsyncMock()
        client.stop_notify = AsyncMock()

        return client

    def build_scanner_result(self) -> dict[str, tuple[Mock, Mock]]:
        """Build a scanner discover result dict."""
        device, adv = self.build_device_and_adv()
        return {self.address: (device, adv)}


def create_mock_scanner_with_devices(*builders: MockBLEDeviceBuilder) -> AsyncMock:
    """Create a mock BleakScanner that returns the specified devices.

    Args:
        *builders: MockBLEDeviceBuilder instances to include in scan results

    Returns:
        AsyncMock BleakScanner with discover() method configured
    """
    scanner = AsyncMock()

    # Combine all device results
    result_dict = {}
    for builder in builders:
        result_dict.update(builder.build_scanner_result())

    async def discover_mock(timeout: float = 10.0, return_adv: bool = False):
        return result_dict

    scanner.discover = AsyncMock(side_effect=discover_mock)
    return scanner
