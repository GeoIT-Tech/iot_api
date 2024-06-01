from pydantic import BaseModel
from typing import Optional
from datetime import date
from typing import List
from uuid import UUID
from enum import Enum

class ResetPassword(BaseModel):
    
    password: str
    confirm_password: str

    class Config:
        orm_mode = True
        
class Category(str, Enum):
    
    PERSONAL='Personal'
    INSTITUTION='Institution'
    ORGANIZATION='Organization'
        
class UserUpdate(BaseModel):
    
    menem_id: str
    
    class Config:
        orm_mode = True
        
class AboutTagline(BaseModel):
    
    about: Optional[str] = None
    tagline: Optional[str] = None
    
    class Config:
        orm_mode = True
        
class UserPronounce(str, Enum):
    
    HE_HIM='He/Him'
    SHE_HER='She/Her'
    THEY_THEM='They/Them'
    PREFER_NOT_TO_SAY = 'Prefer not to say'


