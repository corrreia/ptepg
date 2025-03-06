import asyncio
import aiohttp
from datetime import datetime, timedelta
import pytz
from channels import fetch_channels_async
from programs import fetch_programs_async
import utils



async def main_async():
    """Asynchronously orchestrate the fetching of channels and programs."""

    # Record start time
    start_time = datetime.now(pytz.utc)

    async with aiohttp.ClientSession() as session:
        # Step 1: Fetch channels asynchronously
        channels = await fetch_channels_async(session)
        if not channels:
            print("No channels fetched. Exiting.")
            return

        # Step 2: Define date range (current day to 7 days ahead)
        start_date = datetime.now(pytz.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
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

        # Step 4: Export to JSON
        import json

        with open("channels.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=4, ensure_ascii=False)
        print("Channels and programs exported to channels.json")

    # Record end time
    end_time = datetime.now(pytz.utc)

    # Calculate time delta
    time_delta = end_time - start_time

    # Print results
    print(f"Total time taken: {time_delta.total_seconds()} seconds")
    print(f"Total requests made: {utils.request_counter} equivelant to {utils.request_counter/ time_delta.total_seconds()} requests per second")


if __name__ == "__main__":
    asyncio.run(main_async())
