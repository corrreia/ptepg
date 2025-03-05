import asyncio
import aiohttp
from typing import List
from tv_types import Channel
from utils import CHANNEL_DETAILS_URL, GRID_URL, HEADERS, increment_counter


async def fetch_channel_details_async(
    session: aiohttp.ClientSession, channel: Channel
) -> Channel:
    """Asynchronously fetch and return details for a specific channel."""
    print(f"Fetching details for channel {channel['name']}...")
    try:
        async with session.get(
            CHANNEL_DETAILS_URL + channel.get("meo_id"),
            headers=HEADERS,
        ) as response:
            increment_counter()
            response.raise_for_status()
            channel_data = await response.json()
            if not channel_data or "Result" not in channel_data:
                print("Failed to fetch channel details or invalid response.")
                return channel
            ch = channel_data["Result"]
            channel["description"] = ch.get("Description", "")
            channel["theme"] = ch.get("Thematic", "")
            channel["language"] = ch.get("Language", "")
            channel["region"] = ch.get("Region", "")
            channel["position"] = ch.get("ChannelPosition", -1)
            print(f"Fetched details for channel {channel['name']}.")
            return channel
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
        return channel


async def fetch_channels_async(session: aiohttp.ClientSession) -> List[Channel]:
    """Asynchronously fetch and return a list of channels."""
    print("Fetching channel data asynchronously...")
    try:
        async with session.post(GRID_URL, headers=HEADERS) as response:
            increment_counter()
            response.raise_for_status()
            grid_data = await response.json()
            if (
                not grid_data
                or "d" not in grid_data
                or "channels" not in grid_data["d"]
            ):
                print("Failed to fetch channels or invalid response.")
                return []
            channels = grid_data["d"]["channels"]
            filtered_channels: List[Channel] = [
                {
                    "id": str(ch["id"]),
                    "name": ch["name"],
                    "meo_id": ch["sigla"],
                    "logo": ch["logo"],
                    "isAdult": ch["isAdult"],
                    "programs": [],
                }
                for ch in channels
                if ch.get("id", -1) > 0 and "sigla" in ch
            ]
            print(f"Fetched {len(filtered_channels)} channels.")

            # Fetch details for each channel concurrently
            tasks = [
                fetch_channel_details_async(session, channel)
                for channel in filtered_channels
            ]
            return await asyncio.gather(*tasks)
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
        return []
