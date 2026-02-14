import asyncio
import os
from bleak import BleakClient

# Device address can be configured via environment variable
# Default is for LongBuddy-EMU
ADDR = os.getenv("BLE_TEST_DEVICE_ADDRESS", "A4486977-7944-04D0-ACB9-25ABF3578B51")

async def main():
    print(f"Connecting to {ADDR}...")
    async with BleakClient(ADDR) as client:
        print("connected:", client.is_connected)
        services = client.services
        for svc in services:
            print("SVC", svc.uuid)
            for ch in svc.characteristics:
                props = ",".join(sorted(ch.properties))
                handle = getattr(ch, "handle", None)
                print("  CHAR", ch.uuid, "props=", props, "handle=", handle)

asyncio.run(main())
