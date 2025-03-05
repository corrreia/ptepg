import asyncio
import aiohttp
from typing import List
from datetime import datetime
from api_utils import HEADERS, PROGRAMS_URL, PROGRAM_DETAILS_URL
from tv_types import Channel, Program


async def fetch_program_details(
    session: aiohttp.ClientSession, program_id: str
) -> Program:
    """Asynchronously fetch and return details for the specified program."""
    print(f"Fetching details for program {program_id}...")
    data = {"service": "programdetail", "programID": program_id, "accountID": ""}
    try:
        async with session.post(
            PROGRAM_DETAILS_URL, json=data, headers=HEADERS
        ) as response:
            response.raise_for_status()
            program_data = await response.json()
            if not program_data or "d" not in program_data:
                print("Failed to fetch program details or invalid response.")
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
            p = program_data["d"]
            return {
                "id": str(p["uniqueId"]),
                "start_date_time": p["date"] + " " + p["startTime"],
                "end_date_time": p["date"] + " " + p["endTime"],
                "name": p["progName"],
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
    channel: Channel, start_date: datetime, end_date: datetime
) -> List[Program]:
    """Asynchronously fetch programs with full details for the specified channel and date range."""
    print(
        f"Fetching programs for {channel.get('name', 'unknown channel')} from {start_date} to {end_date}..."
    )
    data = {
        "service": "channelsguide",
        "channels": [channel["meo_id"]],
        "dateStart": start_date.isoformat() + "Z",
        "dateEnd": end_date.isoformat() + "Z",
        "accountID": "",
    }
    async with aiohttp.ClientSession() as session:
        # Fetch program list
        async with session.post(PROGRAMS_URL, json=data, headers=HEADERS) as response:
            response.raise_for_status()
            programs_data = await response.json()
            if (
                not programs_data
                or "d" not in programs_data
                or "channels" not in programs_data["d"]
            ):
                print("Failed to fetch programs or invalid response.")
                return []

            # Extract all program IDs
            program_ids = [
                p["uniqueId"]
                for ch in programs_data["d"]["channels"]
                for p in ch.get("programs", [])
                if "uniqueId" in p
            ]

            # Fetch details for all programs concurrently
            tasks = [fetch_program_details(session, pid) for pid in program_ids]
            programs = await asyncio.gather(*tasks)
            return programs


def fetch_programs(
    channel: Channel, start_date: datetime, end_date: datetime
) -> List[Program]:
    """Synchronous wrapper to run the asynchronous fetch_programs_async function."""
    return asyncio.run(fetch_programs_async(channel, start_date, end_date))
