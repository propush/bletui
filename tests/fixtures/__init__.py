"""
Test fixtures for BLE TUI App.

Provides mock BLE devices, services, and characteristics for testing.
"""
from tests.fixtures.ble_fixtures import (
    MockBLEDeviceBuilder,
    MockServiceBuilder,
    MockCharacteristicBuilder,
    create_mock_scanner_with_devices,
)
from tests.fixtures.device_fixtures import (
    create_test_device,
    create_longbuddy_emu,
    create_minimal_device,
    create_device_with_notifications,
)

__all__ = [
    "MockBLEDeviceBuilder",
    "MockServiceBuilder",
    "MockCharacteristicBuilder",
    "create_mock_scanner_with_devices",
    "create_test_device",
    "create_longbuddy_emu",
    "create_minimal_device",
    "create_device_with_notifications",
]
