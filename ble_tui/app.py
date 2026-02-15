#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import traceback
from datetime import datetime
from typing import Any, Optional

from bleak import BleakClient
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Grid, Vertical, VerticalScroll
from textual.widgets import DataTable, Footer, Header, RichLog, Static, Tree

from ble_tui.models import CharacteristicInfo, DeviceInfo, LogEntry
from ble_tui.services import BleService, StateService
from ble_tui.ui.renderers import (
    characteristic_label,
    latest_value_markup,
    log_line,
    log_meta,
    status_line,
)
from ble_tui.ui.styles import APP_CSS
from ble_tui.ui.write_dialog import WriteDialog
from ble_tui.utils import ERROR_LOG_PATH, format_ble_error


class BleTui(App):
    ENABLE_COMMAND_PALETTE = False
    CSS = APP_CSS

    BINDINGS = [
        ("tab", "next_pane", "Next Pane"),
        ("shift+tab", "prev_pane", "Prev Pane"),
        ("s", "scan", "Scan"),
        ("c", "connect", "Connect"),
        ("d", "disconnect", "Disconnect"),
        ("enter", "connect", "Connect"),
        ("r", "read_char", "Read"),
        ("n", "toggle_notify", "Notify"),
        ("w", "write_char", "Write"),
        ("l", "clear_log", "Clear"),
        ("h", "toggle_value_height", "Expand"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._ble = BleService()
        self._state = StateService()
        self._ble_lock = asyncio.Lock()
        self._client: Optional[BleakClient] = None
        self._selected_device: Optional[str] = None
        self._selected_char: Optional[str] = None
        self._scan_in_progress = False
        self._expanded_value = False
        self._status_msg = "Ready"

    def compose(self) -> ComposeResult:
        yield Header()
        with Grid(id="main"):
            with Vertical(classes="pane right-divider"):
                yield Static("Devices", classes="pane-title")
                yield DataTable(id="devices")
            with Vertical(classes="pane right-divider"):
                yield Static("GATT", classes="pane-title")
                yield Tree("GATT", id="gatt")
            with Vertical(classes="pane"):
                yield Static("Values", classes="pane-title")
                yield Static("No characteristic selected", id="log_meta")
                with VerticalScroll(id="latest_value_scroll", classes="latest-value"):
                    yield Static("", id="latest_value")
                yield Static("History", classes="history-title")
                yield RichLog(id="log", wrap=True)
        yield Static("Ready", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        devices = self.query_one("#devices", DataTable)
        devices.add_columns("Conn", "RSSI", "Name", "Address")
        devices.cursor_type = "row"
        devices.zebra_stripes = True
        devices.focus()
        self._set_status("Auto-scanning for BLE devices...")
        asyncio.create_task(self.action_scan())

    def _set_status(self, msg: str) -> None:
        self._status_msg = msg
        self._render_status()

    def _render_status(self) -> None:
        line = status_line(
            status_msg=self._status_msg,
            connected_address=self._connected_address(),
            scan_in_progress=self._scan_in_progress,
            selected_char=self._selected_char,
            subscribed_count=len(self._state.subscribed),
        )
        self.query_one("#status", Static).update(line)

    def _record_error(self, context: str, exc: Exception) -> None:
        ts = datetime.now().isoformat(timespec="seconds")
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        try:
            with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {context}\n{details}\n")
        except Exception:
            pass

    def _connected_address(self) -> Optional[str]:
        return self._state.connected_address(self._client)

    def _restore_device_cursor(self, addr: Optional[str]) -> None:
        if not addr or addr not in self._state.device_order:
            if self._state.device_order:
                devices_table = self.query_one("#devices", DataTable)
                devices_table.move_cursor(row=0, column=0)
            return
        row_index = self._state.device_order.index(addr)
        devices_table = self.query_one("#devices", DataTable)
        devices_table.move_cursor(row=row_index, column=0)

    def _render_devices_table(self, preserve_addr: Optional[str] = None) -> None:
        devices_table = self.query_one("#devices", DataTable)
        devices_table.clear()
        connected_addr = self._connected_address()
        for addr in self._state.device_order:
            dev = self._state.devices.get(addr)
            if dev is None:
                continue
            conn_label = "ON" if connected_addr == addr else ""
            devices_table.add_row(
                conn_label, str(dev.rssi), dev.name, dev.address, key=dev.address
            )
        self._restore_device_cursor(preserve_addr)

    async def action_scan(self) -> None:
        if self._scan_in_progress:
            return
        async with self._ble_lock:
            self._scan_in_progress = True
            self._render_status()
            self._set_status("Scanning...")
            previous_addr = self._selected_device
            self._state.devices.clear()
            self._state.device_order.clear()
            self._render_devices_table(preserve_addr=previous_addr)

            try:
                devices = await self._ble.scan()
            except Exception as exc:
                self._record_error("scan", exc)
                self._scan_in_progress = False
                self._render_status()
                self._set_status(format_ble_error("Scan", exc, ERROR_LOG_PATH))
                return

            self._state.replace_devices(devices)
            self._render_devices_table(preserve_addr=previous_addr)

            self._scan_in_progress = False
            self._render_status()
            self._set_status(f"Scan complete: {len(devices)} device(s).")

    async def action_connect(self) -> None:
        async with self._ble_lock:
            self._select_device_from_cursor()
            if not self._selected_device:
                self._set_status("Select a device first.")
                return

            await self._disconnect_internal()

            addr = self._selected_device
            self._set_status(f"Connecting to {addr}...")

            def _on_disconnect(_: BleakClient) -> None:
                try:
                    self.call_from_thread(self._handle_disconnect)
                except Exception:
                    pass

            try:
                self._client = await self._ble.connect(
                    addr, disconnected_callback=_on_disconnect
                )
            except Exception as exc:
                self._record_error("connect", exc)
                self._set_status(format_ble_error("Connect", exc, ERROR_LOG_PATH))
                return

            self._render_devices_table(preserve_addr=addr)
            self._set_status(f"Connected: {addr}")
            await self._discover_gatt()
            self.query_one("#gatt", Tree).focus()

    async def action_disconnect(self) -> None:
        async with self._ble_lock:
            await self._disconnect_internal()
            self._set_status("Disconnected")

    async def _disconnect_internal(self) -> None:
        if self._client and self._client.is_connected:
            try:
                await self._ble.disconnect(self._client)
            except Exception as exc:
                self._record_error("disconnect", exc)
        self._client = None
        self._state.clear_connection_state()
        self._selected_char = None
        self._clear_gatt_ui()

    def _clear_gatt_ui(self) -> None:
        gatt = self.query_one("#gatt", Tree)
        gatt.clear()
        gatt.root.label = "GATT"
        gatt.refresh()
        self.query_one("#log_meta", Static).update("No characteristic selected")
        self.query_one("#latest_value", Static).update("")
        self.query_one("#log", RichLog).clear()
        self._render_devices_table(preserve_addr=self._selected_device)
        self._render_status()

    def _handle_disconnect(self) -> None:
        self._client = None
        self._state.clear_connection_state()
        self._selected_char = None
        self._clear_gatt_ui()
        self._set_status("Device disconnected unexpectedly")

    async def _discover_gatt(self) -> None:
        if not self._client:
            return

        try:
            (
                services_map,
                key_map,
                service_count,
                char_count,
            ) = await self._ble.discover_gatt(self._client)
        except Exception as exc:
            self._record_error("discover_gatt", exc)
            self._set_status(format_ble_error("Service discovery", exc, ERROR_LOG_PATH))
            return

        self._state.set_gatt(services_map, key_map)

        gatt = self.query_one("#gatt", Tree)
        gatt.clear()
        gatt.root.label = "GATT"
        root = gatt.root

        for svc_uuid, chars in self._state.services.items():
            svc_node = root.add(f"Service {svc_uuid}")
            for info in chars:
                svc_node.add(
                    characteristic_label(info, info.key in self._state.subscribed),
                    data=info,
                )
            svc_node.expand()

        gatt.root.expand()
        gatt.refresh()
        self._set_status(
            f"GATT loaded: {service_count} service(s), {char_count} characteristic(s)."
        )

    def _char_target(self, info: CharacteristicInfo) -> str | int:
        return self._state.char_target(info)

    def _sync_selected_char_from_tree(self) -> Optional[CharacteristicInfo]:
        gatt = self.query_one("#gatt", Tree)
        cursor_node = getattr(gatt, "cursor_node", None)
        if cursor_node is None:
            return None
        info = cursor_node.data
        if isinstance(info, CharacteristicInfo):
            self._selected_char = info.key
            self._render_status()
            return info
        return None

    async def action_read_char(self) -> None:
        async with self._ble_lock:
            if not self._client:
                self._set_status("Select a characteristic first.")
                return

            info = self._sync_selected_char_from_tree()
            if info is None and self._selected_char:
                info = self._state.find_char(self._selected_char)
            if not info or "read" not in info.properties:
                self._set_status("Selected characteristic is not readable.")
                return

            try:
                data = await self._ble.read_char(self._client, self._char_target(info))
            except Exception as exc:
                self._record_error("read_char", exc)
                self._set_status(f"Read failed (details in {ERROR_LOG_PATH})")
                return

            self._append_value(info.key, data)
            self._set_status(f"Read {info.uuid}")

    async def action_toggle_notify(self) -> None:
        async with self._ble_lock:
            if not self._client:
                self._set_status("Select a characteristic first.")
                return

            info = self._sync_selected_char_from_tree()
            if info is None and self._selected_char:
                info = self._state.find_char(self._selected_char)
            if not info or (
                "notify" not in info.properties and "indicate" not in info.properties
            ):
                self._set_status("Selected characteristic is not notifiable.")
                return

            if info.key in self._state.subscribed:
                try:
                    await self._ble.stop_notify(self._client, self._char_target(info))
                except Exception as exc:
                    self._record_error("stop_notify", exc)
                    self._set_status(
                        f"Stop notify failed (details in {ERROR_LOG_PATH})"
                    )
                    return
                self._state.subscribed.remove(info.key)
                self._set_status(f"Stopped notify {info.uuid}")
            else:

                def _cb(sender: Any, data: bytearray) -> None:
                    key = info.key
                    sender_handle = getattr(sender, "handle", None)
                    if isinstance(sender_handle, int):
                        key = self._state.key_by_handle.get(sender_handle, key)
                    self._dispatch_notify(key, bytes(data), info.uuid)

                try:
                    await self._ble.start_notify(
                        self._client, self._char_target(info), _cb
                    )
                except Exception as exc:
                    self._record_error("start_notify", exc)
                    self._set_status(
                        f"Start notify failed (details in {ERROR_LOG_PATH})"
                    )
                    return
                self._state.subscribed.add(info.key)
                self._set_status(f"Subscribed {info.uuid}")

            self._refresh_gatt_labels()
            self._render_status()

    async def action_write_char(self) -> None:
        if not self._client:
            self._set_status("Connect to a device first.")
            return

        info = self._sync_selected_char_from_tree()
        if info is None and self._selected_char:
            info = self._state.find_char(self._selected_char)

        has_write = info is not None and "write" in info.properties
        has_write_nr = info is not None and "write-without-response" in info.properties

        if not has_write and not has_write_nr:
            self._set_status("Selected characteristic is not writable.")
            return

        dialog = WriteDialog(
            char_uuid=info.uuid,
            has_write=has_write,
            has_write_no_response=has_write_nr,
        )

        def _on_dismiss(result: tuple[bytes, bool] | None) -> None:
            if result is None:
                return
            data, use_response = result
            asyncio.create_task(self._do_write(info, data, use_response))

        self.push_screen(dialog, callback=_on_dismiss)

    async def _do_write(
        self, info: CharacteristicInfo, data: bytes, use_response: bool
    ) -> None:
        async with self._ble_lock:
            try:
                await self._ble.write_char(
                    self._client, self._char_target(info), data, response=use_response
                )
            except Exception as exc:
                if use_response:
                    self._record_error("write_char (with-response, retrying without)", exc)
                    try:
                        await self._ble.write_char(
                            self._client, self._char_target(info), data, response=False
                        )
                    except Exception as exc2:
                        self._record_error("write_char (without-response)", exc2)
                        self._set_status(f"Write failed (details in {ERROR_LOG_PATH})")
                        return
                    self._set_status(
                        f"Wrote {len(data)} bytes to {info.uuid} (no-response fallback)"
                    )
                    return
                self._record_error("write_char", exc)
                self._set_status(f"Write failed (details in {ERROR_LOG_PATH})")
                return

        self._set_status(f"Wrote {len(data)} bytes to {info.uuid}")

    async def action_clear_log(self) -> None:
        """Clear history and current value for the selected characteristic."""
        if not self._selected_char:
            self._set_status("No characteristic selected to clear.")
            return

        info = self._state.find_char(self._selected_char)
        if not info:
            self._set_status("Selected characteristic not found.")
            return

        # Clear logs and latest data using StateService method
        self._state.clear_char_log(self._selected_char)

        # Re-render the log display (handles empty state gracefully)
        self._render_log(self._selected_char)

        # Provide user feedback
        self._set_status(f"Cleared history for {info.uuid}")

    def _find_char(self, key: str) -> Optional[CharacteristicInfo]:
        return self._state.find_char(key)

    def _append_value(self, key: str, data: bytes) -> None:
        self._state.append_value(key, data)
        if self._selected_char == key:
            self._render_log(key)

    def _dispatch_notify(self, key: str, data: bytes, uuid: str) -> None:
        try:
            self.call_from_thread(self._append_value, key, data)
            self.call_from_thread(self._set_status, f"Notify {uuid} ({len(data)} B)")
        except Exception:
            self._append_value(key, data)
            self._set_status(f"Notify {uuid} ({len(data)} B)")

    def _render_log(self, key: str) -> None:
        log_view = self.query_one("#log", RichLog)
        log_view.clear()

        info = self._state.find_char(key)
        self.query_one("#log_meta", Static).update(log_meta(info))

        # Update latest value display
        logs = self._state.logs.get(key, [])
        if logs:
            latest_entry = logs[-1]
            latest_data = self._state.latest_data.get(key, b"")
            self.query_one("#latest_value", Static).update(
                latest_value_markup(latest_entry, latest_data)
            )
        else:
            self.query_one("#latest_value", Static).update(
                "[dim]No data received yet[/]"
            )

        # Render history log
        for entry in logs:
            log_view.write(log_line(entry))

    def _iter_tree_nodes(self, root: Any) -> list[Any]:
        nodes: list[Any] = []
        stack = [root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            children = list(getattr(node, "children", []))
            if children:
                stack.extend(reversed(children))
        return nodes

    def _refresh_gatt_labels(self) -> None:
        gatt = self.query_one("#gatt", Tree)
        for node in self._iter_tree_nodes(gatt.root):
            info = node.data
            if isinstance(info, CharacteristicInfo):
                node.label = characteristic_label(
                    info, info.key in self._state.subscribed
                )

    def _select_device_from_cursor(self) -> bool:
        devices = self.query_one("#devices", DataTable)
        cursor_row = devices.cursor_row
        if cursor_row is None or cursor_row >= len(self._state.device_order):
            return False
        self._selected_device = self._state.device_order[cursor_row]
        return True

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        info = event.node.data
        if isinstance(info, CharacteristicInfo):
            self._selected_char = info.key
            self._render_status()
            self._render_log(info.key)

    async def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        info = event.node.data
        if isinstance(info, CharacteristicInfo):
            self._selected_char = info.key
            self._render_status()
            self._render_log(info.key)

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._selected_device = event.row_key.value

    async def on_data_table_row_highlighted(
        self, event: DataTable.RowHighlighted
    ) -> None:
        self._selected_device = event.row_key.value

    def _pane_widgets(self) -> list[Any]:
        return [
            self.query_one("#devices", DataTable),
            self.query_one("#gatt", Tree),
            self.query_one("#latest_value_scroll", VerticalScroll),
            self.query_one("#log", RichLog),
        ]

    def action_toggle_value_height(self) -> None:
        self._expanded_value = not self._expanded_value
        scroll = self.query_one("#latest_value_scroll", VerticalScroll)
        log = self.query_one("#log", RichLog)
        if self._expanded_value:
            scroll.add_class("expanded")
            log.add_class("collapsed")
        else:
            scroll.remove_class("expanded")
            log.remove_class("collapsed")

    async def action_next_pane(self) -> None:
        panes = self._pane_widgets()
        current = self.focused
        if current not in panes:
            panes[0].focus()
            return
        idx = panes.index(current)
        panes[(idx + 1) % len(panes)].focus()

    async def action_prev_pane(self) -> None:
        panes = self._pane_widgets()
        current = self.focused
        if current not in panes:
            panes[-1].focus()
            return
        idx = panes.index(current)
        panes[(idx - 1) % len(panes)].focus()

    async def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            event.prevent_default()
            event.stop()

            focused = self.focused
            if isinstance(focused, DataTable):
                if self._selected_device is None:
                    self._select_device_from_cursor()

                if self._client and self._client.is_connected:
                    if self._selected_device and self._selected_device == str(
                        self._client.address
                    ):
                        self._set_status(f"Already connected: {self._selected_device}")
                        return
                await self.action_connect()
                return

            if isinstance(focused, Tree):
                if self._selected_char:
                    info = self._state.find_char(self._selected_char)
                    if info and "read" in info.properties:
                        await self.action_read_char()
                        return
                self._set_status("Select a readable characteristic to read.")
                return

            # No action for Enter on other panes (Latest Value, History)
            return

        if event.key == "escape":
            await self.action_disconnect()
            return

        if event.key == "space":
            event.prevent_default()
            event.stop()
            await self.action_toggle_notify()

    async def on_shutdown(self) -> None:
        await self._disconnect_internal()


__all__ = ["BleTui"]
