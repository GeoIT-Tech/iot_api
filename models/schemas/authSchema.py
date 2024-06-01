from pydantic import BaseModel
from typing import Optional

class RegisterUser(BaseModel):
    
    fullname: str
    email: str
    password: str
    
    class Config:
        orm_mode = True
        
        
class RegisterMobileUser(BaseModel):
    
    fullname: str
    dial_code: Optional[str] = None
    mobile: str
    password: str
    
    class Config:
        orm_mode = True

class OAuthUser(BaseModel):
    
    full_name: str
    email: str
    signup_type : str
    
    
    class Config:
        orm_mode = True