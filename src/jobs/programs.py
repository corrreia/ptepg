import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List
from schemas.epg import EpgChannelSchema, EpgProgramSchema
from utils.constants import HEADERS, PROGRAM_DETAILS_URL, PROGRAMS_URL
from utils.rate_limit import token_bucket


async def get_correct_dates(
    date_str: str, start_time_str: str, end_time_str: str
) -> tuple[str, str]:
    """
    Calculate the correct start and end date-time strings, adjusting for programs that span midnight.

    Args:
        date_str: The date string from the API (e.g., "4-3-2025").
        start_time_str: The start time (e.g., "22:43").
        end_time_str: The end time (e.g., "00:43").

    Returns:
        Tuple of (start_date_time, end_date_time) strings in "d-m-yyyy HH:MM" format.
    """
    # Parse the date
    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
    # Parse start and end times into time objects
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()

    # Construct the start datetime
    start_datetime = datetime.combine(date_obj, start_time)

    # Check if the end time is before the start time (indicating it’s on the next day)
    if end_time < start_time:
        end_datetime = datetime.combine(date_obj + timedelta(days=1), end_time)
    else:
        end_datetime = datetime.combine(date_obj, end_time)

    # Format back to strings
    start_str = start_datetime.strftime("%d-%m-%Y %H:%M")
    end_str = end_datetime.strftime("%d-%m-%Y %H:%M")

    return start_str, end_str


async def fetch_program_details(
    session: aiohttp.ClientSession, program_id: str
) -> EpgProgramSchema:
    """Fetch detailed information for a single program."""
    await token_bucket.acquire()  # Ensure request is rate-limited
    print(f"Fetching details for program {program_id}...")
    data = {"service": "programdetail", "programID": program_id, "accountID": ""}
    try:
        async with session.post(
            PROGRAM_DETAILS_URL, json=data, headers=HEADERS
        ) as response:
            if response.status != 200:
                print(f"Failed to fetch program details: {response.status}")
                return {
                    "id": program_id,
                    "start_date_time": "",
                    "end_date_time": "",
                    "name": "",
                    "description": "",
                    "imgM": "",
                    "imgL": "",
                    "imgXL": "",
                    "series_id": "",
                }
            program_data = await response.json()
            p = program_data.get("d", {})
            start_str, end_str = await get_correct_dates(
                p.get("date", ""), p.get("startTime", ""), p.get("endTime", "")
            )
            return {
                "id": str(p.get("uniqueId", program_id)),
                "start_date_time": start_str,
                "end_date_time": end_str,
                "name": p.get("progName", ""),
                "description": p.get("description", ""),
                "imgM": p.get("progImageM", ""),
                "imgL": p.get("progImageL", ""),
                "imgXL": p.get("progImageXL", ""),
                "series_id": p.get("seriesID", ""),
            }
    except aiohttp.ClientError as e:
        print(f"Request failed: {e}")
        return {
            "id": program_id,
            "start_date_time": "",
            "end_date_time": "",
            "name": "",
            "description": "",
            "imgM": "",
            "imgL": "",
            "imgXL": "",
            "series_id": "",
        }


async def fetch_programs_async(
    session: aiohttp.ClientSession,
    channels: List[EpgChannelSchema],
    start_date: datetime,
    end_date: datetime,
) -> List[EpgChannelSchema]:
    """Asynchronously fetch programs with full details for a batch of channels and return the channels with programs attached."""
    if not channels:
        return []

    # Limit to a maximum of 30 channels per request
    max_channels_per_request = 30
    if len(channels) > max_channels_per_request:
        print(
            f"Warning: Number of channels exceeds the limit. Only the first {max_channels_per_request} channels will be processed."
        )
        channels = channels[:max_channels_per_request]

    await token_bucket.acquire()  # Rate-limit the request
    print(f"Fetching programs for {len(channels)} channels...")
    data = {
        "service": "channelsguide",
        "channels": [channel["meo_id"] for channel in channels],
        "dateStart": start_date.isoformat() + "Z",
        "dateEnd": end_date.isoformat() + "Z",
        "accountID": "",
    }
    async with session.post(PROGRAMS_URL, json=data, headers=HEADERS) as response:
        response.raise_for_status()
        programs_data = await response.json()
        if (
            not programs_data
            or "d" not in programs_data
            or "channels" not in programs_data["d"]
        ):
            print("Failed to fetch programs or invalid response.")
            return channels  # Return channels without programs

        # Organize programs by channel
        channel_programs = {channel["meo_id"]: [] for channel in channels}
        for ch in programs_data["d"]["channels"]:
            meo_id = ch["sigla"]
            if meo_id in channel_programs:
                program_ids = [
                    p["uniqueId"] for p in ch.get("programs", []) if "uniqueId" in p
                ]
                tasks = [fetch_program_details(session, pid) for pid in program_ids]
                programs = await asyncio.gather(*tasks)
                channel_programs[meo_id] = programs

        # Attach programs to their respective channels
        for channel in channels:
            channel["programs"] = channel_programs.get(channel["meo_id"], [])

        return channels
