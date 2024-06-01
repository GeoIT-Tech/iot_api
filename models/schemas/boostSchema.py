from pydantic import BaseModel
from enum import Enum
from uuid import UUID

class BoostStatus(str, Enum):
    
    TRUE ='Accepted'
    FALSE ='Rejected'
    PENDING ='Pending'

class BoostVerifySetting(str, Enum):
    
    EVERYONE='Everyone'
    NO_ONE='No One'
    PROFILE_YOU_BOOST='Profile You Boost'

class SendRequest(BaseModel):
    
    receiver_uuid: UUID

    class Config:
        orm_mode =  True