import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz
from channels import fetch_channels_async
from programs import fetch_programs_async
from tv_types import Channel

async def main_async():
    """Asynchronously orchestrate the fetching of channels and programs."""
    async with aiohttp.ClientSession() as session:
        # Step 1: Fetch channels asynchronously
        channels = await fetch_channels_async(session)
        if not channels:
            print("No channels fetched. Exiting.")
            return

        # Print a sample of fetched channels
        print("Sample of fetched channels:")
        for channel in channels[:5]:
            print(channel)

        # Step 2: Define date range (current day to 7 days ahead)
        start_date = datetime.now(pytz.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=7)

        # Step 3: Fetch programs for all channels concurrently
        print("Fetching programs for all channels concurrently...")
        tasks = [
            fetch_programs_async(session, channel, start_date, end_date)
            for channel in channels
        ]
        all_programs = await asyncio.gather(*tasks)

        # Attach programs to their respective channels
        for channel, programs in zip(channels, all_programs):
            channel["programs"] = programs
        print(f"Successfully attached programs to {len(channels)} channels.")

        # Print programs for the first channel as an example
        if channels:
            first_channel = channels[0]
            print(f"\nPrograms for {first_channel['name']} (first 5):")
            for program in first_channel["programs"][:5]:
                print(program)

        # Step 4: Export to JSON
        import json
        with open("channels.json", "w") as f:
            json.dump(channels, f, indent=4)
        print("Channels and programs exported to channels.json")

if __name__ == "__main__":
    asyncio.run(main_async())