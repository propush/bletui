"""
Predefined test device profiles and expected data.

Provides factory functions for creating common test BLE devices
with realistic service and characteristic configurations.
"""
from tests.fixtures.ble_fixtures import MockBLEDeviceBuilder


# Common BLE GATT UUIDs
GENERIC_ACCESS_SERVICE = "00001800-0000-1000-8000-00805f9b34fb"
DEVICE_NAME_CHAR = "00002a00-0000-1000-8000-00805f9b34fb"
APPEARANCE_CHAR = "00002a01-0000-1000-8000-00805f9b34fb"

GENERIC_ATTRIBUTE_SERVICE = "00001801-0000-1000-8000-00805f9b34fb"
SERVICE_CHANGED_CHAR = "00002a05-0000-1000-8000-00805f9b34fb"

BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_CHAR = "00002a19-0000-1000-8000-00805f9b34fb"

DEVICE_INFO_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"
MANUFACTURER_NAME_CHAR = "00002a29-0000-1000-8000-00805f9b34fb"
MODEL_NUMBER_CHAR = "00002a24-0000-1000-8000-00805f9b34fb"
SERIAL_NUMBER_CHAR = "00002a25-0000-1000-8000-00805f9b34fb"


def create_test_device(
    name: str = "Test Device",
    address: str = "AA:BB:CC:DD:EE:FF",
    rssi: int = -45,
) -> MockBLEDeviceBuilder:
    """Create a generic test BLE device with common services.

    Args:
        name: Device name
        address: BLE MAC address
        rssi: Signal strength

    Returns:
        Configured MockBLEDeviceBuilder
    """
    builder = MockBLEDeviceBuilder(name, address, rssi)

    # Generic Access Service
    builder.add_service(GENERIC_ACCESS_SERVICE)
    builder.add_char(DEVICE_NAME_CHAR, ["read"], handle=10)
    builder.add_char(APPEARANCE_CHAR, ["read"], handle=11)

    # Generic Attribute Service
    builder.add_service(GENERIC_ATTRIBUTE_SERVICE)
    builder.add_char(SERVICE_CHANGED_CHAR, ["indicate"], handle=20)

    # Battery Service
    builder.add_service(BATTERY_SERVICE)
    builder.add_char(BATTERY_LEVEL_CHAR, ["read", "notify"], handle=30)

    return builder


def create_longbuddy_emu(
    address: str = "A4486977-7944-04D0-ACB9-25ABF3578B51",
    rssi: int = -45,
) -> MockBLEDeviceBuilder:
    """Create a mock LongBuddy-EMU device profile.

    This creates a device profile that matches the expected structure
    of the LongBuddy-EMU device for E2E testing.

    Args:
        address: BLE MAC address (default is typical macOS format)
        rssi: Signal strength

    Returns:
        Configured MockBLEDeviceBuilder
    """
    builder = MockBLEDeviceBuilder("LongBuddy-EMU", address, rssi)

    # Generic Access Service
    builder.add_service(GENERIC_ACCESS_SERVICE)
    builder.add_char(DEVICE_NAME_CHAR, ["read"], handle=3)
    builder.add_char(APPEARANCE_CHAR, ["read"], handle=5)

    # Generic Attribute Service
    builder.add_service(GENERIC_ATTRIBUTE_SERVICE)
    builder.add_char(SERVICE_CHANGED_CHAR, ["indicate"], handle=8)

    # Device Information Service
    builder.add_service(DEVICE_INFO_SERVICE)
    builder.add_char(MANUFACTURER_NAME_CHAR, ["read"], handle=11)
    builder.add_char(MODEL_NUMBER_CHAR, ["read"], handle=13)
    builder.add_char(SERIAL_NUMBER_CHAR, ["read"], handle=15)

    # Battery Service
    builder.add_service(BATTERY_SERVICE)
    builder.add_char(BATTERY_LEVEL_CHAR, ["read", "notify"], handle=18)

    # Custom services would be added here based on actual LongBuddy-EMU device
    # These would be discovered during E2E testing

    return builder


def create_minimal_device(
    name: str = "Minimal",
    address: str = "11:22:33:44:55:66",
) -> MockBLEDeviceBuilder:
    """Create a minimal BLE device with just Generic Access Service.

    Useful for testing basic connection and discovery flows.

    Args:
        name: Device name
        address: BLE MAC address

    Returns:
        Configured MockBLEDeviceBuilder
    """
    builder = MockBLEDeviceBuilder(name, address, rssi=-50)

    builder.add_service(GENERIC_ACCESS_SERVICE)
    builder.add_char(DEVICE_NAME_CHAR, ["read"], handle=1)

    return builder


def create_device_with_notifications(
    name: str = "Notify Device",
    address: str = "FF:EE:DD:CC:BB:AA",
) -> MockBLEDeviceBuilder:
    """Create a device with multiple notifiable characteristics.

    Useful for testing notification subscription flows.

    Args:
        name: Device name
        address: BLE MAC address

    Returns:
        Configured MockBLEDeviceBuilder
    """
    builder = MockBLEDeviceBuilder(name, address, rssi=-40)

    # Service with multiple notifiable characteristics
    builder.add_service("custom-service-uuid-1")
    builder.add_char("notify-char-1", ["notify"], handle=100)
    builder.add_char("notify-char-2", ["notify", "read"], handle=101)
    builder.add_char("indicate-char", ["indicate"], handle=102)

    # Battery service for good measure
    builder.add_service(BATTERY_SERVICE)
    builder.add_char(BATTERY_LEVEL_CHAR, ["read", "notify"], handle=110)

    return builder
