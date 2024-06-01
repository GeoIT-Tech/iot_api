from typing import List, Optional
from pydantic import BaseModel
from datetime import date
# import datetime 
from uuid import UUID

class AddEBattle(BaseModel):
  
    category: Optional[str] = None
    cover_image_url: Optional[str] = None
    title: str
    timezone: str
    description: str
    is_online_battle: Optional[bool] = None
    activity_url: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    guests: Optional[List[UUID]] = None
    collab_acc: Optional[List[UUID]] = None
    
    class Config:
        orm_mode = True
        
class Like(BaseModel):
    
    is_liked: bool = False

    class Config:
        orm_mode = True

#this class is not needed   
class Hashtag(BaseModel):
    
    caption: str
    
    class Config:
        orm_mode =  True
    
class DontRecomment(BaseModel):
    
    ebattle_uuid: List[UUID]
    
    class Config:
        orm_mode =  True
        
class JoinEBattle(BaseModel):
    
    e_battle_uuid: UUID
    caption: str
    email: str
    mobile: str 
    
    class Config:
        orm_mode = True
