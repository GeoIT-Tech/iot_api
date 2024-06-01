from typing import List, Optional
from pydantic import BaseModel
from datetime import date
from uuid import UUID

# class CoreUser(BaseModel):
    
#     admin_management_uuid: Optional[List[UUID]] = None
#     faculty_uuid: Optional[List[UUID]] = None
#     alumini_uuid: Optional[List[UUID]] = None
    
#     class Config:
#         orm_mode =  True
        
class AddProgram(BaseModel):
    
    detail: Optional[str]
    course_year: Optional[str]
    course_mode: Optional[str]
    no_of_seat: Optional[int]
    
    class Config:
        orm_mode =  True
    
        
class Admission(BaseModel):
    
    detail: Optional[str] 
    start_date: Optional[date] 
    end_date: Optional[date] 
    course_title: Optional[str] 
    academic_year: Optional[str] 
    admission_url: Optional[str] 
    
    class Config:
        orm_mode =  True

class Placement(BaseModel):
    
    description: str
    placement_partner_id: Optional[List[UUID]] = None
    
    class Config:
        orm_mode =  True