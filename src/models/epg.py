from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class EPGChannel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    meo_id = Column(String, unique=True, index=True)  # Added unique constraint
    name = Column(String)
    description = Column(String)
    logo = Column(String)
    theme = Column(String)
    language = Column(String)
    region = Column(String)
    position = Column(Integer)
    isAdult = Column(Boolean)
    programs = relationship("EPGProgram", back_populates="channel")


class EPGProgram(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    meo_program_id = Column(
        String, unique=True, index=True
    )  # Added to store uniqueId from API
    start_date_time = Column(String)
    end_date_time = Column(String)
    name = Column(String)
    description = Column(String)
    imgM = Column(String)
    imgL = Column(String)
    imgXL = Column(String)
    series_id = Column(String)
    channel_id = Column(Integer, ForeignKey("channels.id"))
    channel = relationship("EPGChannel", back_populates="programs")
