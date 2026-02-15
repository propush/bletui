import pytest
from unittest.mock import Mock

from ble_tui.models import CharacteristicInfo, DeviceInfo
from ble_tui.services.state_service import StateService


@pytest.mark.unit
def test_replace_devices_populates_maps_in_order():
    state = StateService()
    devices = [
        DeviceInfo(name="A", address="AA", rssi=-40),
        DeviceInfo(name="B", address="BB", rssi=-60),
    ]

    state.replace_devices(devices)

    assert state.device_order == ["AA", "BB"]
    assert state.devices["AA"].name == "A"


@pytest.mark.unit
def test_append_value_creates_log_entry_with_json():
    state = StateService()

    state.append_value("k", b'{"ok":true}')

    assert "k" in state.logs
    entry = state.logs["k"][0]
    assert entry.size == 11
    assert entry.json_str == '{"ok":true}'


@pytest.mark.unit
def test_find_char_and_target_helpers():
    state = StateService()
    char = Mock()
    char.handle = 101
    info = CharacteristicInfo(
        key="svc:char:101",
        uuid="char",
        properties=("read",),
        service_uuid="svc",
        char=char,
    )
    state.services = {"svc": [info]}

    assert state.find_char("svc:char:101") == info
    assert state.char_target(info) == 101


@pytest.mark.unit
def test_clear_char_log():
    """Test clearing logs and latest data for a specific characteristic."""
    state = StateService()
    key = "service:char:42"
    state.append_value(key, b"test data 1")
    state.append_value(key, b"test data 2")

    assert len(state.logs[key]) == 2
    assert key in state.latest_data

    state.clear_char_log(key)

    assert len(state.logs[key]) == 0
    assert key not in state.latest_data


@pytest.mark.unit
def test_clear_char_log_nonexistent_key():
    """Test clearing a characteristic that doesn't exist (should not error)."""
    state = StateService()
    state.clear_char_log("nonexistent:key:999")  # Should not raise
