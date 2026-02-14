from __future__ import annotations

import sys


def current_platform_name(platform: str | None = None) -> str:
    value = (platform or sys.platform).lower()
    if value.startswith("win"):
        return "windows"
    if value.startswith("linux"):
        return "linux"
    if value.startswith("darwin"):
        return "macos"
    return "unknown"


def platform_ble_hint(exc: Exception, platform: str | None = None) -> str:
    plat = current_platform_name(platform)
    text = f"{exc!r} {exc}".lower()

    unavailable_tokens = (
        "bluetooth is unsupported",
        "bleakbluetoothnotavailableerror",
        "no_bluetooth",
        "bluetooth is off",
    )
    linux_stack_tokens = (
        "org.bluez",
        "bluez",
        "dbus",
        "permission denied",
        "operation not permitted",
    )

    if any(token in text for token in unavailable_tokens):
        if plat == "windows":
            return "Check that Bluetooth is enabled and a BLE adapter is available."
        if plat == "linux":
            return "Check Bluetooth adapter, ensure bluetoothd is running, and verify BlueZ permissions."
        if plat == "macos":
            return "Check Bluetooth is enabled and grant terminal Bluetooth permission in System Settings."
        return "Check Bluetooth is enabled and an adapter is available."

    if plat == "linux" and any(token in text for token in linux_stack_tokens):
        return "Ensure BlueZ/dbus are installed and running, then retry with sufficient permissions."

    if plat == "windows" and "access is denied" in text:
        return "Run with an account that has Bluetooth access and confirm adapter permissions."

    return "Check Bluetooth availability and platform BLE prerequisites."


def format_ble_error(action: str, exc: Exception, error_log_path: str) -> str:
    hint = platform_ble_hint(exc)
    return f"{action} failed: {hint} (details in {error_log_path})"

