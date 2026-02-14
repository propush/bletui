import pytest

from ble_tui.utils.platform_support import (
    current_platform_name,
    format_ble_error,
    platform_ble_hint,
)


@pytest.mark.unit
def test_current_platform_name_windows():
    assert current_platform_name("win32") == "windows"


@pytest.mark.unit
def test_current_platform_name_linux():
    assert current_platform_name("linux") == "linux"


@pytest.mark.unit
def test_platform_ble_hint_windows_adapter_unavailable():
    exc = RuntimeError("BleakBluetoothNotAvailableError: NO_BLUETOOTH")
    hint = platform_ble_hint(exc, platform="win32")
    assert "Bluetooth is enabled" in hint
    assert "adapter" in hint.lower()


@pytest.mark.unit
def test_platform_ble_hint_linux_bluez_stack_issue():
    exc = RuntimeError("org.bluez.Error.Failed: dbus unavailable")
    hint = platform_ble_hint(exc, platform="linux")
    assert "BlueZ" in hint
    assert "dbus" in hint


@pytest.mark.unit
def test_format_ble_error_includes_action_and_log_path():
    msg = format_ble_error("Scan", RuntimeError("x"), "ble_tui_errors.log")
    assert msg.startswith("Scan failed:")
    assert "ble_tui_errors.log" in msg

