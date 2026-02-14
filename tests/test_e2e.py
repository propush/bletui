"""
End-to-End tests against real BLE devices.

These tests require a real BLE device to be available and are skipped
by default. Enable them by setting BLE_RUN_E2E_TESTS=true.

Environment variables:
- BLE_TEST_DEVICE_NAME: Device name to connect to (default: LongBuddy-EMU)
- BLE_TEST_DEVICE_ADDRESS: Optional device MAC address
- BLE_RUN_E2E_TESTS: Set to "true" to run E2E tests
- BLE_E2E_TIMEOUT: Timeout for operations in seconds (default: 15.0)
- BLE_EXPECTED_SERVICES: Comma-separated list of expected service UUIDs
- BLE_EXPECTED_READABLE_CHARS: Expected readable characteristic UUIDs
- BLE_EXPECTED_NOTIFIABLE_CHARS: Expected notifiable characteristic UUIDs
"""
import asyncio
import pytest
from bleak import BleakScanner, BleakClient
from tests.config import test_config


# Skip all E2E tests if not enabled
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.skipif(
        not test_config.run_e2e_tests,
        reason="E2E tests disabled. Set BLE_RUN_E2E_TESTS=true to enable."
    ),
]


@pytest.fixture
async def discovered_device_address():
    """Discover and return the test device address.

    Returns the device address if found, or skips the test if not found.
    """
    timeout = test_config.e2e_timeout

    # Scan for devices
    try:
        devices = await asyncio.wait_for(
            BleakScanner.discover(timeout=timeout, return_adv=True),
            timeout=timeout + 2.0
        )
    except asyncio.TimeoutError:
        pytest.skip(f"Scan timeout after {timeout}s")
        return None

    # Find device by name or address
    target_name = test_config.device_name
    target_address = test_config.device_address

    for device, adv_data in devices.values():
        device_name = device.name or adv_data.local_name or ""

        if target_address and device.address == target_address:
            return device.address

        if target_name and target_name in device_name:
            return device.address

    # Device not found
    pytest.skip(
        f"Device '{target_name}' (or address '{target_address}') not found in scan. "
        f"Found {len(devices)} devices."
    )
    return None


@pytest.fixture
async def connected_client(discovered_device_address):
    """Connect to the test device and return a connected BleakClient.

    Ensures proper cleanup on teardown.
    """
    if not discovered_device_address:
        pytest.skip("No device address available")

    client = BleakClient(discovered_device_address)

    try:
        await asyncio.wait_for(
            client.connect(),
            timeout=test_config.e2e_timeout
        )

        if not client.is_connected:
            pytest.skip(f"Failed to connect to {discovered_device_address}")

        yield client

    finally:
        # Cleanup
        if client.is_connected:
            try:
                await client.disconnect()
            except Exception:
                pass


@pytest.mark.e2e
async def test_e2e_scan_discovers_device():
    """Test that BLE scan discovers the target device."""
    timeout = test_config.e2e_timeout

    devices = await asyncio.wait_for(
        BleakScanner.discover(timeout=timeout, return_adv=True),
        timeout=timeout + 2.0
    )

    assert len(devices) > 0, "No BLE devices found during scan"

    # Check if target device is present
    target_name = test_config.device_name
    found = False

    for device, adv_data in devices.values():
        device_name = device.name or adv_data.local_name or ""
        if target_name in device_name:
            found = True
            break

    assert found, f"Target device '{target_name}' not found in scan results"


@pytest.mark.e2e
async def test_e2e_connect_to_device(discovered_device_address):
    """Test connecting to the real BLE device."""
    client = BleakClient(discovered_device_address)

    try:
        await asyncio.wait_for(
            client.connect(),
            timeout=test_config.e2e_timeout
        )

        assert client.is_connected, "Client should be connected"

    finally:
        if client.is_connected:
            await client.disconnect()


@pytest.mark.e2e
async def test_e2e_discover_services(connected_client):
    """Test discovering GATT services on the real device."""
    services = connected_client.services

    assert services is not None, "Services should not be None"

    # Convert to list to check length
    service_list = list(services)
    assert len(service_list) > 0, "Should discover at least one service"

    # If expected services are configured, verify them
    if test_config.expected_services:
        discovered_uuids = {svc.uuid.lower() for svc in services}

        for expected_uuid in test_config.expected_services:
            expected_lower = expected_uuid.lower()
            assert expected_lower in discovered_uuids, \
                f"Expected service {expected_uuid} not found. " \
                f"Discovered: {discovered_uuids}"


@pytest.mark.e2e
async def test_e2e_discover_characteristics(connected_client):
    """Test discovering characteristics on the real device."""
    services = connected_client.services

    total_chars = 0
    for svc in services:
        total_chars += len(svc.characteristics)

    assert total_chars > 0, "Should discover at least one characteristic"


@pytest.mark.e2e
async def test_e2e_read_characteristic(connected_client):
    """Test reading a characteristic from the real device."""
    services = connected_client.services

    # Find a readable characteristic
    readable_char = None
    for svc in services:
        for char in svc.characteristics:
            if "read" in char.properties:
                readable_char = char
                break
        if readable_char:
            break

    if not readable_char:
        pytest.skip("No readable characteristics found on device")

    # Read the characteristic
    try:
        data = await asyncio.wait_for(
            connected_client.read_gatt_char(readable_char),
            timeout=test_config.e2e_timeout
        )

        assert isinstance(data, (bytes, bytearray)), \
            f"Read data should be bytes, got {type(data)}"

        # Data can be empty, but should be bytes
        assert data is not None

    except Exception as e:
        pytest.fail(f"Failed to read characteristic {readable_char.uuid}: {e}")


@pytest.mark.e2e
async def test_e2e_subscribe_to_notifications(connected_client):
    """Test subscribing to notifications on the real device."""
    services = connected_client.services

    # Find a notifiable characteristic
    notifiable_char = None
    for svc in services:
        for char in svc.characteristics:
            if "notify" in char.properties or "indicate" in char.properties:
                notifiable_char = char
                break
        if notifiable_char:
            break

    if not notifiable_char:
        pytest.skip("No notifiable characteristics found on device")

    # Track if notification was received
    notification_received = asyncio.Event()
    notification_data = []

    def notification_callback(sender, data):
        notification_data.append(bytes(data))
        notification_received.set()

    try:
        # Subscribe
        await connected_client.start_notify(notifiable_char, notification_callback)

        # Wait for at least one notification (with timeout)
        try:
            await asyncio.wait_for(notification_received.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            # It's OK if no notification arrives - some devices don't send
            # notifications immediately
            pass

        # Unsubscribe
        await connected_client.stop_notify(notifiable_char)

        # If we received data, verify it
        if notification_data:
            assert isinstance(notification_data[0], bytes), \
                "Notification data should be bytes"

    except Exception as e:
        pytest.fail(
            f"Failed to subscribe to notifications on {notifiable_char.uuid}: {e}"
        )


@pytest.mark.e2e
async def test_e2e_full_workflow(discovered_device_address):
    """Test the complete scan → connect → discover → read → disconnect flow."""
    # Connect
    client = BleakClient(discovered_device_address)

    try:
        await asyncio.wait_for(
            client.connect(),
            timeout=test_config.e2e_timeout
        )

        assert client.is_connected

        # Discover services
        services = client.services
        service_list = list(services)
        assert len(service_list) > 0

        # Find and read a characteristic if available
        for svc in services:
            for char in svc.characteristics:
                if "read" in char.properties:
                    try:
                        data = await client.read_gatt_char(char)
                        assert data is not None
                        # Successfully read at least one char, test passes
                        return
                    except Exception:
                        # Try next characteristic
                        continue

        # If we get here, no readable chars found, but that's OK
        # The connection and discovery worked

    finally:
        # Disconnect
        if client.is_connected:
            await client.disconnect()

        # Verify disconnected
        assert not client.is_connected, "Client should be disconnected"


@pytest.mark.e2e
async def test_e2e_disconnect_and_reconnect(discovered_device_address):
    """Test that we can disconnect and reconnect to the device."""
    client = BleakClient(discovered_device_address)

    try:
        # First connection
        await asyncio.wait_for(
            client.connect(),
            timeout=test_config.e2e_timeout
        )
        assert client.is_connected

        # Disconnect
        await client.disconnect()
        await asyncio.sleep(0.5)  # Give it time to disconnect
        assert not client.is_connected

        # Reconnect
        await asyncio.wait_for(
            client.connect(),
            timeout=test_config.e2e_timeout
        )
        assert client.is_connected

    finally:
        if client.is_connected:
            await client.disconnect()
