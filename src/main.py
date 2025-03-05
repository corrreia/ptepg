from datetime import datetime, timedelta
import pytz
from typing import List
from channels import fetch_channels
from programs import fetch_programs
from tv_types import Channel


def main():
    """Orchestrate the fetching of channels and programs."""
    # Fetch channels
    channels: List[Channel] = fetch_channels()
    if not channels:
        print("No channels fetched. Exiting.")
        return

    # Print first few channels for demonstration
    print("Sample of fetched channels:")
    for channel in channels[:5]:
        print(channel)

    # Define date range (current time in UTC to 7 days ahead)
    start_date = datetime.now(pytz.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end_date = start_date + timedelta(days=7)

    # Fetch programs for all channels
    for channel in channels:
        channel["programs"] = fetch_programs(channel, start_date, end_date)
    print(f"Successfully attached programs to {len(channels)} channels.")

    # Print programs for the first channel as an example
    if channels:
        first_channel = channels[0]
        print(f"\nPrograms for {first_channel['name']} (first 5):")
        for program in first_channel["programs"][:5]:
            print(program)

    # export to json
    import json

    with open("channels.json", "w") as f:
        json.dump(channels, f, indent=4)
    print("Channels exported to channels.json")


if __name__ == "__main__":
    main()
