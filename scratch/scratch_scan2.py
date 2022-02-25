import asyncio

from bleak import BleakScanner


async def main(wanted_name):
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and d.name.lower() == wanted_name.lower()
    )
    print(device)


if __name__ == "__main__":
    asyncio.run(main("SmartPatch"))
