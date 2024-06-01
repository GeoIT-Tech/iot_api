from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from uuid import UUID

class Setting(str, Enum):
    
    EVERYONE='Everyone'
    NO_ONE='No One'
    PROFILE_YOU_BOOST='Profile You Boost'

# class PrivacySetting(BaseModel):
    
#     is_private: bool = False
    
#     class Config:
#         orm_mode = True

class ProtectAccount(BaseModel):
    
    is_protected: bool = False
    
    class Config:
        orm_mode = True
        
class BlockAccount(BaseModel):
    
    block_user_uuid: UUID
    is_blocked: bool = False
    
    class Config:
        orm_mode = True
        
class ChangePassword(BaseModel):
    
    current_password: str
    password: str
    confirm_password: str
    
    class Config:
        orm_mode = True
        
class DocumentType(str, Enum):
    
    ARTICLE_OF_INCORPORATE='Articles of Incorporate'
    DRIVER_LICENSE='Driver\'s License'
    NATIONAL_IDENTIFICATION_CARD='National Identification Card'
    PASSPORT='Passport'
    RECENT_UTILITY_BILL='Recent Utility Bill'
    TAX_FILLING='Tax Filing'

class DocumentCategory(str, Enum):

    INSTITUTE='Institute'
    BUSINESS_ORGANIZATION='Business/Organization'
    STUDENT='Student'
    EDUCATOR='Educator'
    MEDIA_NEWS='Media/News'
    ENTERTAINMENT_EDUTAINMENT='Entertainment/Edutainment'
    GOVERNMENT_POLITICS='Government/Politics'
    CREATOR_BLOGGER_INFLUENCER='Creator/Blogger/Influencer'
    SPORTS='Sports'
    MUSIC='Music'
    OTHERS='Others'

class VerifyStatus(str, Enum):

    NOT_VERIFIED='Not_Verified'
    SUMBITTED='Submitted'
    PENDING='Pending'
    VERIFIED='Verified'
    REJECTED='Rejected'
    WAITINGLIST='Waitinglist'

class DocumentDetails(BaseModel):
    
    fullname: str
    menem_id: str
    country: str
    d_category: str 
    d_type: str 
    
    class Config:
        orm_mode = True
              
# class VerifyInfo(BaseModel):
    
#     password: str
#     email: Optional[str]
#     mobile: Optional[str]
    
#     class Config:
#         orm_mode = True

class PersonalEditInfo(BaseModel):
    
    fullname: Optional[str]
    pronounce: Optional[str]
    DOB: Optional[str]
    location: Optional[str]
    title: Optional[str]
    mail_address: Optional[str]
    phone_no: Optional[str]

    class Config:
        orm_mode = True

class OrgEditInfo(BaseModel):
    
    fullname: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    website: Optional[str]
    mail_address: Optional[str]
    phone_no: Optional[str]
    company_size: Optional[str] 
    head_quaters: Optional[str] 
    established_year: Optional[int]

    class Config:
        orm_mode = True

class InstituteEditInfo(BaseModel):
    
    fullname: Optional[str]
    location: Optional[str]
    website: Optional[str]
    mail_address: Optional[str]
    phone_no: Optional[str]
    established_year: Optional[int]
    NIRF_ranking: Optional[str]
    recognised_by: Optional[str]
    strength: Optional[int]
    student_placed: Optional[int]
    academic_facilities: Optional[str]
    entrance_eligibility: Optional[str]

    class Config:
        orm_mode = True

class PartnerAndServices(BaseModel):
    organization_name: Optional[str]
    location: Optional[str]
    website: Optional[str]
    services: Optional[str]
    email: Optional[str]
    mobile: Optional[str]

    class Config:
        orm_mode = True

class MobileApp(BaseModel):
    
    is_maintenance: bool = False
    mobile_app_version = str

    class Config:
        orm_mode = True
    