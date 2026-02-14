import pytest
from unittest.mock import Mock

from ble_tui.models import CharacteristicInfo, LogEntry
from ble_tui.ui.renderers import characteristic_label, log_line, log_meta, status_line


@pytest.mark.unit
def test_status_line_disconnected_idle():
    line = status_line(
        status_msg="Ready",
        connected_address=None,
        scan_in_progress=False,
        selected_char=None,
        subscribed_count=0,
    )

    assert "[CONN Disconnected]" in line
    assert "[SCAN Idle]" in line
    assert "[CHAR -]" in line
    assert "[NOTIFY 0]" in line


@pytest.mark.unit
def test_status_line_connected_and_selected_char():
    line = status_line(
        status_msg="ok",
        connected_address="AA:BB",
        scan_in_progress=True,
        selected_char="svc:1234567890:10",
        subscribed_count=2,
    )

    assert "[CONN Connected AA:BB]" in line
    assert "[SCAN Scanning]" in line
    assert "[CHAR 12345678]" in line
    assert "[NOTIFY 2]" in line


@pytest.mark.unit
def test_characteristic_label_includes_handle_and_notify_mark():
    char = Mock()
    char.handle = 101
    info = CharacteristicInfo(
        key="svc:char:101",
        uuid="char-uuid",
        properties=("notify", "read"),
        service_uuid="svc",
        char=char,
    )

    label = characteristic_label(info, subscribed=True)

    assert label == "char-uuid h=101 [notify, read] [N]"


@pytest.mark.unit
def test_log_meta_none_and_with_info():
    assert log_meta(None) == "No characteristic selected"

    char = Mock()
    info = CharacteristicInfo(
        key="k",
        uuid="char-uuid",
        properties=("read",),
        service_uuid="svc",
        char=char,
    )
    assert log_meta(info) == "char-uuid [read]"


@pytest.mark.unit
def test_log_line_json_and_long_hex():
    json_entry = LogEntry(ts="12:00:00.000", size=2, hex_str="7b 7d", json_str="{}")
    assert "| {}" in log_line(json_entry)

    long_hex = " ".join(["aa"] * 40)
    plain_entry = LogEntry(ts="12:00:00.000", size=40, hex_str=long_hex, json_str=None)
    line = log_line(plain_entry)
    assert "..." in line
    assert "12:00:00.000" in line
