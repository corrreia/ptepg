from typing import TypedDict, List


# Define Program type
class Program(TypedDict):
    id: str  # uniqueId field
    start_date_time: str
    end_date_time: str
    name: str
    description: str
    imgM: str
    imgL: str
    imgXL: str
    series_id: str


# Define Channel type
class Channel(TypedDict):
    id: str
    name: str
    meo_id: str  # sigla field
    logo: str
    isAdult: bool
    programs: List[Program]
