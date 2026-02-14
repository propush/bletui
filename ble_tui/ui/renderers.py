from __future__ import annotations

from typing import Optional

from ble_tui.models import CharacteristicInfo, LogEntry


def status_line(
    status_msg: str,
    connected_address: Optional[str],
    scan_in_progress: bool,
    selected_char: Optional[str],
    subscribed_count: int,
) -> str:
    conn = "Disconnected"
    if connected_address:
        conn = f"Connected {connected_address}"

    scan = "Scanning" if scan_in_progress else "Idle"
    selected = "-"
    if selected_char:
        parts = selected_char.split(":")
        if len(parts) > 1:
            selected = parts[1][:8]

    return (
        f"[CONN {conn}] [SCAN {scan}] [CHAR {selected}] "
        f"[NOTIFY {subscribed_count}] {status_msg}"
    )


def characteristic_label(info: CharacteristicInfo, subscribed: bool) -> str:
    props = ", ".join(info.properties)
    mark = " [N]" if subscribed else ""
    handle = getattr(info.char, "handle", None)
    handle_label = f" h={handle}" if handle is not None else ""
    return f"{info.uuid}{handle_label} [{props}]{mark}"


def log_meta(info: Optional[CharacteristicInfo]) -> str:
    if info is None:
        return "No characteristic selected"
    return f"{info.uuid} [{', '.join(info.properties)}]"


def log_line(entry: LogEntry) -> str:
    hex_preview = entry.hex_str
    if len(hex_preview) > 52:
        hex_preview = f"{hex_preview[:49]}..."
    if entry.json_str is not None:
        return f"{entry.ts} | {entry.size:4d}B | {hex_preview:<52} | {entry.json_str}"
    return f"{entry.ts} | {entry.size:4d}B | {hex_preview}"


def latest_value_markup(entry: LogEntry, data: bytes) -> str:
    """Render latest value with Rich markup for syntax highlighting."""
    from ble_tui.utils.formatting import pretty_json_with_highlighting

    lines = [
        f"[dim]{entry.ts}[/] | [yellow]{entry.size}B[/]",
        "",
        "[bold]Hex:[/]",
        entry.hex_str,
    ]

    pretty_json = pretty_json_with_highlighting(data)
    if pretty_json:
        lines.extend([
            "",
            "[bold]JSON:[/]",
            pretty_json
        ])

    return "\n".join(lines)
