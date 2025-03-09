from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from utils.db import Base  # Import Base from db.py instead of creating a new one


class EPGChannelModel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    meo_id = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String)
    logo = Column(String)
    theme = Column(String)
    language = Column(String)
    region = Column(String)
    position = Column(Integer)
    isAdult = Column(Boolean)
    programs = relationship("EPGProgramModel", back_populates="channel")


class EPGProgramModel(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    meo_program_id = Column(String, unique=True, index=True)
    start_date_time = Column(DateTime)
    end_date_time = Column(DateTime)
    name = Column(String)
    description = Column(String)
    imgM = Column(String)
    imgL = Column(String)
    imgXL = Column(String)
    series_id = Column(String)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    channel = relationship("EPGChannelModel", back_populates="programs")
