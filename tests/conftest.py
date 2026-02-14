"""
Pytest fixtures and configuration.

Provides shared fixtures for BLE TUI tests including mock BLE devices,
clients, and configured app instances.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import Any, Callable
from tests.config import test_config


@pytest.fixture
def config():
    """Test configuration from environment variables."""
    return test_config


@pytest.fixture
def mock_ble_device():
    """Create a mock BLE device (BLEDevice from bleak)."""
    device = Mock()
    device.name = "Test Device"
    device.address = "AA:BB:CC:DD:EE:FF"
    return device


@pytest.fixture
def mock_advertisement_data():
    """Create mock advertisement data."""
    adv = Mock()
    adv.rssi = -45
    adv.local_name = "Test Device"
    return adv


@pytest.fixture
def mock_characteristic():
    """Create a mock BLE characteristic."""
    char = Mock()
    char.uuid = "00002a00-0000-1000-8000-00805f9b34fb"
    char.properties = ["read", "write"]
    char.handle = 100
    return char


@pytest.fixture
def mock_service(mock_characteristic):
    """Create a mock BLE GATT service with one characteristic."""
    svc = Mock()
    svc.uuid = "00001800-0000-1000-8000-00805f9b34fb"
    svc.characteristics = [mock_characteristic]
    return svc


@pytest.fixture
def mock_scanner():
    """Create a mock BleakScanner with async discover method."""
    scanner = MagicMock()

    async def discover_mock(timeout: float = 10.0, return_adv: bool = False):
        """Mock discover that returns empty dict by default."""
        return {}

    scanner.discover = AsyncMock(side_effect=discover_mock)
    return scanner


@pytest.fixture
def mock_client():
    """Create a mock BleakClient with common async methods."""
    client = AsyncMock()
    client.address = "AA:BB:CC:DD:EE:FF"
    client.is_connected = True
    client.services = []

    # Mock async methods
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.read_gatt_char = AsyncMock(return_value=b"test data")
    client.start_notify = AsyncMock()
    client.stop_notify = AsyncMock()

    return client


@pytest.fixture
def mock_client_factory(mock_service):
    """Factory to create configured mock BleakClient instances."""
    def _create_client(
        address: str = "AA:BB:CC:DD:EE:FF",
        is_connected: bool = True,
        services: list = None,
    ):
        client = AsyncMock()
        client.address = address
        client.is_connected = is_connected
        client.services = services if services is not None else [mock_service]

        client.connect = AsyncMock()
        client.disconnect = AsyncMock()
        client.read_gatt_char = AsyncMock(return_value=b"test data")
        client.start_notify = AsyncMock()
        client.stop_notify = AsyncMock()

        return client

    return _create_client


@pytest.fixture
async def ble_app():
    """Create a BleTui instance for testing.

    Note: This creates the app but does NOT call on_mount() automatically.
    Tests that need a fully initialized app should call app.on_mount() or
    use textual's Pilot for full TUI testing.
    """
    from ble_tui import BleTui
    app = BleTui()
    yield app
    # Cleanup
    if app._client and app._client.is_connected:
        try:
            await app._disconnect_internal()
        except Exception:
            pass
