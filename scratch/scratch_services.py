
# ADDRESS = 'E3:11:20:62:5D:3F'
# ADDRESS = 'e3:11:20:62:5d:3f'
# ADDRESS = 'EB:E5:31:BF:2E:B5'
ADDRESS = 'eb:e5:31:bf:2e:b5'
 
import sys
import asyncio

from bleak import BleakClient


async def main(address: str):
    # Note: any timeout less than 60 does not work great......
    async with BleakClient(address, timeout=60) as client:
        svcs = await client.get_services()
        print("Services:")
        for service in svcs:
            print(service)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) == 2 else ADDRESS))
