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

session = boto3.Session(
    aws_access_key_id=Configuration.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Configuration.AWS_SECRET_ACCESS_KEY,
    region_name=Configuration.AWS_REGION
)
s3 = session.client('s3')
verification_bucket_name = Configuration.AWS_VERIFICATION_BUCKET_NAME

cloudfront_url = 'https://d1qg0t2v350aib.cloudfront.net/'
# key_id = 'E1DT9MG04OE7QN'

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
def UserVerification(request: Request, otp: int, password_data: userSchema.ResetPassword, email: str, db: Session = Depends(get_db)):
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
    
    
# @router.patch('/update_ID')
# def UpdateID(request: Request, update: userSchema.UserUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_MID = db.query(models.User).filter(models.User.MID == update.menem_id).first()
#             if not db_MID:
#                 db_user.MID = update.menem_id
#                 db.commit()
#                 call_log(logger, description='MeNeM ID Created', user_uuid=user_uuid, status_code=400, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'MeNeM ID Created' }
#             else:
#                 raise HTTPException(status_code=400, detail='MeNeM ID already exist.Try another ID')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.get("/update_ID/{full_name}")
async def UpdateID(request: Request, full_name: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Convert full name to lowercase
    MID = full_name.lower()
    # Replace spaces with underscores
    MID = MID.replace(" ", "_")
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_user.MID(full_name.str(MID))
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
        return {"details": MID}
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/update_ID')
# def UpdateID(request: Request, update: userSchema.UserUpdate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_MID = db.query(models.User).filter(models.User.MID == update.menem_id).first()
#             if not db_MID:
#                 db_user.MID = update.menem_id
#                 db.commit()
#                 call_log(logger, description='MeNeM ID Created', user_uuid=user_uuid, status_code=400, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'MeNeM ID Created' }
#             else:
#                 raise HTTPException(status_code=400, detail='MeNeM ID already exist.Try another ID')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.patch('/update_profile')
# def UpdateProfile(request: Request, category: userSchema.Category, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_user.category = category
#             db.commit()
#             call_log(logger, description='User Profile Updated', user_uuid=user_uuid, status_code=400, api=request.url.path, ip=request.client.host)
#             return { 'detail' : 'User Profile Updated' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.patch('/update_about_tagline')
def UpdateABoutTagline(request: Request, update: userSchema.AboutTagline, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid  
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_user.about = update.about
            db_user.tagline = update.tagline
            db.commit()
            call_log(logger, description='About or Tagline Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail' : 'About or Tagline Updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post('/personal_account')
def PersonalAccount(request: Request, create: userSchema.Personals, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_user.category = 'Personal'
            db_user.is_protected = False
            if create.fullname:
                db_user.fullname = create.fullname
            db.commit()
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if not db_setting:
                db_create = models.Setting(user_uuid=user_uuid, private_setting="Everyone", blocked_account = [])
                db.add(db_create)
                db.commit()
            db_check = db.query(models.Personal).filter(models.Personal.user_uuid == user_uuid).first()
            if not db_check:
                db_personal = models.Personal(user_uuid=user_uuid)
                db.add(db_personal)
                db.commit()
                call_log(logger, description='Personal profile created', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Personal profile created'}
            else:
                if create.location:
                    db_check.location= create.location
                if create.DOB:
                    db_check.DOB= create.DOB
                if create.pronounce:
                    db_check.pronounce= create.pronounce
                if create.title:
                    db_check.title= create.title
                if create.mail_address and create.phone_no:
                    db_check.contact_us = {'mail_address': create.mail_address, 'phone_no': create.phone_no}
                db.commit()
                return { 'detail' : 'Personal profile updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post('/pa_edu_info')
def PAEduInfo(request: Request, create: userSchema.PAEduInfo, edu_uuid: Optional[UUID] = None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == 'Personal', models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if not edu_uuid:
                db_edu = models.PAEducationInfo(user_uuid=user_uuid, institute_name=create.institute_name, degree=create.degree, specialization=create.specialization, start_date=create.start_date, end_date=create.end_date, description=create.description)
                db.add(db_edu)
                db.commit()
                call_log(logger, description='Education Info Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Education Info Added'}
            else:
                db_edu_info = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.user_uuid == user_uuid, models.PAEducationInfo.uuid == edu_uuid).first()
                if db_edu_info:
                    db_edu_info.institute_name = create.institute_name
                    db_edu_info.degree = create.degree
                    db_edu_info.specialization = create.specialization
                    db_edu_info.start_date = create.start_date
                    db_edu_info.end_date = create.end_date
                    db_edu_info.description = create.description
                    db.commit()
                    return { 'detail' : 'Education Info Updated' }
                else:
                    raise HTTPException(status_code=400, detail='You can edit only your info or Invalid info')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/pa_edu_info')
def PAEduInfo(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.user_uuid == user_uuid, models.PAEducationInfo.is_deleted == False).order_by(models.PAEducationInfo.created_at.desc()).all()
            return { 'data' : db_data }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.patch('/delete_pa_edu_info')
def DeletePAEduInfo(request: Request, edu_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.uuid == edu_uuid, models.PAEducationInfo.is_deleted == False).first()
            if db_data:
                db_data.is_deleted = True
                db.commit()
                return { 'detail' : 'Edu Info removed' }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post('/pa_work_info')
def PAWorkInfo(request: Request, create: userSchema.PAWorkInfo, work_uuid: Optional[UUID] = None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == 'Personal', models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if not work_uuid:
                db_work = models.PAWorkInfo(user_uuid=user_uuid, designation=create.designation, company_name=create.company_name, industry=create.industry, start_date=create.start_date, end_date=create.end_date, roles_responsibilities=create.roles_responsibilities)
                db.add(db_work)
                db.commit()
                call_log(logger, description='Work Info Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Work Info Added'}
            else:
                db_work_info = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.user_uuid == user_uuid, models.PAWorkInfo.uuid == work_uuid).first()
                if db_work_info:
                    db_work_info.designation = create.designation
                    db_work_info.company_name = create.company_name
                    db_work_info.industry = create.industry
                    db_work_info.location = create.location
                    db_work_info.start_date = create.start_date
                    db_work_info.end_date = create.end_date
                    db_work_info.roles_responsibilities = create.roles_responsibilities
                    db.commit()
                    return { 'detail' : 'Work Info Updated' }
                else:
                    raise HTTPException(status_code=400, detail='You can edit only your info or Invalid info')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/pa_work_info')
def PAWorkInfo(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.user_uuid == user_uuid, models.PAWorkInfo.is_deleted == False).order_by(models.PAWorkInfo.created_at.desc()).all()
            return { 'data' : db_data }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.patch('/delete_pa_work_info')
def DeletePAWorkInfo(request:Request, work_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.uuid == work_uuid).first()
            if db_data:
                db_data.is_deleted = True
                db.commit()
            return { 'detail' : 'Work Info removed' }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    

@router.post('/pa_project')
def PAProject(request: Request, create: userSchema.PAProject, project_uuid: Optional[UUID] = None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == 'Personal', models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if not project_uuid:
                db_project = models.PAProject(user_uuid=user_uuid, name=create.name, start_date=create.start_date, end_date=create.end_date, url=create.url, description=create.description)
                db.add(db_project)
                db.commit()
                call_log(logger, description='Project Details Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Project Details Added'}
            else:
                db_project_info = db.query(models.PAProject).filter(models.PAProject.uuid == project_uuid).first()
                if db_project_info:
                    db_project_info.name = create.name
                    db_project_info.start_date = create.start_date
                    db_project_info.end_date = create.end_date
                    db_project_info.url = create.url
                    db_project_info.description = create.description
                    db.commit()
                    return { 'detail' : 'Project Details Updated' }
                else:
                    raise HTTPException(status_code=400, detail='You can edit only your info or Invalid info')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/pa_project')
def PAProject(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False).first()
        if db_user:
            db_data = db.query(models.PAProject).filter(models.PAProject.user_uuid == user_uuid, models.PAProject.is_deleted == False).order_by(models.PAProject.created_at.desc()).all()
            return { 'data' : db_data }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.patch('/delete_pa_project_info')
def DeletePAProjectInfo(request:Request, project_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.PAProject).filter(models.PAProject.uuid == project_uuid).first()
            if db_data:
                db_data.is_deleted = True
                db.commit()
            return { 'detail' : 'Project removed' }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    

@router.post('/social_links')
def SocialLinks(request: Request, create: userSchema.SocialLinks, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_check = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == user_uuid).first()
            if not db_check:
                db_sociallinks = models.SocialLink(user_uuid=user_uuid,  facebook=create.facebook, instagram=create.instagram, youtube=create.youtube, twitter=create.youtube, linkedin=create.linkedin, threads=create.threads, discord=create.discord)
                db.add(db_sociallinks)
                db.commit()
                call_log(logger, description='SocialLinks Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'SocialLinks Added'}
            else:
                db_check.facebook = create.facebook
                db_check.instagram = create.instagram
                db_check.youtube = create.youtube
                db_check.twitter = create.twitter
                db_check.linkedin = create.linkedin
                db_check.discord = create.discord
                db_check.threads = create.threads
                db.commit()
                return { 'detail' : 'SocialLinks Updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/social_links')
def SocialLinks(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == user_uuid, models.SocialLink.is_deleted == False).first()
            return { 'detail' : db_data }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    

@router.patch('/delete_social_links')
def DeleteSociallinks(request:Request, social_links_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.SocialLink).filter(models.SocialLink.uuid == social_links_uuid).first()
            if db_data:
                db_data.is_deleted = True
                db.commit()
            return { 'detail' : 'Social Links removed' }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
@router.post('/add_skills')
def AddSkills(request: Request, create: userSchema.Skils, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == 'Personal', models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_personal = db.query(models.Personal).filter(models.Personal.user_uuid == user_uuid, models.Personal.is_deleted == False).first()
            if db_personal:
                db_personal.skills = create.skills
                db.commit()
                return { 'detail' : 'Skills Added' }
            else:
                raise HTTPException(status_code=400, detail='User details not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/skills')
def Skills(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.category == "Personal", models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_data = db.query(models.Personal).filter(models.Personal.user_uuid == user_uuid).first()
            return { 'detail' : db_data.skills }
        else:
            raise HTTPException(status_code=400, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    

@router.post('/organization_account')
def OrganizationAccount(request: Request, create: userSchema.Organizations, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_user.category = 'Organization'
            db_user.is_protected = False
            if create.fullname:
                db_user.fullname = create.fullname
            db.commit()
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if not db_setting:
                db_create = models.Setting(user_uuid=user_uuid, private_setting="Everyone", blocked_account = [])
                db.add(db_create)
                db.commit()
            db_check = db.query(models.Organization).filter(models.Organization.user_uuid == user_uuid).first()
            if not db_check:
                db_organization = models.Organization(user_uuid=user_uuid)
                db.add(db_organization)
                db.commit()
                call_log(logger, description='Organization profile created', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Organization profile created' }
            else:
                if create.o_type:
                    db_check.organization_type = create.o_type
                if create.location:
                    db_check.location= create.location
                if create.industry:
                    db_check.industry= create.industry
                if create.website:
                    db_check.website= create.website
                if create.mail_address and create.phone_no:
                    db_check.contact_us = {'mail_address': create.mail_address, 'phone_no': create.phone_no}
                if create.company_size:
                    db_check.company_size = create.company_size
                if create.head_quaters:
                    db_check.head_quaters = create.head_quaters
                if create.established_year:
                    db_check.established_year = create.established_year
                db.commit()
                return { 'detail' : 'Organization profile updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.post('/institute_account')
def InstituteAccount(request: Request, create: userSchema.Institutes, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_user.category = 'Institution'
            db_user.is_protected = False
            if create.fullname:
                db_user.fullname = create.fullname
            db.commit()
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if not db_setting:
                db_create = models.Setting(user_uuid=user_uuid, private_setting="Everyone", blocked_account = [])
                db.add(db_create)
                db.commit()
            db_check = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid).first()
            if not db_check:
                db_institute = models.EduInstitute(user_uuid=user_uuid)
                db.add(db_institute)
                db.commit()
                call_log(logger, description='Institute profile created', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Institute profile created' }
            else:
                if create.i_type:
                    db_check.institute_type= create.i_type
                if create.location:
                    db_check.location= create.location
                if create.website:
                    db_check.website= create.website
                if create.mail_address and create.phone_no:
                    db_check.contact_us = {'mail_address': create.mail_address, 'phone_no': create.phone_no}
                if create.established_year:
                    db_check.established_year = create.established_year
                if create.ranking:
                    db_check.ranking = create.ranking
                if create.recognised_by:
                    db_check.recognised_by = create.recognised_by
                if create.strength:
                    db_check.strength = create.strength
                if create.academic_facilities:
                    db_check.academic_facilities = create.academic_facilities
                if create.course_url:
                    db_check.course_url= create.course_url
                if create.admission_url:
                    db_check.admission_url= create.admission_url
                db.commit()
                return { 'detail' : 'Institute profile updated' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
        

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

@router.get('/get_org_users')
def GetOrgUsers(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True ).first()
        if db_user:
            db_users = db.query(models.User).filter(models.User.is_deleted == False,models.User.is_active == True, models.User.category == "Organization").order_by(models.User.created_at.desc()).all()
            for users in db_users:
                del(users.hashed_password)
                del(users.verification_code)
                db_organization = db.query(models.Organization).filter(models.Organization.user_uuid == users.uuid, models.Organization.is_deleted == False).all()
                if db_organization:
                    users.profile = db_organization
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
    
    
@router.patch('/upload_profile_photo')
def UploadProfilePhoto(request: Request, upload: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            extention = "png"
            s3_file_path = 'ProfilePhoto' + '/' + str(user_uuid) + '.' + str(extention)
            s3.upload_fileobj(upload.file, verification_bucket_name, s3_file_path)
            url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
            db_user.profile_photo = cloudfront_url + s3_file_path
            db.commit()
            call_log(logger, description='User Profile Photo uploaded', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'data' : db_user.profile_photo }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.patch('/upload_cover_image')
def UploadCoverImage(request: Request, upload: UploadFile = File(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            # file_type = upload.content_type
            extention = "png"
            s3_file_path = 'CoverImage' + '/' + str(db_user.uuid) + '.' + str(extention)
            s3.upload_fileobj(upload.file, verification_bucket_name, s3_file_path)
            url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
            db_user.cover_image = cloudfront_url + s3_file_path
            db.commit()
            call_log(logger, description='User Cover Image uploaded', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'data' : db_user.cover_image }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_users_to_tag')
def GetUserstoTag(request:Request, text: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{text}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        users=[]
        if db_user:
            db_user_tag = db.query(models.User, models.Setting).filter(or_(models.User.MID.ilike(input), models.User.MID == text), models.User.is_deleted == False, models.User.is_active == True,  models.Setting.private_setting == 'Everyone', models.User.uuid == models.Setting.user_uuid).all()
            if db_user_tag:               
                for user_tag in db_user_tag:
                    del(user_tag['User'].verification_code)
                    del(user_tag['User'].hashed_password)
                    users.append(user_tag['User'])                   
                return { 'data' : users }
            else:
                raise HTTPException(status_code=400, detail='Search results not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')


@router.get('/get_hashtags')
def GetHashtag(request:Request, hashtags: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{hashtags}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.hashtags.ilike(input)).all()
            # db_search = db.query(models.Hashtag, models.EBattle, models.Post, models.Certificate).filter(models.Hashtag.caption.ilike(input), models.EBattle.hashtags == hashtags, models.Post.hashtags == hashtags, models.Certificate.hashtags == hashtags).all()
            # if db_hashtag:               
            #     for hasht in db_hashtag:
            #         hashtags.append(db_hashtag)                   
            return { 'data' : db_hashtag[:5] }
            # else:
            #     raise HTTPException(status_code=400, detail='Search results not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')

@router.get('/get_user_search')
def GetUserSearch(request:Request, text: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{text}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        users=[]
        db_user = db.query(models.User).filter( models.User.is_deleted == False,  models.User.is_active == True).all()
        if db_user:
            db_block=[]
            db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_my_settings:
                if db_my_settings.blocked_account:
                    db_block=db_my_settings.blocked_account
            db_suggested_list= db.query(models.User).filter(or_(models.User.fullname.ilike(input),models.User.MID.ilike(input),models.User.tagline.ilike(input),models.User.about.ilike(input)),~models.User.uuid.in_(db_block), models.User.is_deleted == False,  models.User.is_active == True).all()
            return { 'data' : db_suggested_list[:10]}
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')
    
   
@router.get('/get_user_setting')
def GetUserSetting(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            return { 'data' : db_setting }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.post('/add_user_title')
# def AddUserTitle(request: Request, db: Session = Depends(get_db)):
#     import openpyxl

#     # Define variable to load the dataframe
#     dataframe = openpyxl.load_workbook("Title.csv")

#     # Define variable to read sheet
#     dataframe1 = dataframe.active

#     # Iterate the loop to read the cell values
#     for row in range(0, dataframe1.max_row):
#         for col in dataframe1.iter_cols(1, dataframe1.max_column):
#             print(col[row].value)
#             db_title = models.Designation(title=col[row].value)
#             db.add(db_title)
#             db.commit()
#     return { 'detail' : 'Titles Added' }


@router.get('/get_job_title')
def GetJobTitle(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.job_title).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_edu_specialization')
def GetEduSpecialization(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.edu_specialization).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_edu_degree')
def GetEduDegree(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.edu_degree).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_industry')
def GetIndustry(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.industry).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_explore_category')
def GetExploreCategory(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.explore_category).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_location')
def GetLocation(request:Request, location: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{location}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_location = db.query(models.location).filter(models.location.location.ilike(input)).all()               
            return { 'data' : db_location[:5] }
        else:
            raise HTTPException(status_code=400, detail='Location not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')
