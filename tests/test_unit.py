"""
Unit tests for BLE TUI App pure functions and data structures.

These tests are fast, have no external dependencies, and can run in CI.
"""
import json
import pytest
from ble_tui.models import DeviceInfo, CharacteristicInfo, LogEntry
from ble_tui.utils.formatting import hex_groups as _hex_groups
from ble_tui.utils.formatting import try_parse_json as _try_parse_json


# =============================================================================
# Tests for _hex_groups()
# =============================================================================

@pytest.mark.unit
def test_hex_groups_empty():
    """Test _hex_groups with empty bytes."""
    assert _hex_groups(b"") == ""


@pytest.mark.unit
def test_hex_groups_single_byte():
    """Test _hex_groups with a single byte."""
    assert _hex_groups(b"\x00") == "00"
    assert _hex_groups(b"\xff") == "ff"
    assert _hex_groups(b"\x42") == "42"


@pytest.mark.unit
def test_hex_groups_multiple_bytes():
    """Test _hex_groups with multiple bytes."""
    assert _hex_groups(b"\x01\x02\x03") == "01 02 03"
    assert _hex_groups(b"\xaa\xbb\xcc\xdd") == "aa bb cc dd"


@pytest.mark.unit
def test_hex_groups_ascii_text():
    """Test _hex_groups with ASCII text."""
    assert _hex_groups(b"Hello") == "48 65 6c 6c 6f"


@pytest.mark.unit
def test_hex_groups_with_zeros():
    """Test _hex_groups with zero bytes."""
    assert _hex_groups(b"\x00\x00\x00") == "00 00 00"


# =============================================================================
# Tests for _try_parse_json()
# =============================================================================

@pytest.mark.unit
def test_try_parse_json_valid_object():
    """Test _try_parse_json with valid JSON object."""
    data = b'{"key": "value", "number": 42}'
    result = _try_parse_json(data)
    assert result is not None
    # Result should be compact JSON
    parsed = json.loads(result)
    assert parsed["key"] == "value"
    assert parsed["number"] == 42


@pytest.mark.unit
def test_try_parse_json_valid_array():
    """Test _try_parse_json with valid JSON array."""
    data = b'[1, 2, 3, "test"]'
    result = _try_parse_json(data)
    assert result is not None
    parsed = json.loads(result)
    assert parsed == [1, 2, 3, "test"]


@pytest.mark.unit
def test_try_parse_json_valid_string():
    """Test _try_parse_json with valid JSON string."""
    data = b'"hello world"'
    result = _try_parse_json(data)
    assert result is not None
    assert json.loads(result) == "hello world"


@pytest.mark.unit
def test_try_parse_json_valid_number():
    """Test _try_parse_json with valid JSON number."""
    data = b'42'
    result = _try_parse_json(data)
    assert result is not None
    assert json.loads(result) == 42


@pytest.mark.unit
def test_try_parse_json_invalid_utf8():
    """Test _try_parse_json with invalid UTF-8."""
    # Invalid UTF-8 sequence
    data = b"\xff\xfe\xfd"
    result = _try_parse_json(data)
    assert result is None


@pytest.mark.unit
def test_try_parse_json_invalid_json():
    """Test _try_parse_json with invalid JSON (valid UTF-8)."""
    data = b"not valid json"
    result = _try_parse_json(data)
    assert result is None


@pytest.mark.unit
def test_try_parse_json_incomplete_json():
    """Test _try_parse_json with incomplete JSON."""
    data = b'{"incomplete":'
    result = _try_parse_json(data)
    assert result is None


@pytest.mark.unit
def test_try_parse_json_empty_bytes():
    """Test _try_parse_json with empty bytes."""
    result = _try_parse_json(b"")
    assert result is None


@pytest.mark.unit
def test_try_parse_json_ensures_ascii():
    """Test _try_parse_json ensures ASCII output."""
    data = b'{"unicode": "\\u00e9"}'  # é character
    result = _try_parse_json(data)
    assert result is not None
    # Should contain escaped unicode, not raw unicode
    assert "\\u" in result


# =============================================================================
# Tests for DeviceInfo dataclass
# =============================================================================

@pytest.mark.unit
def test_device_info_creation():
    """Test creating a DeviceInfo instance."""
    device = DeviceInfo(name="Test Device", address="AA:BB:CC:DD:EE:FF", rssi=-45)
    assert device.name == "Test Device"
    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert device.rssi == -45


@pytest.mark.unit
def test_device_info_immutable():
    """Test that DeviceInfo is immutable (frozen=True)."""
    device = DeviceInfo(name="Test", address="AA:BB:CC:DD:EE:FF", rssi=-50)
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        device.name = "Modified"


@pytest.mark.unit
def test_device_info_equality():
    """Test DeviceInfo equality comparison."""
    device1 = DeviceInfo(name="Test", address="AA:BB:CC:DD:EE:FF", rssi=-45)
    device2 = DeviceInfo(name="Test", address="AA:BB:CC:DD:EE:FF", rssi=-45)
    device3 = DeviceInfo(name="Other", address="AA:BB:CC:DD:EE:FF", rssi=-45)

    assert device1 == device2
    assert device1 != device3


# =============================================================================
# Tests for CharacteristicInfo dataclass
# =============================================================================

@pytest.mark.unit
def test_characteristic_info_creation():
    """Test creating a CharacteristicInfo instance."""
    char = CharacteristicInfo(
        key="svc:char:100",
        uuid="00002a00-0000-1000-8000-00805f9b34fb",
        properties=("read", "write"),
        service_uuid="00001800-0000-1000-8000-00805f9b34fb",
        char=None,
    )
    assert char.key == "svc:char:100"
    assert char.uuid == "00002a00-0000-1000-8000-00805f9b34fb"
    assert char.properties == ("read", "write")
    assert char.service_uuid == "00001800-0000-1000-8000-00805f9b34fb"


@pytest.mark.unit
def test_characteristic_info_immutable():
    """Test that CharacteristicInfo is immutable."""
    char = CharacteristicInfo(
        key="test", uuid="uuid", properties=("read",),
        service_uuid="svc", char=None
    )
    with pytest.raises(Exception):
        char.key = "modified"


@pytest.mark.unit
def test_characteristic_info_properties_tuple():
    """Test that properties is a tuple (immutable sequence)."""
    char = CharacteristicInfo(
        key="test", uuid="uuid", properties=("read", "notify"),
        service_uuid="svc", char=None
    )
    assert isinstance(char.properties, tuple)
    assert "read" in char.properties
    assert "notify" in char.properties


# =============================================================================
# Tests for LogEntry dataclass
# =============================================================================

@pytest.mark.unit
def test_log_entry_creation():
    """Test creating a LogEntry instance."""
    entry = LogEntry(
        ts="12:34:56.789",
        size=5,
        hex_str="48 65 6c 6c 6f",
        json_str=None,
    )
    assert entry.ts == "12:34:56.789"
    assert entry.size == 5
    assert entry.hex_str == "48 65 6c 6c 6f"
    assert entry.json_str is None


@pytest.mark.unit
def test_log_entry_with_json():
    """Test LogEntry with JSON string."""
    entry = LogEntry(
        ts="12:34:56.789",
        size=10,
        hex_str="7b 7d",
        json_str='{"key":"value"}',
    )
    assert entry.json_str == '{"key":"value"}'


@pytest.mark.unit
def test_log_entry_immutable():
    """Test that LogEntry is immutable."""
    entry = LogEntry(ts="12:00:00", size=1, hex_str="ff", json_str=None)
    with pytest.raises(Exception):
        entry.size = 2


# =============================================================================
# Edge case and integration tests
# =============================================================================

@pytest.mark.unit
def test_hex_groups_and_json_together():
    """Test hex_groups and try_parse_json work together on same data."""
    data = b'{"test": 123}'
    hex_result = _hex_groups(data)
    json_result = _try_parse_json(data)

    assert hex_result  # Should have hex representation
    assert json_result  # Should parse as JSON
    assert json.loads(json_result)["test"] == 123


@pytest.mark.unit
def test_hex_groups_large_data():
    """Test hex_groups with larger data."""
    data = bytes(range(256))  # 0x00 to 0xff
    result = _hex_groups(data)
    parts = result.split()
    assert len(parts) == 256
    assert parts[0] == "00"
    assert parts[255] == "ff"


@pytest.mark.unit
def test_device_info_with_empty_name():
    """Test DeviceInfo with empty name (unnamed device)."""
    device = DeviceInfo(name="", address="AA:BB:CC:DD:EE:FF", rssi=-999)
    assert device.name == ""
    assert device.rssi == -999


# =============================================================================
# Tests for pretty_json_with_highlighting()
# =============================================================================

@pytest.mark.unit
def test_pretty_json_with_highlighting_valid():
    """Test pretty-formatting with syntax highlighting for valid JSON."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    data = b'{"key": "value", "num": 42, "flag": true}'
    result = pretty_json_with_highlighting(data)

    assert result is not None
    assert "[cyan]" in result  # Keys highlighted
    assert "[green]" in result  # String values highlighted
    assert "[yellow]" in result  # Numbers highlighted
    assert "[magenta]" in result  # Booleans highlighted
    assert "\n" in result  # Multi-line formatting


@pytest.mark.unit
def test_pretty_json_with_highlighting_invalid():
    """Test that non-JSON data returns None."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    assert pretty_json_with_highlighting(b"not json") is None
    assert pretty_json_with_highlighting(b"\xff\xfe") is None


@pytest.mark.unit
def test_pretty_json_with_highlighting_nested():
    """Test pretty-formatting with nested objects."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    data = b'{"outer": {"inner": "value"}}'
    result = pretty_json_with_highlighting(data)

    assert result is not None
    assert "[cyan]" in result
    assert "outer" in result
    assert "inner" in result


@pytest.mark.unit
def test_pretty_json_with_highlighting_array():
    """Test pretty-formatting with arrays."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    data = b'{"items": [1, 2, 3], "count": 3}'
    result = pretty_json_with_highlighting(data)

    assert result is not None
    assert "[cyan]" in result  # Keys "items" and "count"
    assert "[yellow]" in result  # Number values (count: 3)


@pytest.mark.unit
def test_pretty_json_with_highlighting_null():
    """Test pretty-formatting with null values."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    data = b'{"value": null}'
    result = pretty_json_with_highlighting(data)

    assert result is not None
    assert "[magenta]" in result  # null highlighted
    assert "null" in result


# =============================================================================
# Tests for latest_value_markup()
# =============================================================================

@pytest.mark.unit
def test_latest_value_markup_with_json():
    """Test rendering latest value with JSON data."""
    from ble_tui.ui.renderers import latest_value_markup

    entry = LogEntry(
        ts="10:30:45.123",
        size=15,
        hex_str="7b 22 61 22 3a 31 7d",
        json_str='{"a":1}'
    )
    data = b'{"a": 1}'
    result = latest_value_markup(entry, data)

    assert "10:30:45.123" in result
    assert "15B" in result
    assert "Hex:" in result
    assert "JSON:" in result
    assert "[cyan]" in result  # Syntax highlighting present


@pytest.mark.unit
def test_latest_value_markup_binary_only():
    """Test rendering latest value with binary (non-JSON) data."""
    from ble_tui.ui.renderers import latest_value_markup

    entry = LogEntry(
        ts="10:30:45.123",
        size=5,
        hex_str="01 02 03 04 05",
        json_str=None
    )
    data = b"\x01\x02\x03\x04\x05"
    result = latest_value_markup(entry, data)

    assert "10:30:45.123" in result
    assert "Hex:" in result
    assert "JSON:" not in result  # No JSON section for binary data


@pytest.mark.unit
def test_latest_value_markup_includes_hex():
    """Test that latest value markup includes full hex string."""
    from ble_tui.ui.renderers import latest_value_markup

    entry = LogEntry(
        ts="10:30:45.123",
        size=3,
        hex_str="aa bb cc",
        json_str=None
    )
    data = b"\xaa\xbb\xcc"
    result = latest_value_markup(entry, data)

    assert "aa bb cc" in result
    assert "Hex:" in result
