from pydantic import BaseModel


class EpgProgramSchema(BaseModel):
    id: str
    start_date_time: str
    end_date_time: str
    name: str
    description: str
    imgM: str
    imgL: str
    imgXL: str
    series_id: str


class EpgChannelSchema(BaseModel):
    id: str
    meo_id: str
    name: str
    description: str
    logo: str
    theme: str
    language: str
    region: str
    position: int
    isAdult: bool
    programs: list[EpgProgramSchema]
