from typing import Optional, List
from pydantic import BaseModel
from enum import Enum
from uuid import UUID

class MediaType(str, Enum):
    
    IMAGE='Image'
    VIDEO='Video'
    TEXT='Text'
    
class AddPost(BaseModel):
    
    caption: str
    image_media: Optional[str] = None
    video_media: Optional[str] = None
    tags: Optional[List[UUID]] = None
    hashtag: Optional[List[str]] = None

    class Config:
        orm_mode =  True

# Not required         
class UpdatePost(BaseModel):
    
    caption: str
    tags: Optional[List[UUID]] = None

    class Config:
        orm_mode =  True

# Not required        
class Hashtag(BaseModel):
    
    caption: str
    # post_hashtags: str
    # certificate_hashtags: str
    # ebattle_hashtags: str
    
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

#it's repeated from reportschema       
class PostReport(BaseModel):
    
    post_uuid: UUID
    
    class Config:
        orm_mode =  True

#it's repeated from reportschema           
class CommentReport(BaseModel):
    
    comment_uuid: UUID
    
    class Config:
        orm_mode =  True
        
# class DontRecomment(BaseModel):
    
#     post_uuid: UUID
