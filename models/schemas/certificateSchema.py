from typing import Optional, List
from pydantic import BaseModel
from datetime import date
# import datetime 
from uuid import UUID

class Certificate(BaseModel):
    
    name: Optional[str] = None
    link: Optional[str] = None
    is_paid_course: Optional[bool] = None
    is_online_course: Optional[bool] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    
    class Config:
        orm_mode =  True
      
class AddComment(BaseModel):
    
    comment_detail: str

    class Config:
        orm_mode = True

# class AddComment(BaseModel):
    
#     comment_detail: str
#     hashtag: Optional[List[str]] = None
#     class Config:
#         orm_mode = True

class Like(BaseModel):

    is_liked: bool = False

    class Config:
        orm_mode = True

# Hashtag Scheme is not needed    
class Hashtag(BaseModel):
    
    caption: str
    
    class Config:
        orm_mode =  True
    
class DontRecomment(BaseModel):
    
    certificate_uuid: List[UUID]
    
    class Config:
        orm_mode =  True
