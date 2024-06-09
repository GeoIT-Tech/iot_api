from resources.utils import otp_code, call_log, get_logger, create_access_token, create_refresh_token, send_verification_email, send_forgetpassword_email
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer
from configs import BaseConfig, Configuration
from datetime import datetime, timedelta
# from models.schemas import userSchema
from sqlalchemy.orm import Session
from models import models, get_db
from jose import jwt, JWTError
from typing import Optional
from sqlalchemy import or_ , and_
from uuid import UUID
import datetime
import random
import string

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.get('/get_all_users')
def GetAllUsers(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True ).first()
        if db_user:
            db_users = db.query(models.User).filter(models.User.is_deleted == False,models.User.is_active == True).order_by(models.User.created_at.desc()).all()
            for users in db_users:
                del(users.hashed_password)
                del(users.verification_code)
            return { 'data' : db_users }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
       
@router.patch('/delete_user')
def DeleteUser( request: Request, request_uuid: UUID, reason: str, comment: str, current_password:str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == request_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if db_user.verify_password(current_password):
                db_user.is_deleted = True
                db_user.delete_reason = reason
                db_user.delete_comment = comment
                db.commit()
            else:
                call_log(logger, description='Incorrect Password', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Incorrect Password')     
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

