import pytest
from unittest.mock import AsyncMock, Mock, patch

from ble_tui.services.ble_service import BleService


@pytest.mark.unit
async def test_scan_returns_sorted_devices():
    service = BleService()

    d1 = Mock()
    d1.name = "Weak"
    d1.address = "AA"
    a1 = Mock()
    a1.rssi = -70
    a1.local_name = "Weak"

    d2 = Mock()
    d2.name = "Strong"
    d2.address = "BB"
    a2 = Mock()
    a2.rssi = -30
    a2.local_name = "Strong"

    discovered = {"AA": (d1, a1), "BB": (d2, a2)}

    with patch("ble_tui.services.ble_service.BleakScanner.discover", new=AsyncMock(return_value=discovered)):
        result = await service.scan()

    assert [d.address for d in result] == ["BB", "AA"]


@pytest.mark.unit
async def test_connect_uses_bleak_client():
    service = BleService()
    mock_client = AsyncMock()
    mock_client.connect = AsyncMock()

    with patch("ble_tui.services.ble_service.BleakClient", return_value=mock_client):
        client = await service.connect("AA")

    assert client is mock_client
    mock_client.connect.assert_called_once()
