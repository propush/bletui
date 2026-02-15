# BLE TUI Design

## Understanding Summary
- Build a Python TUI app for macOS, Linux, and Windows to scan BLE devices and let the user choose one from a list sorted by signal strength (RSSI).
- The app discovers all services/characteristics (128-bit UUIDs) without prior UUID list.
- User selects which characteristics to read, write to, and subscribe/notify.
- Write support: modal dialog with hex/text input modes, write-with-response and write-without-response.
- Display characteristic values in hex and attempt UTF-8 JSON parsing when valid; otherwise hex only.
- Device list includes all discovered devices, even unnamed.
- Default non-functional assumptions: scan timeout 10s, connect timeout 15s, refresh 4 Hz, keep last 200 messages per characteristic.

## Assumptions
- JSON payloads are UTF-8 encoded and well-formed when present.
- Python with `bleak` is acceptable across macOS, Linux, and Windows.
- No authentication/pairing requirements beyond standard BLE connect.

## Decision Log
- D1: Use `textual` + `bleak` for the TUI. Alternatives: `urwid`, plain CLI. Chosen for best UX and async integration.
- D2: Device list includes all devices, sorted by RSSI.

## Architecture & Data Flow
- Modular package (`ble_tui/`) with `BleTui` orchestration in `ble_tui/app.py`.
- Async `textual` app with `bleak` for BLE I/O.
- Scan flow: 10s scan, collect all advertisements, deduplicate by address/identifier, sort by RSSI, populate device list.
- Connect flow: connect with 15s timeout, discover GATT services/characteristics, model in memory, render in UI.
- Read/write/notify flow: user triggers read, write, or toggles notification. Write opens a modal dialog for hex or text input. Notifications push log entries (max 200) to UI.

## UI & Interaction Model
- **Device List Pane**: rows show `RSSI | Name | Address`, sorted by RSSI. Select to connect.
- **GATT Explorer Pane**: services with characteristics and properties. Select to read/subscribe.
- **Latest Value Pane**: scrollable display of the most recent characteristic value with syntax-highlighted JSON and hex. Supports keyboard scrolling (arrow keys, Page Up/Down, Home/End).
- **History Log Pane**: timestamped entries with hex payload and parsed JSON when possible.

### Keybindings
- `s`: scan
- `c` / `enter`: select/connect
- `d` / `escape`: disconnect
- `r`: read selected characteristic
- `w`: write to selected characteristic (opens hex/text input dialog)
- `n` / `space`: toggle notifications for selected characteristic
- `tab` / `shift+tab`: navigate between panes (Devices → GATT → Latest Value → History)
- `↑` / `↓` / `Page Up` / `Page Down` / `Home` / `End`: scroll latest value (when focused)
- `q`: quit

## Parsing
- Hex: `bytes.hex()` (with grouping in UI for readability).
- JSON: attempt `json.loads(raw.decode("utf-8"))` and display parsed JSON if successful.

## Error Handling
- Non-blocking status messages for scan/connect timeouts and BLE exceptions.
- Graceful handling of disconnects.

## Testing

### Three-Layer Test Architecture

The project implements a comprehensive testing strategy with 94 total tests across three layers:

**1. Unit Tests (48 tests)**
- Pure function tests: `_hex_groups()`, `_try_parse_json()`, `latest_value_markup()`, `parse_hex_string()`
- Data structure tests: `DeviceInfo`, `CharacteristicInfo`, `LogEntry`
- Immutability and edge case validation
- Rendering and formatting helpers
- Fast, no external dependencies, runs in CI
- Coverage: ~50-60% of total

**2. Integration Tests (38 tests)**
- **TUI Integration (22 tests)**: Textual Pilot-based UI testing
  - Keyboard navigation (Tab, Shift+Tab, 4-pane navigation)
  - Latest value scrolling and widget structure
  - Scan action with mocked BleakScanner
  - Device selection and pane switching
  - GATT tree rendering
  - Write dialog open/cancel/submit flows
- **BLE Integration (16 tests)**: Mocked BleakClient testing
  - Connect/disconnect flows
  - GATT service/characteristic discovery
  - Read operations
  - Notification subscribe/unsubscribe
  - State management validation
- Medium speed, mocked dependencies, runs in CI
- Coverage: ~30-40% of total

**3. E2E Tests (8 tests)**
- Full workflow against real BLE hardware (LongBuddy-EMU)
- Scan → Connect → Discover → Read → Notify → Disconnect
- Service and characteristic validation
- Real-world device interaction
- Slow, requires hardware, skipped in CI by default
- Coverage: ~10-15% of total

### Test Configuration

Environment-based configuration via `.env.test`:
```bash
BLE_TEST_DEVICE_NAME=LongBuddy-EMU       # Device name for E2E tests
BLE_TEST_DEVICE_ADDRESS=<mac-address>    # Optional specific address
BLE_RUN_E2E_TESTS=true                   # Enable/disable E2E tests
BLE_E2E_TIMEOUT=15.0                     # Operation timeout in seconds
BLE_EXPECTED_SERVICES=<uuid1>,<uuid2>    # Expected services (validation)
```

### Running Tests

```bash
./run_tests.sh fast        # Unit + integration (no E2E)
./run_tests.sh unit        # Unit tests only
./run_tests.sh integration # Integration tests only
./run_tests.sh e2e         # E2E tests (requires device)
./run_tests.sh coverage    # All tests with coverage report
```

### Test Infrastructure

- **Mock Fixtures**: Builder pattern for BLE devices, services, and characteristics
- **Test Devices**: Predefined profiles (generic, LongBuddy-EMU, minimal, notifications)
- **CI/CD Ready**: E2E tests automatically skipped when `BLE_RUN_E2E_TESTS=false`
- **Coverage Target**: 85%+ overall

See `TESTING.md` for detailed testing documentation.
