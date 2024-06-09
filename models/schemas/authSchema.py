from pydantic import BaseModel
from typing import Optional

class RegisterUser(BaseModel):
    
    name: str
    email: str
    password: str
    
    class Config:
        orm_mode = True

class ResetPassword(BaseModel):
    
    password: str
    confirm_password: str

    class Config:
        orm_mode = True