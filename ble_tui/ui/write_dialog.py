from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Label, TextArea


def parse_hex_string(hex_str: str) -> bytes | None:
    """Parse a hex string like 'AA BB CC' or 'AABBCC' into bytes.

    Returns None if the string contains invalid hex characters.
    """
    cleaned = hex_str.replace(" ", "").replace("\t", "").replace("\n", "")
    if not cleaned:
        return None
    if len(cleaned) % 2 != 0:
        return None
    try:
        return bytes.fromhex(cleaned)
    except ValueError:
        return None


class WriteDialog(ModalScreen[tuple[bytes, bool] | None]):
    """Modal dialog for writing data to a BLE characteristic."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("f2", "toggle_mode", "Hex/Text", show=True),
    ]

    DEFAULT_CSS = """
    WriteDialog {
        align: center middle;
    }
    #write-dialog-container {
        width: 70;
        height: auto;
        max-height: 30;
        background: #1a2235;
        border: solid #3a5070;
        padding: 1 2;
    }
    #write-dialog-title {
        text-style: bold;
        color: #96acd2;
        margin-bottom: 1;
    }
    #write-mode-row {
        height: 1;
        margin-bottom: 1;
    }
    #write-mode-label {
        color: #90a4c6;
    }
    #write-mode-value {
        color: #ffffff;
        text-style: bold;
    }
    #write-input {
        height: 7;
        margin-bottom: 1;
    }
    #write-response-checkbox {
        margin-bottom: 1;
    }
    #write-error {
        color: red;
        height: 1;
        margin-bottom: 1;
    }
    #write-buttons {
        height: 3;
        align: right middle;
    }
    #write-buttons Button {
        margin-left: 1;
    }
    """

    def __init__(
        self,
        char_uuid: str,
        has_write: bool = True,
        has_write_no_response: bool = False,
    ) -> None:
        super().__init__()
        self._char_uuid = char_uuid
        self._has_write = has_write
        self._has_write_no_response = has_write_no_response
        self._hex_mode = True

    def compose(self) -> ComposeResult:
        with Vertical(id="write-dialog-container"):
            yield Label(f"Write to {self._char_uuid}", id="write-dialog-title")
            with Horizontal(id="write-mode-row"):
                yield Label("Format: ", id="write-mode-label")
                yield Label("Hex", id="write-mode-value")
                yield Label("  (F2 to toggle)", classes="dim-hint")
            yield TextArea("", id="write-input", language=None)
            show_checkbox = self._has_write and self._has_write_no_response
            yield Checkbox(
                "Write with response",
                value=False,
                id="write-response-checkbox",
                classes="" if show_checkbox else "hidden",
            )
            yield Label("", id="write-error")
            with Horizontal(id="write-buttons"):
                yield Button("Cancel", variant="default", id="write-cancel")
                yield Button("Write", variant="primary", id="write-ok")

    def on_mount(self) -> None:
        self.query_one("#write-input", TextArea).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_toggle_mode(self) -> None:
        self._hex_mode = not self._hex_mode
        mode_label = self.query_one("#write-mode-value", Label)
        mode_label.update("Hex" if self._hex_mode else "Text")
        self.query_one("#write-error", Label).update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "write-cancel":
            self.dismiss(None)
            return

        if event.button.id == "write-ok":
            self._do_write()

    def _do_write(self) -> None:
        raw = self.query_one("#write-input", TextArea).text
        error_label = self.query_one("#write-error", Label)

        if not raw.strip():
            error_label.update("Input is empty")
            return

        if self._hex_mode:
            data = parse_hex_string(raw)
            if data is None:
                error_label.update("Invalid hex (use e.g. AA BB CC)")
                return
        else:
            data = raw.encode("utf-8")

        if self._has_write and self._has_write_no_response:
            # Both supported — let user choose via checkbox
            use_response = self.query_one("#write-response-checkbox", Checkbox).value
        elif self._has_write:
            # Only write-with-response supported
            use_response = True
        else:
            # Only write-without-response supported
            use_response = False

        self.dismiss((data, use_response))
