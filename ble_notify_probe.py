#!/usr/bin/env python3
import asyncio
import os

from bleak import BleakClient


# Device address can be configured via environment variable
# Default is for LongBuddy-EMU on macOS
ADDR = os.getenv("BLE_TEST_DEVICE_ADDRESS", "A4486977-7944-04D0-ACB9-25ABF3578B51")

# Characteristic UUIDs can be configured via environment variable (comma-separated)
# Default is for LongBuddy-EMU characteristics
DEFAULT_CHARS = [
    "3f0d1003-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d2001-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d2002-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d3002-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d3004-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d4001-8f28-4a9a-bf69-90c7a1b20000",
    "3f0d4002-8f28-4a9a-bf69-90c7a1b20000",
]

chars_env = os.getenv("BLE_TEST_NOTIFY_CHARS", "")
if chars_env:
    CHARS = [c.strip() for c in chars_env.split(",") if c.strip()]
else:
    CHARS = DEFAULT_CHARS


def cb(sender, data):
    print(f"notify sender={sender} len={len(data)} hex={bytes(data).hex()}")


async def main():
    print(f"Connecting to {ADDR}...")
    print(f"Will probe {len(CHARS)} characteristic(s) for notifications")
    async with BleakClient(ADDR) as client:
        print("connected:", client.is_connected)

        for uuid in CHARS:
            try:
                await client.start_notify(uuid, cb)
                print("subscribed:", uuid)
            except Exception as exc:
                print(f"subscribe failed: {uuid} -> {exc!r}")

        await asyncio.sleep(12)

        for uuid in CHARS:
            try:
                await client.stop_notify(uuid)
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main())
