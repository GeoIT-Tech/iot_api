from resources.utils import otp_code, call_log, get_logger, create_access_token, create_refresh_token, send_verification_email, send_forgetpassword_email
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer
from configs import BaseConfig, Configuration
from botocore.signers import CloudFrontSigner
from datetime import datetime, timedelta
from models.schemas import userSchema
from sqlalchemy.orm import Session
from models import models, get_db
from jose import jwt, JWTError
from typing import Optional
from sqlalchemy import or_ , and_
from uuid import UUID
import boto3
import datetime
import random
import string

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.post('/resend_verification_OTP')
def ResendOTP(request: Request, email: str, db: Session = Depends(get_db)):
    if email:
        db_user = db.query(models.User).filter(models.User.email == email).first()
        if db_user:
            if db_user.is_active:
                raise HTTPException(status_code=400, detail='Your account is already verified')
            else:
                code = otp_code()
                expiration_time = datetime.datetime.utcnow()+timedelta(minutes=10)
                db_user.verification_code = {'code':code, 'expires_at':expiration_time.strftime('%y-%m-%d %H:%M:%S')}
                db.commit()
                email_response = send_verification_email(db_user.fullname, db_user.email, 'Verification Email', code)
                if email_response['status']:
                    call_log(logger, description='Verification Email with OTP sent to registered Email id', status_code=200, api=request.url.path, ip=request.client.host)
                    return db_user
                else:
                    call_log(logger, description=email_response['error']['message'], status_code=400, api=request.url.path, ip=request.client.host)
                    raise HTTPException(status_code=400,detail=email_response['error']['message'])
        else:
            raise HTTPException(status_code=400, detail='Your Email is not registered with us')
    
def generate_random_string(length):
   # letters_and_digits = string.ascii_letters + string.digits
   # return ''.join(random.choice(letters_and_digits) for _ in range(length))
    return ''.join(random.choice(string.digits) for _ in range(length))
            
@router.patch('/verification/{email}')
def UserVerification(request: Request, otp: int, email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        MID = db_user.fullname.replace(" ", "_").lower()
        while True:
            MID = f"{MID}{generate_random_string(3)}" 
            existing_user = db.query(models.User).filter(models.User.MID == MID).first()
            if not existing_user:
               break
         # Replace spaces with underscores MID.replace(" ", "_")
        
        code = int(db_user.verification_code['code'])
        if code == otp:
            db_user.MID=MID
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            date = datetime.datetime.strptime(db_user.verification_code['expires_at'], '%y-%m-%d %H:%M:%S')
            if not date <= datetime.datetime.utcnow():
                db_user.is_active = True
                # db_user.is_verified = True
                db.commit()
                
                access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_token_expires = timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"sub": str(db_user.uuid)}, expires_delta=access_token_expires)
                refresh_token = create_refresh_token(data={"sub": str(db_user.uuid)}, expires_delta=refresh_token_expires)
                call_log(logger, description='User Registered', user_uuid=db_user.uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': db_user}
            else:
                call_log(logger, description='Your OTP Expired', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Your OTP Expired')
        else:
            call_log(logger, description='Enter correct OTP', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
            raise HTTPException(status_code=400, detail='Enter correct OTP')
    else:
        call_log(logger, description='User does not exist',user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='User does not exist')
    
    
@router.post('/forgot_password')
def forget_password(request: Request, user_email: str, db: Session = Depends(get_db)):
    user_email = user_email.lower()
    db_user = db.query(models.User).filter(models.User.email == user_email).first()
    if not db_user:
        call_log(logger, description='Email id is not registered with us', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400, detail='Email id is not registered with us')
    code = otp_code()
    expiration_time = datetime.datetime.utcnow()+timedelta(minutes=10)
    email_response = send_forgetpassword_email(db_user.fullname, db_user.email, 'Reset Password Email', code)
    if email_response['status']:
        old_codes = db.query(models.ResetPasswordCode).filter(models.ResetPasswordCode.user_uuid == db_user.uuid).all()
        for old_code in old_codes:
            if not old_code.consumed:
                old_code.consumed = True
        db.commit()
        reset_pwd_data = models.ResetPasswordCode(user_uuid=db_user.uuid, verification_code = {'code':code, 'expires_at':expiration_time.strftime('%y-%m-%d %H:%M:%S')})
        db.add(reset_pwd_data)
        db.commit()
        call_log(logger, description='Reset Password mail sent to user email', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
        del(db_user.hashed_password)
        del(db_user.verification_code)
        return db_user
    else:
        call_log(logger, description=email_response['error']['message'], user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400, detail=email_response['error']['message'])


@router.post('/resend_forget_password_OTP')
def ResendOTP(request: Request, email: str, db: Session = Depends(get_db)):
    if email:
        db_user = db.query(models.User).filter(models.User.email == email).first()
        if db_user:
            db_code = db.query(models.ResetPasswordCode).filter(models.ResetPasswordCode.user_uuid == db_user.uuid, models.ResetPasswordCode.consumed == False).first()
            if db_code:
                code = otp_code()
                expiration_time = datetime.datetime.utcnow()+timedelta(minutes=10)
                db_code.verification_code = {'code':code, 'expires_at':expiration_time.strftime('%y-%m-%d %H:%M:%S')}
                db.commit()
                email_response = send_forgetpassword_email(db_user.fullname, db_user.email, 'Reset Password Email', code)
                if email_response['status']:
                    call_log(logger, description='Reset Password mail sent to user email', status_code=200, api=request.url.path, ip=request.client.host)
                    return db_user
                else:
                    call_log(logger, description=email_response['error']['message'], status_code=400, api=request.url.path, ip=request.client.host)
                    raise HTTPException(status_code=400,detail=email_response['error']['message'])
            else:  
                call_log(logger, description='Password is updated already using this reset password mail', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Password is updated already using this reset password mail')
        else:
            raise HTTPException(status_code=400, detail='Your Email is not registered with us')
    
    
@router.patch('/forget_password_verification/{email}')
def UserVerification(request: Request, otp: int, password_data: authSchema.ResetPassword, email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        db_code = db.query(models.ResetPasswordCode).filter(models.ResetPasswordCode.user_uuid == db_user.uuid, models.ResetPasswordCode.consumed == False).first()
        if db_code:
            code = int(db_code.verification_code['code'])
            if code == otp:
                date = datetime.datetime.strptime(db_code.verification_code['expires_at'], '%y-%m-%d %H:%M:%S')
                if not date <= datetime.datetime.utcnow():
                    # if db_user.verify_password(password_data.password):
                    #     exception_msg = 'The new password should be different from previous used password'
                    #     call_log(logger, description=exception_msg, user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                    #     raise HTTPException(status_code=400, detail=exception_msg)
                    # else:
                        if password_data.password == password_data.confirm_password:
                            db_user.hash_password(password_data.password)
                            db.commit()
                            db_code.consumed = True
                            db.commit()
                            call_log(logger, description='Password Updated successfully', user_uuid=db_user.uuid, status_code=200, api=request.url.path, ip=request.client.host)
                            return { 'detail' : 'Password Updated successfully' }
                        else:
                            exception_msg = 'Passwords does not match'
                            call_log(logger, description=exception_msg, user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                            raise HTTPException(status_code=400, detail=exception_msg)
                else:
                    call_log(logger, description='Your OTP Expired', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                    raise HTTPException(status_code=400, detail='Your OTP Expired')
            else:
                call_log(logger, description='Enter correct OTP', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Enter correct OTP')
        else:  
            call_log(logger, description='Password is updated already using this reset password mail', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
            raise HTTPException(status_code=400, detail='Password is updated already using this reset password mail')
    else:
        call_log(logger, description='User does not exist',user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='User does not exist')
    

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
                db_personal = db.query(models.Personal).filter(models.Personal.user_uuid == users.uuid, models.Personal.is_deleted == False).all()
                db_organization = db.query(models.Organization).filter(models.Organization.user_uuid == users.uuid, models.Organization.is_deleted == False).all()
                db_institute = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == users.uuid, models.EduInstitute.is_deleted == False).all()
                if db_personal:
                    users.profile = db_personal
                elif db_organization:
                    users.profile = db_organization
                elif db_institute:
                    users.profile = db_institute
                else:
                    users.profile = []
                db_settings = db.query(models.Setting).filter(models.Setting.user_uuid == users.uuid).all()
                users.settings = db_settings
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
                db_personal = db.query(models.Personal).filter(models.Personal.user_uuid == request_uuid, models.Personal.is_deleted == False).first()
                db_organization = db.query(models.Organization).filter(models.Organization.user_uuid == request_uuid, models.Organization.is_deleted == False).first()
                db_institute = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == request_uuid, models.EduInstitute.is_deleted == False).first()
                if db_personal:
                    db_personal.is_deleted = True
                    db.commit()
                    call_log(logger, description='User Deleted Temporarily', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'User Deleted Temporarily' }
                elif db_organization:
                    db_organization.is_deleted = True
                    db.commit()
                    call_log(logger, description='User Deleted Temporarily', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'User Deleted Temporarily' }
                elif db_institute:
                    db_institute.is_deleted = True
                    db.commit()
                    call_log(logger, description='User Deleted Temporarily', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'User Deleted Temporarily' }
                else:
                    raise HTTPException(status_code=400, detail='Account not Deleted')
            else:
                call_log(logger, description='Incorrect Password', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Incorrect Password')     
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

