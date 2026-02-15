"""
BLE Integration tests with mocked BleakClient.

These tests verify BLE operations (connect, disconnect, discover, read, notify)
using mocked BLE client instances without requiring full TUI initialization.
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
import threading
from ble_tui.models import CharacteristicInfo


@pytest.mark.integration_ble
async def test_connect_to_device(mock_client_factory):
    """Test connecting to a BLE device."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Add a device
        app._state.devices["AA:BB:CC:DD:EE:FF"] = Mock(
            name="Test", address="AA:BB:CC:DD:EE:FF", rssi=-45
        )
        app._state.device_order.append("AA:BB:CC:DD:EE:FF")
        app._selected_device = "AA:BB:CC:DD:EE:FF"

        # Mock BleakClient
        mock_client = mock_client_factory("AA:BB:CC:DD:EE:FF")

        with patch("ble_tui.services.ble_service.BleakClient", return_value=mock_client):
            await app.action_connect()

        # Client should be set
        assert app._client is not None
        mock_client.connect.assert_called_once()


@pytest.mark.integration_ble
async def test_disconnect_clears_state():
    """Test that disconnect clears all BLE state."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Simulate connected state
        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.disconnect = AsyncMock()

        app._client = mock_client
        app._state.services = {"svc1": []}
        app._state.key_by_handle = {100: "key1"}
        app._state.subscribed = {"key1"}
        app._state.logs = {"key1": [{"ts": "12:00:00.000", "data": b"test"}]}
        app._selected_char = "key1"

        # Disconnect
        await app._disconnect_internal()

        # All state should be cleared
        assert app._client is None
        assert len(app._state.services) == 0
        assert len(app._state.key_by_handle) == 0
        assert len(app._state.subscribed) == 0
        assert len(app._state.logs) == 0
        assert app._selected_char is None

        # Client disconnect should have been called
        mock_client.disconnect.assert_called_once()


@pytest.mark.integration_ble
async def test_disconnect_handles_no_client():
    """Test disconnect when no client exists."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # No client set
        app._client = None

        # Disconnect should not raise error
        await app._disconnect_internal()

        # Should still be None
        assert app._client is None


@pytest.mark.integration_ble
async def test_discover_gatt_services():
    """Test GATT service and characteristic discovery."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Create mock service with characteristic
        char = Mock()
        char.uuid = "00002a00-0000-1000-8000-00805f9b34fb"
        char.properties = ["read", "write"]
        char.handle = 100

        svc = Mock()
        svc.uuid = "00001800-0000-1000-8000-00805f9b34fb"
        svc.characteristics = [char]

        # Setup client with string address to avoid markup issues
        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.is_connected = True
        mock_client.services = [svc]
        app._client = mock_client

        # Discover GATT
        await app._discover_gatt()

        # Services should be stored
        assert len(app._state.services) > 0
        assert len(app._state.key_by_handle) > 0


@pytest.mark.integration_ble
async def test_read_characteristic():
    """Test reading a characteristic."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Readable characteristic
        char = Mock()
        char.uuid = "char-uuid"
        char.properties = ["read"]
        char.handle = 100

        char_info = CharacteristicInfo(
            key="svc:char:100",
            uuid="char-uuid",
            properties=("read",),
            service_uuid="svc-uuid",
            char=char,
        )

        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.is_connected = True
        mock_client.read_gatt_char = AsyncMock(return_value=b"Hello BLE")

        app._client = mock_client
        app._state.services = {"svc-uuid": [char_info]}
        app._selected_char = "svc:char:100"

        # Read characteristic
        await app.action_read_char()

        # Read should have been called
        mock_client.read_gatt_char.assert_called_once()

        # Value should be logged
        assert "svc:char:100" in app._state.logs
        assert len(app._state.logs["svc:char:100"]) == 1


@pytest.mark.integration_ble
async def test_read_non_readable_characteristic_fails():
    """Test that reading a non-readable characteristic fails gracefully."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Non-readable characteristic
        char = Mock()
        char.uuid = "char-uuid"
        char.properties = ["notify"]  # No read!
        char.handle = 100

        char_info = CharacteristicInfo(
            key="svc:char:100",
            uuid="char-uuid",
            properties=("notify",),
            service_uuid="svc-uuid",
            char=char,
        )

        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.is_connected = True

        app._client = mock_client
        app._state.services = {"svc-uuid": [char_info]}
        app._selected_char = "svc:char:100"

        # Try to read
        await app.action_read_char()

        # Read should NOT have been called
        mock_client.read_gatt_char.assert_not_called()


@pytest.mark.integration_ble
async def test_start_notify():
    """Test starting notifications on a characteristic."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Notifiable characteristic
        char = Mock()
        char.uuid = "char-uuid"
        char.properties = ["notify"]
        char.handle = 100

        char_info = CharacteristicInfo(
            key="svc:char:100",
            uuid="char-uuid",
            properties=("notify",),
            service_uuid="svc-uuid",
            char=char,
        )

        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.is_connected = True

        app._client = mock_client
        app._state.services = {"svc-uuid": [char_info]}
        app._selected_char = "svc:char:100"

        # Start notify
        await app.action_toggle_notify()

        # start_notify should have been called
        mock_client.start_notify.assert_called_once()

        # Should be in subscribed set
        assert "svc:char:100" in app._state.subscribed


@pytest.mark.integration_ble
async def test_stop_notify():
    """Test stopping notifications on a characteristic."""
    from ble_tui import BleTui

    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Setup: Already subscribed characteristic
        char = Mock()
        char.uuid = "char-uuid"
        char.properties = ["notify"]
        char.handle = 100

        char_info = CharacteristicInfo(
            key="svc:char:100",
            uuid="char-uuid",
            properties=("notify",),
            service_uuid="svc-uuid",
            char=char,
        )

        mock_client = AsyncMock()
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        mock_client.is_connected = True

        app._client = mock_client
        app._state.services = {"svc-uuid": [char_info]}
        app._selected_char = "svc:char:100"
        app._state.subscribed.add("svc:char:100")

        # Stop notify
        await app.action_toggle_notify()

        # stop_notify should have been called
        mock_client.stop_notify.assert_called_once()

        # Should be removed from subscribed set
        assert "svc:char:100" not in app._state.subscribed


@pytest.mark.integration_ble
async def test_append_value_creates_log_entry():
    """Test that appending a value creates a proper log entry."""
    from ble_tui import BleTui

    app = BleTui()

    # Append a value
    test_data = b'{"test": 123}'
    app._append_value("test-key", test_data)

    # Log should exist
    assert "test-key" in app._state.logs
    assert len(app._state.logs["test-key"]) == 1

    entry = app._state.logs["test-key"][0]
    assert entry.size == len(test_data)
    assert entry.hex_str  # Should have hex representation
    assert entry.json_str  # Should parse as JSON


@pytest.mark.integration_ble
async def test_log_entry_max_limit():
    """Test that log entries respect max limit (200)."""
    from ble_tui import BleTui

    app = BleTui()

    # Add 250 entries
    for i in range(250):
        app._append_value("test-key", f"data-{i}".encode())

    # Should only keep last 200 (LOG_MAX)
    assert len(app._state.logs["test-key"]) == 200


@pytest.mark.integration_ble
async def test_find_char_by_key():
    """Test finding a characteristic by its key."""
    from ble_tui import BleTui

    app = BleTui()

    # Setup: Add a characteristic
    char_info = CharacteristicInfo(
        key="svc:char:100",
        uuid="char-uuid",
        properties=("read",),
        service_uuid="svc-uuid",
        char=Mock(),
    )

    app._state.services = {"svc-uuid": [char_info]}

    # Find by key
    found = app._find_char("svc:char:100")

    assert found is not None
    assert found.key == "svc:char:100"
    assert found.uuid == "char-uuid"


@pytest.mark.integration_ble
async def test_find_char_returns_none_if_not_found():
    """Test that finding a non-existent characteristic returns None."""
    from ble_tui import BleTui

    app = BleTui()
    app._state.services = {}

    found = app._find_char("non-existent-key")

    assert found is None


@pytest.mark.integration_ble
async def test_char_target_uses_handle_if_available():
    """Test that _char_target returns handle when available."""
    from ble_tui import BleTui

    app = BleTui()

    char = Mock()
    char.handle = 100
    char.uuid = "char-uuid"

    char_info = CharacteristicInfo(
        key="test",
        uuid="char-uuid",
        properties=("read",),
        service_uuid="svc",
        char=char,
    )

    target = app._char_target(char_info)

    # Should return handle, not UUID
    assert target == 100


@pytest.mark.integration_ble
async def test_char_target_uses_uuid_if_no_handle():
    """Test that _char_target returns UUID when handle not available."""
    from ble_tui import BleTui

    app = BleTui()

    char = Mock(spec=[])  # No handle attribute
    char.uuid = "char-uuid"

    char_info = CharacteristicInfo(
        key="test",
        uuid="char-uuid",
        properties=("read",),
        service_uuid="svc",
        char=char,
    )

    target = app._char_target(char_info)

    # Should return UUID
    assert target == "char-uuid"


@pytest.mark.integration_ble
async def test_dispatch_notify_does_not_touch_ui_when_thread_dispatch_fails():
    """Notification callback fallback must not update UI off the main thread."""
    from ble_tui import BleTui

    app = BleTui()
    app._thread_id = threading.get_ident() + 1

    with patch.object(app, "call_from_thread", side_effect=RuntimeError("closed loop")):
        with patch.object(app, "_append_value") as append_mock:
            with patch.object(app, "_set_status") as status_mock:
                with patch.object(app, "_record_error") as error_mock:
                    app._dispatch_notify("svc:char:1", b"\x01\x02", "char-uuid")

    append_mock.assert_not_called()
    status_mock.assert_not_called()
    error_mock.assert_called_once()


@pytest.mark.integration_ble
async def test_dispatch_notify_falls_back_to_direct_calls_on_app_thread():
    """If callback runs on app thread, fallback should apply updates directly."""
    from ble_tui import BleTui

    app = BleTui()
    app._thread_id = threading.get_ident()

    with patch.object(
        app,
        "call_from_thread",
        side_effect=RuntimeError(
            "The `call_from_thread` method must run in a different thread from the app"
        ),
    ):
        with patch.object(app, "_append_value") as append_mock:
            with patch.object(app, "_set_status") as status_mock:
                with patch.object(app, "_record_error") as error_mock:
                    app._dispatch_notify("svc:char:1", b"\x01\x02", "char-uuid")

    append_mock.assert_called_once_with("svc:char:1", b"\x01\x02")
    status_mock.assert_called_once_with("Notify char-uuid (2 B)")
    error_mock.assert_not_called()
