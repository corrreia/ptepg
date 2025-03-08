from datetime import datetime, timedelta
import aiohttp
import pytz
from typing import List
from models.epg import EPGChannelModel, EPGProgramModel
from jobs.channels import fetch_channels_async
from jobs.programs import fetch_programs_async
from utils.constants import DAYS_TO_FETCH
from utils.logger import logger
from utils.db import get_db


async def get_meo_epg():
    """Get the EPG from MEO and store it in the database.(updating it)"""
    start_time = datetime.now(pytz.utc)

    async with aiohttp.ClientSession() as session:
        # Step 1: Fetch channels asynchronously
        channels = await fetch_channels_async(session)
        if not channels:
            logger.error("No channels fetched. Exiting.")
            return

        start_date = datetime.now(pytz.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date = start_date + timedelta(days=DAYS_TO_FETCH)

        # Process channels in batches of 30
        batch_size = 30
        all_updated_channels = []  # Initialize an empty list to store all channels

        for i in range(0, len(channels), batch_size):
            batch = channels[i : i + batch_size]
            batch_updated_channels = await fetch_programs_async(
                session, batch, start_date, end_date
            )
            # Add this batch's channels to our accumulated list
            all_updated_channels.extend(batch_updated_channels)

        # Save all channels to the database
        save_to_database(all_updated_channels)

    # Record end time
    end_time = datetime.now(pytz.utc)

    # Calculate time delta
    time_delta = end_time - start_time
    logger.info(f"EPG update took {time_delta.total_seconds()} seconds.")


def save_to_database(channels: List[dict]):
    """
    Save EPG channels and programs to the database, updating existing records or inserting new ones.

    Args:
        channels: List of dictionaries containing channel data and their associated programs.
    """
    # Get the actual database session from the generator
    db = next(get_db())

    try:
        for channel in channels:
            # Check if the channel already exists in the database by its unique meo_id
            existing_channel = (
                db.query(EPGChannelModel).filter_by(meo_id=channel["meo_id"]).first()
            )

            if existing_channel:
                # Update existing channel fields
                existing_channel.name = channel["name"]
                existing_channel.description = channel["description"]
                existing_channel.logo = channel["logo"]
                existing_channel.theme = channel["theme"]
                existing_channel.language = channel["language"]
                existing_channel.region = channel["region"]
                existing_channel.position = channel["position"]
                existing_channel.isAdult = channel["isAdult"]
                channel_model = existing_channel
            else:
                # Create a new channel record
                channel_model = EPGChannelModel(
                    meo_id=channel["meo_id"],
                    name=channel["name"],
                    description=channel["description"],
                    logo=channel["logo"],
                    theme=channel["theme"],
                    language=channel["language"],
                    region=channel["region"],
                    position=channel["position"],
                    isAdult=channel["isAdult"],
                )
                db.add(channel_model)
                db.flush()  # Flush to generate the channel's id

            # Process each program associated with the channel
            for program in channel["programs"]:
                # Check if the program exists by its unique meo_program_id
                existing_program = (
                    db.query(EPGProgramModel)
                    .filter_by(meo_program_id=program["id"])
                    .first()
                )

                if existing_program:
                    # Update existing program fields
                    existing_program.start_date_time = program["start_date_time"]
                    existing_program.end_date_time = program["end_date_time"]
                    existing_program.name = program["name"]
                    existing_program.description = program["description"]
                    existing_program.imgM = program["imgM"]
                    existing_program.imgL = program["imgL"]
                    existing_program.imgXL = program["imgXL"]
                    existing_program.series_id = program["series_id"]
                    existing_program.channel_id = (
                        channel_model.id
                    )  # Ensure correct channel linkage
                else:
                    # Create a new program record
                    new_program = EPGProgramModel(
                        meo_program_id=program["id"],
                        channel_id=channel_model.id,
                        start_date_time=program["start_date_time"],
                        end_date_time=program["end_date_time"],
                        name=program["name"],
                        description=program["description"],
                        imgM=program["imgM"],
                        imgL=program["imgL"],
                        imgXL=program["imgXL"],
                        series_id=program["series_id"],
                    )
                    db.add(new_program)

        # Commit all changes at the end
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
