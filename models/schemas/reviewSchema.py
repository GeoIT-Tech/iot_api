from pydantic import BaseModel
from typing import Optional #,List
from uuid import UUID

class Reviews(BaseModel):
    
    reviewer_uuid: Optional[UUID] = None
    review: Optional[str] = None
    rating: Optional[float] = None
    
    class Config:
        orm_mode =  True

# class Reviews(BaseModel):
    
#     reviewer_uuid: Optional[UUID] = None
#     review: Optional[str] = None
#     rating: Optional[float] = None
#     hashtags: Optional[List[str]] = None

#     class Config:
#         orm_mode =  True

class Reply(BaseModel):
    
    reply: str
    
    class Config:
        orm_mode =  True

# class Reply(BaseModel):
    
#     reply: str
#     hashtags: Optional[List[str]] = None
    
#     class Config:
#         orm_mode =  True