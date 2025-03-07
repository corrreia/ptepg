import asyncio
import datetime

import aiohttp
import pytz

from typing import List
from models.epg import EPGChannel, EPGProgram
from jobs.channels import fetch_channels_async
from jobs.programs import fetch_programs_async
from src.schemas.epg import EpgChannelSchema
from utils.logger import logger
from utils.db import get_db


async def get_meo_epg():
    """Get the EPG from MEO and store it in the database.(updating it)"""
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
        end_date = start_date + datetime.timedelta(days=7)

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

        save_to_database(channels)

        # Step 4: Export to JSON
        import json

        with open("channels.json", "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=4, ensure_ascii=False)
        print("Channels and programs exported to channels.json")

    # Record end time
    end_time = datetime.now(pytz.utc)

    # Calculate time delta
    time_delta = end_time - start_time
    logger.info(f"EPG update took {time_delta.total_seconds()} seconds.")


def save_to_database(channels: List[EpgChannelSchema]):
    """
    Save EPG channels and programs to the database, updating existing records or inserting new ones.

    Args:
        db: SQLAlchemy database session.
        channels: List of channel dictionaries with attached programs.
    """
    # Fetch all existing channels by meo_id
    db = get_db()
    existing_channels = {ch.meo_id: ch for ch in db.query(EPGChannel).all()}
    channel_map = {}

    # Process channels: update existing or insert new
    for channel_data in channels:
        meo_id = channel_data["meo_id"]
        if meo_id in existing_channels:
            channel_db = existing_channels[meo_id]
            # Update fields
            channel_db.name = channel_data["name"]
            channel_db.description = channel_data["description"]
            channel_db.logo = channel_data["logo"]
            channel_db.theme = channel_data["theme"]
            channel_db.language = channel_data["language"]
            channel_db.region = channel_data["region"]
            channel_db.position = channel_data["position"]
            channel_db.isAdult = channel_data["isAdult"]
        else:
            channel_db = EPGChannel(
                meo_id=meo_id,
                name=channel_data["name"],
                description=channel_data["description"],
                logo=channel_data["logo"],
                theme=channel_data["theme"],
                language=channel_data["language"],
                region=channel_data["region"],
                position=channel_data["position"],
                isAdult=channel_data["isAdult"],
            )
            db.add(channel_db)
        channel_map[meo_id] = channel_db

    # Flush to assign IDs to new channels
    db.flush()

    # Collect all meo_program_ids from fetched programs
    all_meo_program_ids = [
        program["id"] for channel in channels for program in channel["programs"]
    ]

    # Fetch existing programs with these meo_program_ids
    existing_programs = (
        db.query(EPGProgram)
        .filter(EPGProgram.meo_program_id.in_(all_meo_program_ids))
        .all()
    )
    program_map = {p.meo_program_id: p for p in existing_programs}

    # Process programs: update existing or insert new
    for channel_data in channels:
        channel_db = channel_map[channel_data["meo_id"]]
        for program_data in channel_data["programs"]:
            meo_program_id = program_data["id"]
            if meo_program_id in program_map:
                program_db = program_map[meo_program_id]
                # Update fields
                program_db.start_date_time = program_data["start_date_time"]
                program_db.end_date_time = program_data["end_date_time"]
                program_db.name = program_data["name"]
                program_db.description = program_data["description"]
                program_db.imgM = program_data["imgM"]
                program_db.imgL = program_data["imgL"]
                program_db.imgXL = program_data["imgXL"]
                program_db.series_id = program_data["series_id"]
                program_db.channel_id = channel_db.id  # Ensure channel_id is correct
            else:
                program_db = EPGProgram(
                    meo_program_id=meo_program_id,
                    channel_id=channel_db.id,
                    start_date_time=program_data["start_date_time"],
                    end_date_time=program_data["end_date_time"],
                    name=program_data["name"],
                    description=program_data["description"],
                    imgM=program_data["imgM"],
                    imgL=program_data["imgL"],
                    imgXL=program_data["imgXL"],
                    series_id=program_data["series_id"],
                )
                db.add(program_db)

    # Commit all changes
    db.commit()
    print(f"Saved {len(channels)} channels and their programs to the database.")
