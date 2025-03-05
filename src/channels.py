from typing import List
from api_utils import make_post_request, GRID_URL
from tv_types import Channel


def fetch_channels() -> List[Channel]:
    """Fetch and return a list of channels."""
    print("Fetching channel data...")
    grid_data = make_post_request(GRID_URL)
    if not grid_data or "d" not in grid_data or "channels" not in grid_data["d"]:
        print("Failed to fetch channels or invalid response.")
        return []

    channels = grid_data["d"]["channels"]
    filtered_channels: List[Channel] = [
        {
            "id": str(ch["id"]),  # Convert integer ID to string
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
