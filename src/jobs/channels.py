import asyncio
import aiohttp
from typing import List
from schemas.epg import EpgChannelSchema
from utils.constants import CHANNEL_DETAILS_URL, GRID_URL, HEADERS
from utils.rate_limit import token_bucket
from utils.logger import logger


async def fetch_channel_details_async(
    session: aiohttp.ClientSession, channel: EpgChannelSchema
) -> EpgChannelSchema:
    """Asynchronously fetch and return details for a specific channel."""
    await token_bucket.acquire()  # Ensure request is rate-limited
    logger.info(f"Fetching details for channel {channel['name']}...")
    try:
        async with session.get(
            CHANNEL_DETAILS_URL + channel.get("meo_id"),
            headers=HEADERS,
        ) as response:
            response.raise_for_status()
            channel_data = await response.json()
            if not channel_data or "Result" not in channel_data:
                logger.error("Failed to fetch channel details or invalid response.")
                return channel
            ch = channel_data["Result"]
            channel["description"] = ch.get("Description", "")
            channel["theme"] = ch.get("Thematic", "")
            channel["language"] = ch.get("Language", "")
            channel["region"] = ch.get("Region", "")
            channel["position"] = ch.get("ChannelPosition", -1)
            logger.info(f"Fetched details for channel {channel['name']}.")
            return channel
    except aiohttp.ClientError as e:
        logger.error(f"Request failed: {e}")
        return channel


async def fetch_channels_async(
    session: aiohttp.ClientSession,
) -> List[EpgChannelSchema]:
    """Asynchronously fetch and return a list of channels."""
    await token_bucket.acquire()  # Ensure request is rate-limited
    logger.info("Fetching channel data asynchronously...")
    try:
        async with session.post(GRID_URL, headers=HEADERS) as response:
            response.raise_for_status()
            grid_data = await response.json()
            if (
                not grid_data
                or "d" not in grid_data
                or "channels" not in grid_data["d"]
            ):
                logger.error("Failed to fetch channels or invalid response.")
                return []
            channels = grid_data["d"]["channels"]
            filtered_channels: List[EpgChannelSchema] = [
                {
                    "id": str(ch["id"]),
                    "meo_id": ch["sigla"],
                    "name": ch["name"],
                    "description": "",
                    "logo": ch["logo"],
                    "theme": "",
                    "language": "",
                    "region": "",
                    "position": -1,
                    "isAdult": ch["isAdult"],
                    "programs": [],
                }
                for ch in channels
                if ch.get("id", -1) > 0 and "sigla" in ch
            ]
            logger.info(f"Fetched {len(filtered_channels)} channels.")

            # Fetch details for each channel concurrently
            tasks = [
                fetch_channel_details_async(session, channel)
                for channel in filtered_channels
            ]
            return await asyncio.gather(*tasks)
    except aiohttp.ClientError as e:
        logger.error(f"Request failed: {e}")
        return []
