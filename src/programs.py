import asyncio
import aiohttp
from datetime import datetime
from typing import List
from api_utils import HEADERS, PROGRAM_DETAILS_URL, PROGRAMS_URL
from tv_types import Channel, Program

async def fetch_program_details(session: aiohttp.ClientSession, program_id: str) -> Program:
    """Fetch detailed information for a single program and return a Program object."""
    data = {"service": "programdetail", "programID": program_id, "accountID": ""}
    
    try:
        async with session.post(PROGRAM_DETAILS_URL, json=data, headers=HEADERS) as response:
            if response.status != 200:
                # Return a default Program object if the request fails
                return {
                    "id": program_id,
                    "start_date_time": "",
                    "end_date_time": "",
                    "name": "",
                    "description": "",
                    "imgM": "",
                    "imgL": "",
                    "imgXL": "",
                    "series_id": ""
                }
            program_data = await response.json()
            p = program_data.get("d", {})  # Assuming 'd' is the key containing program details
            
            # Construct the Program object by mapping API fields to Program fields
            return {
                "id": str(p.get("uniqueId", program_id)),  # Use program_id as fallback
                "start_date_time": f"{p.get('date', '')} {p.get('startTime', '')}".strip(),
                "end_date_time": f"{p.get('date', '')} {p.get('endTime', '')}".strip(),
                "name": p.get("progName", ""),
                "description": p.get("description", ""),
                "imgM": p.get("progImageM", ""),
                "imgL": p.get("progImageL", ""),
                "imgXL": p.get("progImageXL", ""),
                "series_id": p.get("seriesID", "")
            }
    except aiohttp.ClientError as e:
        # Return a default Program object on exception
        return {
            "id": program_id,
            "start_date_time": "",
            "end_date_time": "",
            "name": "",
            "description": "",
            "imgM": "",
            "imgL": "",
            "imgXL": "",
            "series_id": ""
        }

async def fetch_programs_async(session: aiohttp.ClientSession, channel: Channel, start_date: datetime, end_date: datetime) -> List[Program]:
    """Asynchronously fetch programs with full details for the specified channel and date range."""
    print(f"Fetching programs for {channel.get('name', 'unknown channel')}...")
    data = {
        "service": "channelsguide",
        "channels": [channel["meo_id"]],
        "dateStart": start_date.isoformat() + "Z",
        "dateEnd": end_date.isoformat() + "Z",
        "accountID": "",
    }
    async with session.post(PROGRAMS_URL, json=data, headers=HEADERS) as response:
        response.raise_for_status()
        programs_data = await response.json()
        if not programs_data or "d" not in programs_data or "channels" not in programs_data["d"]:
            print("Failed to fetch programs or invalid response.")
            return []

        # Extract all program IDs
        program_ids = [p["uniqueId"] for ch in programs_data["d"]["channels"] for p in ch.get("programs", []) if "uniqueId" in p]
        
        # Fetch details for all programs concurrently
        tasks = [fetch_program_details(session, pid) for pid in program_ids]
        programs = await asyncio.gather(*tasks)
        return programs