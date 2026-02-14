"""
Test configuration module.

Provides environment-based configuration for BLE TUI tests,
allowing tests to work with different BLE devices across environments.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestConfig:
    """Configuration for BLE TUI tests loaded from environment variables."""

    # Device configuration
    device_name: str = "LongBuddy-EMU"
    device_address: Optional[str] = None

    # Test control
    run_e2e_tests: bool = False
    e2e_timeout: float = 15.0

    # Expected GATT characteristics (for E2E validation)
    expected_services: list[str] = field(default_factory=list)
    expected_readable_chars: list[str] = field(default_factory=list)
    expected_notifiable_chars: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "TestConfig":
        """Create TestConfig from environment variables.

        Environment variables:
        - BLE_TEST_DEVICE_NAME: Device name to test against (default: LongBuddy-EMU)
        - BLE_TEST_DEVICE_ADDRESS: Optional device MAC address
        - BLE_RUN_E2E_TESTS: Enable E2E tests (true/false, default: false)
        - BLE_E2E_TIMEOUT: Timeout for E2E operations in seconds (default: 15.0)
        - BLE_EXPECTED_SERVICES: Comma-separated list of expected service UUIDs
        - BLE_EXPECTED_READABLE_CHARS: Comma-separated list of expected readable char UUIDs
        - BLE_EXPECTED_NOTIFIABLE_CHARS: Comma-separated list of expected notifiable char UUIDs
        """
        def parse_bool(value: str) -> bool:
            return value.lower() in ("true", "1", "yes", "on")

        def parse_list(value: str) -> list[str]:
            if not value:
                return []
            return [item.strip() for item in value.split(",") if item.strip()]

        return cls(
            device_name=os.getenv("BLE_TEST_DEVICE_NAME", "LongBuddy-EMU"),
            device_address=os.getenv("BLE_TEST_DEVICE_ADDRESS"),
            run_e2e_tests=parse_bool(os.getenv("BLE_RUN_E2E_TESTS", "false")),
            e2e_timeout=float(os.getenv("BLE_E2E_TIMEOUT", "15.0")),
            expected_services=parse_list(os.getenv("BLE_EXPECTED_SERVICES", "")),
            expected_readable_chars=parse_list(os.getenv("BLE_EXPECTED_READABLE_CHARS", "")),
            expected_notifiable_chars=parse_list(os.getenv("BLE_EXPECTED_NOTIFIABLE_CHARS", "")),
        )


# Global test configuration instance
test_config = TestConfig.from_env()
