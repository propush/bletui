# Testing Guide for BleTui

This document describes the testing strategy and how to run tests for the BLE TUI application.

## Table of Contents

- [Test Architecture](#test-architecture)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Configuration](#configuration)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)

## Test Architecture

The test suite is organized into three layers (current total: 94 tests):

### 1. Unit Tests (50-60% of coverage)

**Locations:**
- `tests/test_unit.py`
- `tests/test_ble_service.py`
- `tests/test_state_service.py`
- `tests/test_renderers.py`

Fast, isolated tests for pure functions and data structures:
- `_hex_groups()` - Hex formatting
- `_try_parse_json()` - JSON parsing
- `parse_hex_string()` - Hex string to bytes conversion for write dialog
- `DeviceInfo`, `CharacteristicInfo`, `LogEntry` - Data structures
- `BleService` - BLE service behavior with mocked bleak APIs
- `StateService` - State transition and log management behavior
- UI renderer helpers (`status_line`, `characteristic_label`, `log_meta`, `log_line`)

**Run with:**
```bash
./run_tests.sh unit
```

### 2. Integration Tests (30-40% of coverage)

**Locations:**
- `tests/test_integration_tui.py` - TUI interaction tests
- `tests/test_integration_ble.py` - BLE operation tests

Medium-speed tests with mocked dependencies:
- TUI navigation and interaction (using Textual's Pilot)
- Write dialog interaction (open, cancel, hex submit)
- BLE operations with mocked `BleakClient`
- Service discovery, characteristic read/write/notify

**Run with:**
```bash
./run_tests.sh integration        # All integration tests
./run_tests.sh integration-tui    # TUI tests only
./run_tests.sh integration-ble    # BLE tests only
```

### 3. E2E Tests (10-15% of coverage)

**Location:** `tests/test_e2e.py`

Slow tests against real BLE hardware:
- Full scan → connect → discover → read → notify workflow
- Validates app works with actual devices
- Skipped by default (requires hardware)

**Run with:**
```bash
export BLE_TEST_DEVICE_NAME="LongBuddy-EMU"
export BLE_RUN_E2E_TESTS=true
./run_tests.sh e2e
```

## Setup

### 1. Install Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

### 2. Configure Test Environment

Copy the example configuration:

```bash
cp .env.test.example .env.test
```

Edit `.env.test` to match your environment:

```bash
# For LongBuddy-EMU device
BLE_TEST_DEVICE_NAME=LongBuddy-EMU
BLE_RUN_E2E_TESTS=true

# For a different device
BLE_TEST_DEVICE_NAME=MyDevice
BLE_TEST_DEVICE_ADDRESS=AA:BB:CC:DD:EE:FF
```

## Running Tests

### Quick Start

```bash
# Make the test runner executable
chmod +x run_tests.sh

# Run all tests (unit + integration, skips E2E by default)
./run_tests.sh

# Run only fast tests
./run_tests.sh fast

# Run with coverage report
./run_tests.sh coverage
```

### Running Specific Test Types

```bash
# Unit tests only
./run_tests.sh unit

# Integration tests
./run_tests.sh integration

# E2E tests (requires device)
export BLE_RUN_E2E_TESTS=true
./run_tests.sh e2e
```

### Running Individual Tests

```bash
# Run a specific test file
pytest tests/test_unit.py -v
pytest tests/test_renderers.py -v

# Run a specific test function
pytest tests/test_unit.py::test_hex_groups_empty -v

# Run tests matching a pattern
pytest -k "test_scan" -v
```

### Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run with markers
pytest -m unit -v              # Unit tests only
pytest -m integration -v       # Integration tests only
pytest -m e2e -v              # E2E tests only
pytest -m "not e2e" -v        # Everything except E2E

# Generate coverage report
pytest tests/ --cov=app --cov=ble_tui --cov-report=html
open htmlcov/index.html
```

## Configuration

### Environment Variables

All test configuration is done via environment variables:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `BLE_TEST_DEVICE_NAME` | Device name to test against | `LongBuddy-EMU` | `MyDevice` |
| `BLE_TEST_DEVICE_ADDRESS` | Device MAC address (optional) | - | `AA:BB:CC:DD:EE:FF` |
| `BLE_RUN_E2E_TESTS` | Enable E2E tests | `false` | `true` |
| `BLE_E2E_TIMEOUT` | Timeout for E2E operations (seconds) | `15.0` | `30.0` |
| `BLE_EXPECTED_SERVICES` | Expected service UUIDs (comma-separated) | - | `uuid1,uuid2` |
| `BLE_EXPECTED_READABLE_CHARS` | Expected readable char UUIDs | - | `uuid1,uuid2` |
| `BLE_EXPECTED_NOTIFIABLE_CHARS` | Expected notifiable char UUIDs | - | `uuid1,uuid2` |

### Configuration Methods

**1. Using .env.test file (recommended):**

```bash
cp .env.test.example .env.test
# Edit .env.test with your settings
./run_tests.sh
```

**2. Using environment variables:**

```bash
export BLE_TEST_DEVICE_NAME="MyDevice"
export BLE_RUN_E2E_TESTS=true
pytest tests/test_e2e.py -v
```

**3. Inline with command:**

```bash
BLE_TEST_DEVICE_NAME="MyDevice" BLE_RUN_E2E_TESTS=true pytest tests/test_e2e.py -v
```

## Writing Tests

### Unit Test Example

```python
import pytest
from ble_tui.utils.formatting import hex_groups

@pytest.mark.unit
def test_hex_groups_multiple_bytes():
    """Test _hex_groups with multiple bytes."""
    assert hex_groups(b"\x01\x02\x03") == "01 02 03"
```

### Integration Test Example

```python
import pytest
from unittest.mock import patch
from app import BleTui
from tests.fixtures import create_test_device, create_mock_scanner_with_devices

@pytest.mark.integration_tui
async def test_scan_with_mocked_scanner():
    """Test scan action with mocked BleakScanner."""
    device = create_test_device("TestDevice", "AA:BB:CC:DD:EE:FF", -45)
    scanner = create_mock_scanner_with_devices(device)

    with patch("ble_tui.services.ble_service.BleakScanner", scanner):
        async with BleTui().run_test() as pilot:
            await pilot.press("s")
            await pilot.pause(0.5)
            # Assert device was added
```

### E2E Test Example

```python
import pytest
from tests.config import test_config

@pytest.mark.e2e
async def test_e2e_connect_to_device(discovered_device_address):
    """Test connecting to the real BLE device."""
    client = BleakClient(discovered_device_address)
    await client.connect()
    assert client.is_connected
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests (skip E2E)
        env:
          BLE_RUN_E2E_TESTS: false
        run: pytest tests/ -m "not e2e" --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Local CI Simulation

Test what will run in CI:

```bash
BLE_RUN_E2E_TESTS=false ./run_tests.sh fast
```

## Test Coverage

### Current Coverage Targets

- **Overall:** 85%+
- **Unit tests:** 50-60% of total coverage
- **Integration tests:** 30-40% of total coverage
- **E2E tests:** 10-15% of total coverage

### Generating Coverage Reports

```bash
# HTML report
./run_tests.sh coverage
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=app --cov-report=term-missing

# XML report (for CI)
pytest tests/ --cov=app --cov-report=xml
```

## Troubleshooting

### E2E Tests Always Skip

**Problem:** E2E tests show as "skipped"

**Solution:**
```bash
export BLE_RUN_E2E_TESTS=true
./run_tests.sh e2e
```

### Device Not Found in E2E Tests

**Problem:** E2E tests skip with "Device not found"

**Solutions:**
1. Ensure device is powered on and in range
2. Check device name matches: `BLE_TEST_DEVICE_NAME=YourDevice`
3. Try specifying address: `BLE_TEST_DEVICE_ADDRESS=XX:XX:XX:XX:XX:XX`
4. Increase scan timeout: `BLE_E2E_TIMEOUT=30.0`

### Import Errors

**Problem:** `ImportError: No module named 'pytest'`

**Solution:**
```bash
pip install -r requirements-dev.txt
```

### Async Test Failures

**Problem:** `RuntimeError: Event loop is closed`

**Solution:** Tests use `pytest-asyncio` with `asyncio_mode = auto` in `pytest.ini`. Ensure you're using the latest version:
```bash
pip install --upgrade pytest-asyncio
```

## Best Practices

1. **Write unit tests first** - They're fast and catch most bugs
2. **Use fixtures** - Reuse common test setup via fixtures in `conftest.py`
3. **Mock external dependencies** - Use `unittest.mock` for BLE operations
4. **Test edge cases** - Empty inputs, errors, disconnections
5. **Keep E2E tests minimal** - They're slow and flaky; focus on critical paths
6. **Run fast tests frequently** - `./run_tests.sh fast` during development
7. **Run full suite before commit** - `./run_tests.sh coverage`

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Textual testing guide](https://textual.textualize.io/guide/testing/)
- [bleak documentation](https://bleak.readthedocs.io/)
