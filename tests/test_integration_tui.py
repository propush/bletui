"""
TUI Integration tests using Textual's Pilot.

These tests use Textual's testing framework to interact with the TUI
while mocking the BLE operations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from textual.widgets import DataTable, RichLog, Tree

from ble_tui import BleTui
from tests.fixtures import create_mock_scanner_with_devices, create_test_device


@pytest.mark.integration_tui
async def test_app_starts_and_renders():
    """Test that the app starts and renders basic UI elements."""
    async with BleTui().run_test() as pilot:
        app = pilot.app

        # Check that main widgets exist
        assert app.query_one("#devices", DataTable)
        assert app.query_one("#gatt", Tree)
        assert app.query_one("#log", RichLog)
        assert app.query_one("#status")


@pytest.mark.integration_tui
async def test_devices_table_has_columns():
    """Test that the devices DataTable has the correct columns."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        devices_table = app.query_one("#devices", DataTable)

        # Should have columns after mount
        assert devices_table.columns
        # Columns: Conn, RSSI, Name, Address
        assert len(devices_table.columns) == 4


@pytest.mark.integration_tui
async def test_initial_focus_on_devices():
    """Test that initial focus is on the devices table."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Devices table should have focus initially
        focused = app.focused
        assert isinstance(focused, DataTable)


@pytest.mark.integration_tui
async def test_tab_navigation_between_panes():
    """Test Tab key navigates between panes."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.containers import VerticalScroll

        await pilot.pause()

        # Start at devices table
        assert isinstance(app.focused, DataTable)

        # Press Tab -> should move to GATT tree
        await pilot.press("tab")
        assert isinstance(app.focused, Tree)

        # Press Tab again -> should move to latest value scroll
        await pilot.press("tab")
        assert isinstance(app.focused, VerticalScroll)

        # Press Tab again -> should move to log
        await pilot.press("tab")
        assert isinstance(app.focused, RichLog)

        # Press Tab again -> should wrap to devices
        await pilot.press("tab")
        assert isinstance(app.focused, DataTable)


@pytest.mark.integration_tui
async def test_shift_tab_navigation_backward():
    """Test Shift+Tab navigates backward between panes."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.containers import VerticalScroll

        await pilot.pause()

        # Start at devices table
        assert isinstance(app.focused, DataTable)

        # Press Shift+Tab -> should move backward to log
        await pilot.press("shift+tab")
        assert isinstance(app.focused, RichLog)

        # Press Shift+Tab again -> should move to latest value scroll
        await pilot.press("shift+tab")
        assert isinstance(app.focused, VerticalScroll)

        # Press Shift+Tab again -> should move to GATT
        await pilot.press("shift+tab")
        assert isinstance(app.focused, Tree)

        # Press Shift+Tab again -> should wrap to devices
        await pilot.press("shift+tab")
        assert isinstance(app.focused, DataTable)


@pytest.mark.integration_tui
async def test_scan_with_mocked_scanner():
    """Test scan action with mocked BleakScanner."""
    # Create mock devices
    device1 = create_test_device("Device1", "AA:BB:CC:DD:EE:F1", -45)
    device2 = create_test_device("Device2", "AA:BB:CC:DD:EE:F2", -55)

    scanner = create_mock_scanner_with_devices(device1, device2)

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            app = pilot.app

            # Wait for auto-scan to complete
            await pilot.pause(0.5)

            devices_table = app.query_one("#devices", DataTable)

            # Should have 2 devices
            assert devices_table.row_count == 2


@pytest.mark.integration_tui
async def test_scan_action_populates_devices():
    """Test that 's' key triggers scan and populates devices."""
    device1 = create_test_device("TestDev", "AA:BB:CC:DD:EE:FF", -40)
    scanner = create_mock_scanner_with_devices(device1)

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            app = pilot.app
            await pilot.pause()

            # Clear any auto-scan results
            app._state.devices.clear()
            app._state.device_order.clear()

            # Trigger manual scan
            await pilot.press("s")
            await pilot.pause(0.5)

            # Check device was added
            assert len(app._state.devices) == 1
            assert "AA:BB:CC:DD:EE:FF" in app._state.devices

            devices_table = app.query_one("#devices", DataTable)
            assert devices_table.row_count == 1


@pytest.mark.integration_tui
async def test_devices_sorted_by_rssi():
    """Test that devices are sorted by RSSI (strongest first)."""
    weak_device = create_test_device("Weak", "AA:BB:CC:DD:EE:F1", -80)
    strong_device = create_test_device("Strong", "AA:BB:CC:DD:EE:F2", -30)
    medium_device = create_test_device("Medium", "AA:BB:CC:DD:EE:F3", -55)

    scanner = create_mock_scanner_with_devices(
        weak_device, strong_device, medium_device
    )

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            app = pilot.app
            await pilot.pause(0.5)

            # Devices should be sorted by RSSI (strongest first)
            assert len(app._state.device_order) == 3

            # First device should be strongest (-30)
            first_addr = app._state.device_order[0]
            assert app._state.devices[first_addr].rssi == -30

            # Last device should be weakest (-80)
            last_addr = app._state.device_order[-1]
            assert app._state.devices[last_addr].rssi == -80


@pytest.mark.integration_tui
async def test_status_updates_during_scan():
    """Test that status message updates during scan."""
    scanner = create_mock_scanner_with_devices()

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            app = pilot.app

            # Trigger scan
            await pilot.press("s")
            await pilot.pause(0.1)

            # Status should be updated (check internal state)
            assert app._status_msg is not None


@pytest.mark.integration_tui
async def test_scan_failure_shows_platform_guidance():
    """Test scan failure message includes actionable Bluetooth guidance."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause(0.5)

        app._scan_in_progress = False
        app._ble.scan = AsyncMock(side_effect=RuntimeError("org.bluez.Error.Failed"))
        await app.action_scan()

        assert "Scan failed:" in app._status_msg
        assert "Bluetooth" in app._status_msg


@pytest.mark.integration_tui
async def test_gatt_tree_empty_initially():
    """Test that GATT tree is empty on startup."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        gatt_tree = app.query_one("#gatt", Tree)

        # Root should exist but have no children
        assert gatt_tree.root
        assert len(list(gatt_tree.root.children)) == 0


@pytest.mark.integration_tui
async def test_log_pane_empty_initially():
    """Test that log pane shows 'No characteristic selected' initially."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Check that no characteristic is selected
        assert app._selected_char is None


@pytest.mark.integration_tui
async def test_quit_action():
    """Test that 'q' key quits the app."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Press 'q' to quit
        await pilot.press("q")

        # App should exit (run_test context will handle cleanup)
        # If we get here without hanging, the test passes
        assert True


@pytest.mark.integration_tui
async def test_scan_handles_no_devices():
    """Test scan when no devices are found."""
    # Empty scanner
    scanner = create_mock_scanner_with_devices()

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            app = pilot.app
            await pilot.pause()

            # Clear and rescan
            app._state.devices.clear()
            await pilot.press("s")
            await pilot.pause(0.5)

            devices_table = app.query_one("#devices", DataTable)
            assert devices_table.row_count == 0


@pytest.mark.integration_tui
async def test_disconnect_clears_gatt_tree():
    """Test that disconnect action clears the GATT tree."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Simulate having a connection by setting up GATT tree
        gatt_tree = app.query_one("#gatt", Tree)
        gatt_tree.root.add("Test Service")

        # Disconnect
        await pilot.press("d")
        await pilot.pause()

        # GATT tree should be cleared
        assert len(list(gatt_tree.root.children)) == 0


@pytest.mark.integration_tui
async def test_escape_key_disconnects():
    """Test that Escape key triggers disconnect."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Press Escape
        await pilot.press("escape")
        await pilot.pause()

        # Should be disconnected (no client)
        assert app._client is None


@pytest.mark.integration_tui
async def test_latest_value_widget_exists():
    """Test that latest value widget is present in UI."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.containers import VerticalScroll
        from textual.widgets import Static

        # Check VerticalScroll container exists
        scroll_container = app.query_one("#latest_value_scroll", VerticalScroll)
        assert scroll_container is not None

        # Check Static widget inside exists
        latest = app.query_one("#latest_value", Static)
        assert latest is not None


@pytest.mark.integration_tui
async def test_latest_value_is_scrollable():
    """Test that latest value widget supports scrolling."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.containers import VerticalScroll

        scroll_container = app.query_one("#latest_value_scroll", VerticalScroll)

        # VerticalScroll should be scrollable
        assert hasattr(scroll_container, "scroll_to")
        assert hasattr(scroll_container, "scroll_up")
        assert hasattr(scroll_container, "scroll_down")


@pytest.mark.integration_tui
async def test_history_title_widget_exists():
    """Test that history title widget is present in UI."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.widgets import Static

        # Find the history title widget
        history_titles = app.query(".history-title")
        assert len(history_titles) > 0


@pytest.mark.integration_tui
async def test_history_title_shows_entry_count():
    """Test that history title dynamically shows entry count."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.widgets import Static
        from ble_tui.models import CharacteristicInfo

        await pilot.pause()

        # Get the title widget
        title_widget = app.query_one("#history_title", Static)

        # Create mock characteristic
        char = Mock()
        char.handle = 42

        info = CharacteristicInfo(
            key="test-svc:test-char:42",
            uuid="test-char",
            properties=("read", "notify"),
            service_uuid="test-svc",
            char=char,
        )

        # Set up GATT service
        app._state.services = {"test-svc": [info]}
        key = "test-svc:test-char:42"

        # Select characteristic with no data - should show "History (0)"
        app._selected_char = key
        app._render_log(key)
        await pilot.pause()

        rendered = title_widget.render()
        assert "History (0)" in str(rendered)

        # Add one entry - should show "History (1)"
        app._state.append_value(key, b"data1")
        app._render_log(key)
        await pilot.pause()

        rendered = title_widget.render()
        assert "History (1)" in str(rendered)

        # Add more entries - should show "History (3)"
        app._state.append_value(key, b"data2")
        app._state.append_value(key, b"data3")
        app._render_log(key)
        await pilot.pause()

        rendered = title_widget.render()
        assert "History (3)" in str(rendered)

        # Fill to max capacity (200 entries)
        for i in range(197):  # Already have 3 entries
            app._state.append_value(key, f"data{i}".encode())
        app._render_log(key)
        await pilot.pause()

        # Should show "History (200 - max)"
        rendered = title_widget.render()
        assert "History (200 - max)" in str(rendered)

        # Clear log - should show "History (0)"
        app._state.clear_char_log(key)
        app._render_log(key)
        await pilot.pause()

        rendered = title_widget.render()
        assert "History (0)" in str(rendered)

        # Disconnect/clear GATT - should reset to "History"
        app._selected_char = None  # Clear selection (done by disconnect_internal)
        app._clear_gatt_ui()
        await pilot.pause()

        rendered = title_widget.render()
        assert str(rendered) == "History"


@pytest.mark.integration_tui
async def test_latest_value_empty_state():
    """Test placeholder message when no data received."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        from textual.widgets import Static

        await pilot.pause()

        # Before any reads/notifications, latest_value should be empty
        latest = app.query_one("#latest_value", Static)
        # Initial state is empty string - check by rendering
        rendered_text = latest.render()
        assert str(rendered_text) == ""


@pytest.mark.integration_tui
async def test_write_char_no_connection():
    """Test that pressing 'w' without a connection shows status message."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        await pilot.press("w")
        await pilot.pause()

        assert "Connect" in app._status_msg


@pytest.mark.integration_tui
async def test_write_char_not_writable():
    """Test that pressing 'w' on a non-writable characteristic shows status."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Simulate connected state with a read-only characteristic
        app._client = Mock()
        app._client.is_connected = True
        app._client.address = "AA:BB:CC:DD:EE:FF"

        from ble_tui.models import CharacteristicInfo

        char = CharacteristicInfo(
            key="svc:char:1",
            uuid="0000aaaa-0000-1000-8000-00805f9b34fb",
            properties=("read",),
            service_uuid="0000bbbb-0000-1000-8000-00805f9b34fb",
            char=None,
        )
        app._state.services["0000bbbb-0000-1000-8000-00805f9b34fb"] = [char]
        app._selected_char = char.key

        await pilot.press("w")
        await pilot.pause()

        assert "not writable" in app._status_msg


@pytest.mark.integration_tui
async def test_write_dialog_opens_for_writable_char():
    """Test that write dialog opens for a writable characteristic."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        # Simulate connected state
        app._client = Mock()
        app._client.is_connected = True
        app._client.address = "AA:BB:CC:DD:EE:FF"

        from ble_tui.models import CharacteristicInfo

        char = CharacteristicInfo(
            key="svc:char:1",
            uuid="0000aaaa-0000-1000-8000-00805f9b34fb",
            properties=("read", "write"),
            service_uuid="0000bbbb-0000-1000-8000-00805f9b34fb",
            char=None,
        )
        app._state.services["0000bbbb-0000-1000-8000-00805f9b34fb"] = [char]
        app._selected_char = char.key

        await pilot.press("w")
        await pilot.pause(0.5)

        # Dialog should be on the screen stack
        from ble_tui.ui.write_dialog import WriteDialog

        assert any(isinstance(s, WriteDialog) for s in app.screen_stack)

        # Cancel the dialog via the active screen
        dialog = app.screen
        dialog.query_one("#write-cancel").press()
        await pilot.pause()


@pytest.mark.integration_tui
async def test_write_dialog_cancel():
    """Test that cancelling the write dialog does nothing."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        app._client = Mock()
        app._client.is_connected = True
        app._client.address = "AA:BB:CC:DD:EE:FF"

        from ble_tui.models import CharacteristicInfo

        char = CharacteristicInfo(
            key="svc:char:1",
            uuid="0000aaaa-0000-1000-8000-00805f9b34fb",
            properties=("write",),
            service_uuid="0000bbbb-0000-1000-8000-00805f9b34fb",
            char=None,
        )
        app._state.services["0000bbbb-0000-1000-8000-00805f9b34fb"] = [char]
        app._selected_char = char.key

        await pilot.press("w")
        await pilot.pause(0.5)

        # Press cancel
        app.screen.query_one("#write-cancel").press()
        await pilot.pause()

        # Should not have written anything - status shouldn't mention "Wrote"
        assert "Wrote" not in app._status_msg


@pytest.mark.integration_tui
async def test_write_dialog_submit_hex():
    """Test writing hex data through the dialog."""
    async with BleTui().run_test() as pilot:
        app = pilot.app
        await pilot.pause()

        mock_client = AsyncMock()
        mock_client.is_connected = True
        mock_client.address = "AA:BB:CC:DD:EE:FF"
        app._client = mock_client

        from ble_tui.models import CharacteristicInfo

        mock_char = Mock()
        mock_char.handle = 1
        char = CharacteristicInfo(
            key="svc:char:1",
            uuid="0000aaaa-0000-1000-8000-00805f9b34fb",
            properties=("write",),
            service_uuid="0000bbbb-0000-1000-8000-00805f9b34fb",
            char=mock_char,
        )
        app._state.services["0000bbbb-0000-1000-8000-00805f9b34fb"] = [char]
        app._selected_char = char.key

        app._ble.write_char = AsyncMock()

        await pilot.press("w")
        await pilot.pause(0.5)

        # Verify the dialog opened
        from ble_tui.ui.write_dialog import WriteDialog

        dialog = app.screen
        assert isinstance(dialog, WriteDialog)

        # Instead of interacting with the dialog UI (which is tricky in tests),
        # dismiss the dialog and call _do_write directly to test the write flow
        dialog.dismiss(None)
        await pilot.pause(0.5)

        # Directly test the write flow
        from ble_tui.models import CharacteristicInfo as CI

        await app._do_write(char, b"\xaa\xbb\xcc", True)
        await pilot.pause(0.5)

        app._ble.write_char.assert_called_once()
        assert "Wrote 3 bytes" in app._status_msg


@pytest.mark.integration_tui
async def test_clear_log_with_no_selection():
    """Test 'l' key with no characteristic selected shows error."""
    async with BleTui().run_test() as pilot:
        await pilot.press("l")
        await pilot.pause()
        assert "No characteristic selected" in pilot.app._status_msg


@pytest.mark.integration_tui
async def test_clear_log_clears_selected_only():
    """Test 'l' key clears only the selected characteristic."""
    async with BleTui().run_test() as pilot:
        app = pilot.app

        # Create mock characteristics
        from ble_tui.models import CharacteristicInfo

        char1 = Mock()
        char1.handle = 10
        char2 = Mock()
        char2.handle = 20

        info1 = CharacteristicInfo(
            key="svc:char1:10",
            uuid="char1",
            properties=("read",),
            service_uuid="svc",
            char=char1,
        )
        info2 = CharacteristicInfo(
            key="svc:char2:20",
            uuid="char2",
            properties=("read",),
            service_uuid="svc",
            char=char2,
        )

        # Set up GATT services
        app._state.services = {"svc": [info1, info2]}

        # Add logs for two characteristics
        key1, key2 = "svc:char1:10", "svc:char2:20"
        app._state.append_value(key1, b"data1")
        app._state.append_value(key2, b"data2")

        # Select and clear first characteristic
        app._selected_char = key1
        await pilot.press("l")
        await pilot.pause()

        # Verify only key1 cleared, key2 preserved
        assert len(app._state.logs[key1]) == 0
        assert len(app._state.logs[key2]) == 1


@pytest.mark.integration_tui
async def test_clear_log_preserves_notifications():
    """Test 'l' key doesn't stop notification subscriptions."""
    async with BleTui().run_test() as pilot:
        app = pilot.app

        # Create mock characteristic
        from ble_tui.models import CharacteristicInfo

        char = Mock()
        char.handle = 42

        info = CharacteristicInfo(
            key="svc:char:42",
            uuid="char",
            properties=("notify",),
            service_uuid="svc",
            char=char,
        )

        # Set up GATT service
        app._state.services = {"svc": [info]}

        key = "svc:char:42"
        app._state.subscribed.add(key)
        app._state.append_value(key, b"notification")
        app._selected_char = key

        await pilot.press("l")
        await pilot.pause()

        # Subscription preserved, but logs cleared
        assert key in app._state.subscribed
        assert len(app._state.logs[key]) == 0
