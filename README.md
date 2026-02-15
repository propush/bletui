# BleTui

A Python Terminal User Interface (TUI) application for scanning, connecting to, and interacting with Bluetooth Low Energy (BLE) devices on macOS, Linux, and Windows.

![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-blue)
![Python](https://img.shields.io/badge/python-3.13-blue)
![Tests](https://img.shields.io/badge/tests-100%20fast%20passed-green)
![Coverage](https://img.shields.io/badge/coverage-85%2B%25-green)

## Features

- 🔍 **BLE Device Scanning** - Discover nearby BLE devices sorted by signal strength (RSSI)
- 🔌 **Device Connection** - Connect to any discovered BLE device
- 🔬 **GATT Explorer** - Browse all services and characteristics with a tree view
- 📖 **Characteristic Reading** - Read values from any readable characteristic
- ✏️ **Characteristic Writing** - Write text or hex data to writable characteristics via a modal dialog (F2 to toggle mode)
- 🔔 **Notifications** - Subscribe to characteristic notifications in real-time
- 📊 **Dual Display** - View values in both hex and JSON formats with syntax highlighting
- 📜 **Scrollable Latest Value** - Keyboard scrolling for long characteristic values (arrow keys, page up/down, home/end)
- 📈 **History Counter** - Live entry count display in history title (e.g., "History (45)"), shows max indicator at 200 entries
- ⌨️ **Keyboard Navigation** - Full keyboard control with intuitive shortcuts and 4-pane tab navigation
- ✅ **Comprehensive Testing** - 100 tests with 85%+ coverage

## Screenshots

![BleTui](images/bletui2.png)

## Quick Start

### Installation

```bash
# Clone the repository
git clone git@github.com:propush/bletui.git
cd bletui

# Run the app (automatically sets up venv and installs dependencies)
./run.sh
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app (backward-compatible entry point)
python3 app.py

# Or use the package entry point
python3 -m ble_tui
```

## Usage

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `s` | Scan for BLE devices |
| `c` / `Enter` | Connect to selected device |
| `d` / `Escape` | Disconnect from device |
| `r` | Read selected characteristic |
| `w` | Write to selected characteristic (text/hex input dialog, F2 to toggle) |
| `l` | Clear history and current value for selected characteristic |
| `Space` / `n` | Toggle notifications for selected characteristic |
| `Tab` | Navigate to next pane (Devices → GATT → Latest Value → History) |
| `Shift+Tab` | Navigate to previous pane |
| `↑` / `↓` | Scroll latest value display (when focused) |
| `Page Up` / `Page Down` | Jump scroll latest value display (when focused) |
| `Home` / `End` | Jump to top/bottom of latest value display (when focused) |
| `q` | Quit application |

### Workflow

1. **Scan**: Press `s` to scan for nearby BLE devices (10 seconds)
2. **Select**: Use arrow keys to select a device from the list
3. **Connect**: Press `Enter` to connect to the selected device
4. **Explore**: Browse services and characteristics in the GATT pane
5. **Read**: Select a characteristic and press `r` to read its value
6. **Write**: Press `w` to write text or hex data to a writable characteristic (F2 to toggle mode)
7. **Scroll**: Press `Tab` to focus the Latest Value pane, then use arrow keys to scroll through long values
8. **Notify**: Press `Space` to subscribe to notifications
9. **Disconnect**: Press `d` or `Escape` to disconnect

## Testing

### Test Suite Overview

The project includes **100 comprehensive tests** across three layers:

- **48 Unit Tests** - Fast, isolated tests for pure functions, models, services, and renderers
- **44 Integration Tests** - TUI and BLE operation tests with mocked dependencies, including write dialog, latest value scrolling, and history count display
- **8 E2E Tests** - Full workflow tests against real BLE hardware

### Running Tests

```bash
# Quick test run (unit + integration only)
./run_tests.sh fast

# Run specific test categories
./run_tests.sh unit           # Unit tests only
./run_tests.sh integration    # Integration tests only
./run_tests.sh e2e            # E2E tests (requires BLE device)

# Run all tests
./run_tests.sh all

# Generate coverage report
./run_tests.sh coverage
open htmlcov/index.html
```

### Test Results (Fast Suite)

```
==================== 100 passed, 8 deselected in 101.00s ========================
✓ Tests passed!
```

### E2E Testing with Real Devices

To enable E2E tests with your BLE device:

```bash
# Copy example configuration
cp .env.test.example .env.test

# Edit .env.test and configure:
# BLE_TEST_DEVICE_NAME=YourDevice
# BLE_RUN_E2E_TESTS=true

# Run E2E tests
./run_tests.sh e2e
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Helper Scripts

### ble_dump.py

Quick diagnostic script to connect to a device and dump all services/characteristics:

```bash
export BLE_TEST_DEVICE_ADDRESS="AA:BB:CC:DD:EE:FF"
python3 ble_dump.py
```

### ble_notify_probe.py

Test script to subscribe to multiple characteristics and log notifications:

```bash
export BLE_TEST_DEVICE_ADDRESS="AA:BB:CC:DD:EE:FF"
export BLE_TEST_NOTIFY_CHARS="uuid1,uuid2,uuid3"
python3 ble_notify_probe.py
```

## Architecture

### Technology Stack

- **UI Framework**: [Textual](https://textual.textualize.io/) - Modern TUI framework
- **BLE Library**: [Bleak](https://github.com/hbldh/bleak) - Cross-platform BLE library
- **Platform**: Cross-platform BLE backends via bleak (CoreBluetooth on macOS, BlueZ on Linux, WinRT on Windows)
- **Python**: 3.13+

### Core Components

The app now uses a modular package layout:

- `ble_tui/app.py`: Textual orchestration layer
- `ble_tui/models/`: `DeviceInfo`, `CharacteristicInfo`, `LogEntry`
- `ble_tui/services/`: BLE operations and state helpers
- `ble_tui/ui/`: CSS and rendering helpers
- `ble_tui/utils/`: constants and data-format helpers
- `app.py`: backward-compatible shim (`python3 app.py`)

**Key Flows**:
1. Scan → Discover devices via `BleakScanner.discover()`
2. Connect → Connect to device via `BleakClient`
3. Discover → Auto-discover services/characteristics
4. Read → Read characteristic values
5. Write → Write data to characteristics via modal dialog (hex/text)
6. Notify → Subscribe to characteristic notifications

See [DESIGN.md](DESIGN.md) for detailed architecture documentation.

## Development

### Prerequisites

- One of: macOS, Linux, or Windows with BLE support
- Python 3.13+
- Bluetooth enabled

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests during development
./run_tests.sh fast

# Check code coverage
./run_tests.sh coverage
```

### Development Guidelines

- All BLE operations must be async
- UI updates from BLE callbacks must use `call_from_thread()`
- Write unit tests for new functions
- Run `./run_tests.sh fast` before committing
- Maintain 85%+ test coverage

See [CLAUDE.md](CLAUDE.md) for detailed development guidance.

## Project Structure

```
.
├── app.py                      # Backward-compatible entry point
├── ble_tui/                    # Main package
│   ├── __init__.py
│   ├── __main__.py             # python -m ble_tui
│   ├── app.py                  # Textual orchestration
│   ├── models/                 # Dataclasses
│   ├── services/               # BLE and state services
│   ├── ui/                     # Styles and renderers
│   └── utils/                  # Formatting and constants
├── run.sh                      # App launcher script
├── requirements.txt            # App dependencies
├── requirements-dev.txt        # Development dependencies
├── pytest.ini                  # Pytest configuration
├── .env.test.example          # Example test configuration
├── run_tests.sh               # Test runner script
├── ble_dump.py                # Diagnostic script
├── ble_notify_probe.py        # Notification test script
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── config.py              # Test configuration
│   ├── conftest.py            # Pytest fixtures
│   ├── test_unit.py           # Core unit tests
│   ├── test_ble_service.py    # BLE service unit tests
│   ├── test_state_service.py  # State service unit tests
│   ├── test_renderers.py      # UI renderer unit tests
│   ├── test_integration_tui.py # TUI tests (15)
│   ├── test_integration_ble.py # BLE tests (14)
│   ├── test_e2e.py            # E2E tests (8)
│   └── fixtures/              # Mock fixtures
│       ├── __init__.py
│       ├── ble_fixtures.py    # Mock BLE builders
│       └── device_fixtures.py # Test device profiles
├── TESTING.md                 # Testing documentation
├── DESIGN.md                  # Architecture documentation
├── CLAUDE.md                  # Development guide
└── README.md                  # This file
```

## Error Handling

- Errors are logged to `ble_tui_errors.log` with full tracebacks
- Non-blocking status messages for user feedback
- Graceful handling of disconnections and timeouts
- App continues operation after most errors

## Platform Notes

- **macOS**: Uses CoreBluetooth via bleak/PyObjC
- **Linux**: Uses BlueZ via bleak (ensure `bluetoothd`/D-Bus are available)
- **Windows**: Uses WinRT BLE APIs via bleak
- **Python 3.13**: Tested with Python 3.13
- **Bluetooth**: Requires Bluetooth to be enabled at the OS level

## Limitations

- No BLE pairing/bonding support
- Write operations support hex and UTF-8 text input only
- Maximum 200 log entries per characteristic
- 10-second scan timeout and 15-second connect timeout by default

## Troubleshooting

### "No devices found"
- Ensure Bluetooth is enabled in your OS settings
- Check that the BLE device is powered on and advertising
- Try increasing scan timeout in code if needed

### "Connection failed"
- Device may be out of range
- Device may require pairing (not supported)
- Check `ble_tui_errors.log` for details

### Tests failing
- Ensure `requirements-dev.txt` is installed
- For E2E tests, ensure device is available and configured
- Check `BLE_RUN_E2E_TESTS` environment variable

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass: `./run_tests.sh coverage`
5. Maintain 85%+ test coverage
6. Submit a pull request

## License

[Your License Here]

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/)
- BLE support via [Bleak](https://github.com/hbldh/bleak)
- Tested against LongBuddy-EMU BLE device

## Related Documentation

- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [DESIGN.md](DESIGN.md) - Architecture and design decisions
- [CLAUDE.md](CLAUDE.md) - Development tips and guidelines
