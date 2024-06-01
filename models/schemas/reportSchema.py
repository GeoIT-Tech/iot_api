from pydantic import BaseModel
from typing import Optional
from enum import Enum
from uuid import UUID


# class ReportReasons(str, Enum):
    
#     Inappropriate_Content = 'Inappropriate Content'
#     Harassment_Bullying =  'Harassment or Bullying'
#     Impersonation = 'Impersonation'
#     Spam_Fake_Accounts = 'Spam or Fake_Accounts'
#     Privacy_Concerns = 'Privacy Concerns'
#     Violence_Threats = 'Violence Threats'
#     Intellectual_Property_Violations = 'Intellectual Property Violations'
#     Misinformation_Fake_News = 'Misinformation Fake News'
#     Underage_Users='Underage Users'
#     Other_Violations = 'Other Violations'

# class ReportMediaType(str,Enum):

#     Profile='PROFILE'
#     Post='POST'
#     Certificate='CERTIFICATE'
#     Ebattle='EBATTLE'
#     Comment='COMMENT'
#     Review='REVIEW'

class Report_UUID(BaseModel):

    reported_uuid: UUID
    report_reason: str
    media_type: str
    media_uuid: UUID 

# class ProfileReports(BaseModel):

#     profile_uuid: UUID = None
#     reported_uuid : Optional[UUID] = None

#     class Config:
#         orm_mode =  True

# class ReportPostReasons(str, Enum):
    
#     Inappropriate_Content = 'Inappropriate Content'
#     Harassment_Bullying =  'Harassment or Bullying'
#     Impersonation = 'Impersonation'
#     Spam_Fake_Accounts = 'Spam or Fake_Accounts'
#     Privacy_Concerns = 'Privacy Concerns'
#     Violence_Threats = 'Violence Threats'
#     Intellectual_Property_Violations = 'Intellectual Property Violations'
#     Misinformation_Fake_News = 'Misinformation Fake News'
#     Underage_Users='Underage Users'
#     Other_Violations = 'Other Violations'

# class Report_UUID(BaseModel):

#     reported_uuid: UUID = None
#     media_uuid: UUID = None
    # post_uuid: Optional[UUID] = None
    # profile_uuid: Optional[UUID] = None
    # certificate_uuid: Optional[UUID] = None
    # ebattle_uuid: Optional[UUID] = None
    # comment_uuid: Optional[UUID] = None
    # review_uuid: Optional[UUID] = None
    
    # class Config:
    #     orm_mode =  True

# class PostReports(BaseModel):
    
#     post_uuid: Optional[UUID] = None
#     reported_uuid : Optional[UUID] = None

#     class Config:
#         orm_mode =  True

# class CertificateReports(BaseModel):

#     certificate_uuid: Optional[UUID] = None
#     reported_uuid : Optional[UUID] = None

#     class Config:
#         orm_mode =  True

# class EBattleReports(BaseModel):

#     ebattle_uuid: Optional[UUID] = None
#     reported_uuid : Optional[UUID] = None

#     class Config:
#         orm_mode =  True

# class CommentReports(BaseModel):

#     comment_uuid: Optional[UUID] = None
#     reported_uuid : Optional[UUID] = None
    
#     class Config:
#         orm_mode =  True

# class ReviewReports(BaseModel):

#     review_uuid: Optional[UUID] = None
#     reported_uuid : Optional[UUID] = None
    
#     class Config:
#         orm_mode =  True