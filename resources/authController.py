import random
import string
import bcrypt
from resources.utils import email_validator, send_verification_email, send_forgetpassword_email, otp_code, create_access_token, create_refresh_token, call_log, get_logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, HTTPException, Depends, Request
from configs.base_config import BaseConfig
from datetime import datetime, timedelta
from sqlalchemy import or_
from models.schemas import authSchema
from sqlalchemy.orm import Session
from models import models, get_db
from jose import jwt, JWTError
import datetime
import secrets

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post('/sign_up')
def PostUser(request: Request, user: authSchema.RegisterUser, db: Session = Depends(get_db)):
    
    # Convert data to lower case
    user.email = user.email.lower()
     
    db_email = db.query(models.User).filter(models.User.email == user.email, models.User.is_active == True).first()
    if db_email:
        call_log(logger, description='Email ID already registered', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='Email ID already registered') 
    else:
        db.query(models.User).filter(models.User.email == user.email).delete()
        db.commit()
    if len(user.password) < 8:
        call_log(logger, description='Your password needs to be atleast 8 characaters long', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='Your password needs to be atleast 8 characaters long')
    if not email_validator(user.email):
        call_log(logger, description='Please enter a valid E-Mail', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='Please enter a valid E-Mail')
    code = otp_code()
    expiration_time = datetime.utcnow()+timedelta(minutes=10)
    db_user= models.User(email = user.email, name = user.name, verification_code = {'code':code, 'expires_at':expiration_time.strftime('%y-%m-%d %H:%M:%S')})
    db_user.hash_password(user.password)
    db_user.signup_type = "Email"
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": str(db_user.uuid)}, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data={"sub": str(db_user.uuid)}, expires_delta=refresh_token_expires)
    # sender_email, subject, template, user_uuid
    email_response = send_verification_email(user.name, user.email, 'Verification Email', code)
    if email_response['status']:
        del(db_user.verification_code)
        del(db_user.hashed_password)
        call_log(logger, description='Verification Email with OTP sent to registered Email id', status_code=200, api=request.url.path, ip=request.client.host)
        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': db_user}
    else:
        db.query(models.User).filter(models.User.uuid == db_user.uuid).delete()
        db.commit()
        call_log(logger, description=email_response['error']['message'], status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail=email_response['error']['message'])
    
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
                email_response = send_verification_email(db_user.name, db_user.email, 'Verification Email', code)
                if email_response['status']:
                    call_log(logger, description='Verification Email with OTP sent to registered Email id', status_code=200, api=request.url.path, ip=request.client.host)
                    return db_user
                else:
                    call_log(logger, description=email_response['error']['message'], status_code=400, api=request.url.path, ip=request.client.host)
                    raise HTTPException(status_code=400,detail=email_response['error']['message'])
        else:
            raise HTTPException(status_code=400, detail='Your Email is not registered with us')

            
@router.patch('/verification/{email}')
def UserVerification(request: Request, otp: int, email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        code = int(db_user.verification_code['code'])
        if code == otp:
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
    email_response = send_forgetpassword_email(db_user.name, db_user.email, 'Reset Password Email', code)
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
                email_response = send_forgetpassword_email(db_user.name, db_user.email, 'Reset Password Email', code)
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

@router.post('/login')
def Login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.lower()
    password = form_data.password
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        if db_user.verify_password(password):
            if db_user.is_active:
                access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_token_expires = timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"sub": str(db_user.uuid)}, expires_delta=access_token_expires)
                refresh_token = create_refresh_token(data={"sub": str(db_user.uuid)}, expires_delta=refresh_token_expires)
                call_log(logger, description='User logged in', user_uuid=db_user.uuid, status_code=200, api=request.url.path, ip=request.client.host)
                del(db_user.hashed_password)
                del(db_user.verification_code)
                return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': db_user }
            else:
                call_log(logger, description='User is not verified', status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='User is not verified')
        else:
            call_log(logger, description='Password Incorrect', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
            raise HTTPException(status_code=400, detail='Password Incorrect')
    else:
        call_log(logger, description='Your Email is not registered with us', status_code=401, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=401, detail='Your Email is not registered with us')

@router.post('/logout')
def Logout(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_create = models.Setting(user_uuid=user_uuid, logout_activity=datetime.utcnow())
            db.add(db_create)
            db.commit()
            call_log(logger, description='logout Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail' : 'logout Updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')