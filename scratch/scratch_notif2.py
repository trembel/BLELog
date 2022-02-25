import sys
import asyncio

from bleak import BleakClient


# you can change these to match your device or override them from the command line
CHARACTERISTIC_UUID = "182281a8-153a-11ec-82a8-0242ac130001"
ADDRESS = "eb:e5:31:bf:2e:b5"

def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print("{0}: {1}".format(sender, data))


# timeout = 120 # Windows
timeout = None

async def main(address, char_uuid):
    async with BleakClient(address, timeout=timeout) as client:
        print(f"Connected: {client.is_connected}")

        await client.start_notify(char_uuid, notification_handler)
        await asyncio.sleep(50.0)
        await client.stop_notify(char_uuid)


if __name__ == "__main__":
    asyncio.run(
        main(
            sys.argv[1] if len(sys.argv) > 1 else ADDRESS,
            sys.argv[2] if len(sys.argv) > 2 else CHARACTERISTIC_UUID,
        )
    )
