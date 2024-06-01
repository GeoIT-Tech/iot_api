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
        
class Personals(BaseModel):
    
    fullname: Optional[str] = None
    pronounce: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    DOB: Optional[date] = None
    mail_address: Optional[str] = None
    phone_no: Optional[str] = None
    
    class Config:
        orm_mode = True

class PAEduInfo(BaseModel):

    institute_name: Optional[str] = None
    degree: Optional[str] = None
    specialization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class PAWorkInfo(BaseModel):

    designation: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    roles_responsibilities: Optional[str] = None

    class Config:
        orm_mode = True

class PAProject(BaseModel):

    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

    class Config:
        orm_mode = True

class SocialLinks(BaseModel):

    facebook: Optional[str] = None
    instagram: Optional[str] = None
    youtube: Optional[str] = None
    twitter: Optional[str] = None
    linkedin: Optional[str] = None
    threads: Optional[str] = None
    discord: Optional[str] = None

    class Config:
        orm_mode = True

class Skils(BaseModel):

    skills: List[str]

    class Config:
        orm_mode = True
                
# class InstituteType(str, Enum):
    
#     PRIMARY_SCHOOL='Primary School'
#     HIGHER_SCHOOL='Higher School'
#     COLLEGE='College'
#     UNIVERSITY='University'
#     ONLINE_UNIVERSITY='Online University'
#     PRIVATE_INSTITUTE='Private Institute'
#     RESEARCH_INSTITUTE='Research Institute'
#     LIBRARIES_AND_MUSEUMS='Libraries and Museums'
#     MILITARY_INSTITUTIONS='Military Institutions'
#     CULTURAL_INSTITUTIONS='Cultural Institutions'
  
class Institutes(BaseModel):
    
    fullname: Optional[str] = None
    i_type: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone_no: Optional[str] = None
    mail_address: Optional[str] = None
    established_year: Optional[int] = None
    ranking: Optional[str] = None
    recognised_by: Optional[str] = None
    strength: Optional[int] = None
    academic_facilities: Optional[str] = None
    course_url: Optional[str] = None
    admission_url: Optional[str] = None
    
    class Config:
        orm_mode = True

# class OrganizationType(str, Enum):

#     CORPORATE='Corporate'
#     GOVERNMENT_AGENCIES='Government Agencies'
#     NON_PROFIT_ORGANIZATION='Non-Profit Organization'
#     STARTUPS='Startups'
#     MSME='Micro, Small and Medium Enterprises'
#     MEDIA_AND_ENTERTAINMENT='Media and Entertainment'
#     CREATOR_PAGES='Creator Page'

class Organizations(BaseModel):
    
    fullname: Optional[str] = None
    o_type: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    phone_no: Optional[str] = None
    mail_address: Optional[str] = None
    company_size: Optional[str] = None
    head_quaters: Optional[str] = None
    established_year: Optional[int] = None

    class Config:
        orm_mode = True

#it's repeated        
# class UserReport(BaseModel):
    
#     user_uuid: UUID
    
#     class Config:
#         orm_mode =  True