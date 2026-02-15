# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python TUI (Terminal User Interface) application for scanning, connecting to, and interacting with BLE (Bluetooth Low Energy) devices on macOS, Linux, and Windows. The app discovers GATT services and characteristics, supports reading, writing, and notification subscriptions, and displays values in both hex and JSON formats.

## Running the Application

```bash
# Run the app (handles venv setup and dependency installation automatically)
./run.sh

# Or manually with Python
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

## Architecture

### Modular Async TUI Design

The application is a modular package under `ble_tui/` with a `BleTui` orchestration layer and focused submodules. The architecture follows an async event-driven model:

- **BLE operations**: `bleak` library provides async BLE scanning, connection, and GATT interaction
- **UI framework**: `textual` provides the TUI with four navigable panes (Devices, GATT, Latest Value, History)
- **Threading model**: BLE notifications use `call_from_thread()` to safely update the UI from callback threads
- **Latest Value Display**: `VerticalScroll` container wraps the latest value `Static` widget, enabling keyboard scrolling for long characteristic values (JSON, hex)

### Package Layout

- `ble_tui/app.py`: Textual app orchestration (`BleTui`)
- `ble_tui/models/`: `DeviceInfo`, `CharacteristicInfo`, `LogEntry`
- `ble_tui/services/`: `BleService`, `StateService`
- `ble_tui/ui/`: renderers, CSS styles, and modal dialogs (e.g. `WriteDialog`)
- `ble_tui/utils/`: formatting helpers and constants
- `app.py`: backward-compatible shim entry point

### Core Data Structures

- `DeviceInfo`: Immutable device records (name, address, RSSI)
- `CharacteristicInfo`: GATT characteristic metadata including UUID, properties, service UUID, and bleak char object
- `LogEntry`: Timestamped value logs with hex and optional JSON representations

### State Management

The app maintains state in instance variables and uses a `StateService` for shared device/ordering helpers:
- `_devices` and `_device_order`: Device registry and RSSI-sorted list
- `_client`: Active BleakClient connection (or None)
- `_services`: Discovered GATT services mapped by UUID
- `_key_by_handle`: Handle-to-key lookup for notification routing
- `_logs`: Per-characteristic deque of log entries (max 200)
- `_subscribed`: Set of characteristic keys with active notifications

### Key Flows

**Scan → Connect → Discover → Read/Write/Notify**

1. **Scan**: 10s BLE scan via `BleakScanner.discover()`, devices sorted by RSSI
2. **Connect**: `BleakClient` with 15s timeout, registers disconnect callback
3. **Discover**: Auto-discover all services/characteristics via `client.services`
4. **Read**: On-demand read via `client.read_gatt_char()`
5. **Write**: Write data via `client.write_gatt_char()`, supports text/hex input (F2 to toggle, defaults to text) via a modal dialog (`WriteDialog`). Write-with-response is used automatically when available.
6. **Notify**: Toggle subscription via `client.start_notify()` / `client.stop_notify()`

## Keybindings

- `s`: Scan for BLE devices
- `c` / `Enter`: Connect to selected device
- `d` / `Escape`: Disconnect
- `r`: Read selected characteristic
- `w`: Write to selected characteristic (opens text/hex input dialog, F2 to toggle mode)
- `Space` / `n`: Toggle notifications for selected characteristic
- `Tab` / `Shift+Tab`: Navigate between panes (Devices → GATT → Latest Value → History)
- `Arrow Keys`: Scroll through latest value display (when focused)
- `Page Up/Down`: Jump scroll through latest value display (when focused)
- `Home/End`: Jump to top/bottom of latest value display (when focused)
- `q`: Quit

## Error Handling

Errors are logged to `ble_tui_errors.log` with full tracebacks. The app uses non-blocking status messages for user feedback and continues operation after most errors.

## Platform Notes

- **Cross-platform BLE backends**: CoreBluetooth (macOS), BlueZ (Linux), and WinRT (Windows) via bleak
- **Python 3.13**: Current venv uses Python 3.13

## Testing

### Comprehensive Test Suite (94 Tests)

The project has a three-layer testing architecture:

**Unit Tests (48 tests)** - `tests/test_unit.py`, `tests/test_ble_service.py`, `tests/test_state_service.py`, `tests/test_renderers.py`, `tests/test_platform_support.py`
- Pure function tests: `_hex_groups()`, `_try_parse_json()`, `latest_value_markup()`, `parse_hex_string()`
- Data structure validation: `DeviceInfo`, `CharacteristicInfo`, `LogEntry`
- Fast, no dependencies, runs in CI

**Integration Tests (38 tests)**
- `tests/test_integration_tui.py` (22 tests): Textual UI testing with Pilot, including latest value scrolling, tab navigation, and write dialog
- `tests/test_integration_ble.py` (16 tests): BLE operations with mocked client
- Medium speed, mocked BLE, runs in CI

**E2E Tests (8 tests)** - `tests/test_e2e.py`
- Full workflow against real BLE device (LongBuddy-EMU by default)
- Requires hardware, skipped in CI unless enabled

### Running Tests

```bash
# Quick test run (unit + integration)
./run_tests.sh fast

# Specific test categories
./run_tests.sh unit           # Unit tests only
./run_tests.sh integration    # Integration tests only
./run_tests.sh e2e            # E2E tests (requires BLE device)

# Coverage analysis
./run_tests.sh coverage       # Generate HTML coverage report
```

### E2E Test Configuration

Enable E2E tests by setting environment variables:

```bash
# Create test configuration
cp .env.test.example .env.test

# Edit .env.test:
BLE_TEST_DEVICE_NAME=LongBuddy-EMU
BLE_RUN_E2E_TESTS=true

# Run E2E tests
./run_tests.sh e2e
```

### Test Infrastructure

**Mock Fixtures** (`tests/fixtures/`):
- `MockBLEDeviceBuilder`: Fluent API for building mock BLE devices
- `create_test_device()`: Generic test device with common services
- `create_longbuddy_emu()`: LongBuddy-EMU profile
- `create_device_with_notifications()`: Device with notifiable characteristics

**Configuration** (`tests/config.py`):
- Environment-based test configuration
- Device name/address configuration
- E2E test enable/disable
- Expected services/characteristics validation

See `TESTING.md` for detailed documentation.

## Helper Scripts

Helper scripts now support environment-based configuration:

- `ble_dump.py`: Connect and dump all services/characteristics
  - Configure with `BLE_TEST_DEVICE_ADDRESS` env var

- `ble_notify_probe.py`: Subscribe to characteristics and log notifications
  - Configure with `BLE_TEST_DEVICE_ADDRESS` and `BLE_TEST_NOTIFY_CHARS` env vars

Example usage:
```bash
export BLE_TEST_DEVICE_ADDRESS="AA:BB:CC:DD:EE:FF"
python3 ble_dump.py
```

## Development Tips

When modifying this codebase:
- All BLE operations must be async and handle disconnection gracefully
- UI updates from BLE callbacks must use `call_from_thread()`
- Textual's widget tree is: Header → Grid (4 navigable panes) → Status → Footer
- Latest value widget is wrapped in `VerticalScroll` container for keyboard scrolling
- Characteristic keys are composite: `{service_uuid}:{char_uuid}:{handle}`
- The app auto-scans on startup in `on_mount()`
- The documentation should be updated with new features and changes

### Testing Guidelines

- **Write tests first**: Start with unit tests for new functions
- **Run fast tests frequently**: `./run_tests.sh fast` during development
- **Check coverage before commits**: `./run_tests.sh coverage` (target: 85%+)
- **Use mock fixtures**: Leverage `tests/fixtures/` for consistent test data
- **E2E for critical paths**: Only test end-to-end flows that validate real hardware interaction
- **Keep tests independent**: Each test should set up and tear down its own state
