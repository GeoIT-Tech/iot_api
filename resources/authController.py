import random
import string
import bcrypt
from resources.utils import email_validator, send_verification_email, otp_code, create_access_token, create_refresh_token, call_log, get_logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, HTTPException, Depends, Request
from configs.base_config import BaseConfig
from datetime import datetime, timedelta
from sqlalchemy import or_
from models.schemas import authSchema
from sqlalchemy.orm import Session
from models import models, get_db
from jose import jwt, JWTError
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
    db_user= models.User(email = user.email, fullname = user.fullname, verification_code = {'code':code, 'expires_at':expiration_time.strftime('%y-%m-%d %H:%M:%S')})
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
    email_response = send_verification_email(user.fullname, user.email, 'Verification Email', code)
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
    

@router.post('/mobile_sign_up')
def PostUser(request: Request, user: authSchema.RegisterMobileUser, db: Session = Depends(get_db)):     
    db_mobile = db.query(models.User).filter(models.User.mobile == user.mobile).first()
    if db_mobile:
        call_log(logger, description='Mobile Number already registered', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='Mobile Number already registered') 
    if len(user.password) < 8:
        call_log(logger, description='Your password needs to be atleast 8 characaters long', status_code=400, api=request.url.path, ip=request.client.host)
        raise HTTPException(status_code=400,detail='Your password needs to be atleast 8 characaters long')
    db_user= models.User(mobile = user.mobile, fullname = user.fullname, dial_code = user.dial_code)
    db_user.hash_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return { 'detail' : 'User Created'}
    

@router.post('/login')
def Login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.lower()
    MID = form_data.username.lower()
    password = form_data.password
    db_user = db.query(models.User).filter(or_(models.User.email == email, models.User.MID == MID)).first()
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
                db_personal = db.query(models.Personal).filter(models.Personal.user_uuid == db_user.uuid).first()
                if db_personal:
                    db_user.personal = db_personal
                db_organization = db.query(models.Organization).filter(models.Organization.user_uuid == db_user.uuid).first()
                if db_organization:
                    db_user.organization = db_organization
                db_institute = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == db_user.uuid).first()
                if db_institute:
                    db_user.institute = db_institute
                db_settings = db.query(models.Setting.private_setting).filter(models.Setting.user_uuid == db_user.uuid).first()
                if db_settings:
                    db_user.setting = db_settings
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

def generate_random_string(length):
   # letters_and_digits = string.ascii_letters + string.digits
   # return ''.join(random.choice(letters_and_digits) for _ in range(length))
    return ''.join(random.choice(string.digits) for _ in range(length))

@router.post('/oauth_signup')
def OAuthSignup(request: Request, user: authSchema.OAuthUser, db: Session = Depends(get_db)): 
    db_email = db.query(models.User).filter(models.User.email == user.email,models.User.is_active==True).first()
     # Generate a random password
    # password = secrets.token_urlsafe(12)  # Adjust length as needed
     # Hash the password
    MID = user.full_name.replace(" ", "_").lower()
    while True:
        MID = f"{MID}{generate_random_string(3)}" 
        existing_user = db.query(models.User).filter(models.User.MID == MID).first()
        if not existing_user:
            break
    # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    if db_email:
        access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(db_email.uuid)}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": str(db_email.uuid)}, expires_delta=refresh_token_expires)
        call_log(logger, description='User logged in', user_uuid=db_email.uuid, status_code=200, api=request.url.path, ip=request.client.host)
        del(db_email.hashed_password)
        del(db_email.verification_code)
        db_personal = db.query(models.Personal).filter(models.Personal.user_uuid == db_email.uuid).first()
        if db_personal:
            db_email.personal = db_personal
        db_organization = db.query(models.Organization).filter(models.Organization.user_uuid == db_email.uuid).first()
        if db_organization:
            db_email.organization = db_organization
        db_institute = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == db_email.uuid).first()
        if db_institute:
            db_email.institute = db_institute
        db_settings = db.query(models.Setting.private_setting).filter(models.Setting.user_uuid == db_email.uuid).first()
        if db_settings:
            db_email.setting = db_settings
        return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': db_email } 
    else:
        db_emailCheck = db.query(models.User).filter(models.User.email == user.email,models.User.is_active==False).first()
        if db_emailCheck:
            db.query(models.User).filter(models.User.email == user.email).delete()
            db.commit()
        db_user= models.User(email = user.email, fullname = user.full_name, signup_type = user.signup_type)
        db_user.MID = MID
        db_user.hash_password("OA1234%menem@#")
        db_user.is_active = True
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        access_token_expires = timedelta(minutes=BaseConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=BaseConfig.REFRESH_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": str(db_user.uuid)}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": str(db_user.uuid)}, expires_delta=refresh_token_expires)
    call_log(logger, description='OAuth Verified Successfully', status_code=200, api=request.url.path, ip=request.client.host)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': db_user}


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