import aiohttp
from typing import List
from api_utils import HEADERS, GRID_URL
from tv_types import Channel

async def fetch_channels_async(session: aiohttp.ClientSession) -> List[Channel]:
    """Asynchronously fetch and return a list of channels."""
    print("Fetching channel data asynchronously...")
    try:
        async with session.post(GRID_URL, headers=HEADERS) as response:
            response.raise_for_status()
            grid_data = await response.json()
            if not grid_data or "d" not in grid_data or "channels" not in grid_data["d"]:
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
            return filtered_channels
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
        return []