import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List
from api_utils import HEADERS, PROGRAM_DETAILS_URL, PROGRAMS_URL
from tv_types import Channel, Program

async def get_correct_dates(date_str: str, start_time_str: str, end_time_str: str) -> tuple[str, str]:
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

async def fetch_program_details(session: aiohttp.ClientSession, program_id: str) -> Dict:
    """
    Fetch detailed information for a single program and return a Program object with corrected dates.
    
    Args:
        session: The aiohttp session for making the request.
        program_id: The ID of the program to fetch.
    
    Returns:
        A dictionary representing the Program with corrected start and end times.
    """
    # Log the request (assuming logger is defined)
    print(f"Fetching details for program {program_id}...")
    data = {"service": "programdetail", "programID": program_id, "accountID": ""}
    
    try:
        async with session.post(PROGRAM_DETAILS_URL, json=data, headers=HEADERS) as response:
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
                    "series_id": ""
                }
            program_data = await response.json()
            p = program_data.get("d", {})
            
            # Get corrected start and end times
            start_str, end_str = await get_correct_dates(
                p.get("date", ""),
                p.get("startTime", ""),
                p.get("endTime", "")
            )
            
            # Return the Program object with corrected dates
            return {
                "id": str(p.get("uniqueId", program_id)),
                "start_date_time": start_str,
                "end_date_time": end_str,
                "name": p.get("progName", ""),
                "description": p.get("description", ""),
                "imgM": p.get("progImageM", ""),
                "imgL": p.get("progImageL", ""),
                "imgXL": p.get("progImageXL", ""),
                "series_id": p.get("seriesID", "")
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