from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from botocore.signers import CloudFrontSigner
from configs import BaseConfig, Configuration
from models.schemas import settingSchema
from sqlalchemy.orm import Session
from sqlalchemy import delete
from models import models, get_db
from jose import jwt, JWTError
from typing import Optional
from uuid import UUID
import boto3
import datetime

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

@router.patch('/mentions_setting')
def MentionsSetting(request: Request, setting: settingSchema.Setting, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,models.User.is_active == True).first()
        if db_user:
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_setting:
                # db_setting.private_account=update.is_private 
                db_setting.private_setting=setting
                db.commit()
                call_log(logger, description='Mentions Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Setting Updated' }
            else:
                # db_create = models.Setting(user_uuid=user_uuid, private_account=update.is_private, private_setting=setting)
                db_create = models.Setting(user_uuid=user_uuid, private_setting=setting)
                db.add(db_create)
                db.commit()
                call_log(logger, description='Mentions Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Setting Added' }
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    
# @router.patch('/protect_account')
# def ProtectAccount(request: Request, update: settingSchema.ProtectAccount, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
#             if db_setting:
#                 db_setting.protect_account=update.is_protected
#                 db.commit()
#                 call_log(logger, description='Account Status Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Setting Updated' }
#             else:
#                 db_create = models.Setting(user_uuid=user_uuid, protect_account=update.is_protected)
#                 db.add(db_create)
#                 db.commit()
#                 call_log(logger, description='Account Status Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Setting Added' }
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


@router.patch('/protect_account')
def ProtectAccount(request: Request, update: settingSchema.ProtectAccount, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_user = db.query(models.User).filter(models.User.uuid == user_uuid).first()
            if db_user:
                db_user.is_protected=update.is_protected
                db.commit()
                call_log(logger, description='Account Status Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Setting Updated' }
            else:
                db_create = models.User(user_uuid=user_uuid, is_protected=update.is_protected)
                db.add(db_create)
                db.commit()
                call_log(logger, description='Account Status Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Setting Added' }
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.patch('/block_account')
def BlockAccount(request: Request, update: settingSchema.BlockAccount, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if str(update.block_user_uuid) ==user_uuid:
                            raise HTTPException(status_code=400, detail='you didnt block yourself')
            db_setting = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_setting:
                # if db_setting.blocked_account == block_user_uuid:
                #    raise HTTPException(status_code=400, detail='You didn't blocked this person')
                if db_setting.blocked_account:

                    block=[]
                    for blocks in db_setting.blocked_account:
                        block.append(blocks)
                     
                    # else:
                    #     blocks=[]
                    #     blocks.append(update.block_user_uuid)
                    #     db_update = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
                    #     db_update.blocked_account=blocks
                    #     db.commit()                  
                    if update.is_blocked:
                        if str(update.block_user_uuid) in db_setting.blocked_account:
                           raise HTTPException(status_code=400, detail='User already blocked')
                        block.append(update.block_user_uuid)
                        db_update = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
                        db_update.blocked_account=block
                        db.commit()
                        db_sender = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid).first()
                        db_receive = db.query(models.Boosts).filter(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid ).first()
                        if db_sender:
                            db.execute(delete(models.Boosts).where(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid))
                            db.commit()
                        elif db_receive:
                            db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid))
                            db.commit()
                        call_log(logger, description='Account Blocked', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Account Blocked Successfully' }
                    else: 
                        if str(update.block_user_uuid) not in block:
                            raise HTTPException(status_code=400, detail='User not found')         
                        block.remove(str(update.block_user_uuid))
                        db_update = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
                        db_update.blocked_account=block
                        db.commit()
                        call_log(logger, description='Account Unblocked', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Account Unblocked' }
                else:
                    if update.is_blocked:
                        block=[]
                        block.append(update.block_user_uuid)
                        db_update = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
                        db_update.blocked_account=block
                        db.commit()
                        db_sender = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid).first()
                        db_receive = db.query(models.Boosts).filter(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid ).first()
                        if db_sender:
                            db.execute(delete(models.Boosts).where(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid))
                            db.commit()
                        elif db_receive:
                            db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid))
                            db.commit()
                        call_log(logger, description='Account Blocked', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Account Blocked Successfully' }
                    else:
                        raise HTTPException(status_code=400, detail='User already unblocked')
            else:
                if update.is_blocked is True:
                    block=[]
                    block.append(update.block_user_uuid)
                    db_create = models.Setting(user_uuid=user_uuid, blocked_account=block)
                    db.add(db_create)
                    db.commit()
                    db_sender = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid).first()
                    db_receive = db.query(models.Boosts).filter(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid ).first()
                    if db_sender:
                        db.execute(delete(models.Boosts).where(models.Boosts.receiver_uuid == update.block_user_uuid, models.Boosts.sender_uuid==user_uuid))
                        db.commit()
                    elif db_receive:
                        db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == update.block_user_uuid,models.Boosts.receiver_uuid==user_uuid))
                        db.commit()
                    call_log(logger, description='Account Blocked', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'Account Blocked' }
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.get('/get_blocked_account')
def GetBlockedAccount(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,models.User.is_active == True).first()
        if db_user:
            accounts=[]
            db_blocked = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).order_by(models.Setting.created_at.desc()).first()
            if db_blocked.blocked_account:   
                for block in db_blocked.blocked_account:
                    db_accounts = db.query(models.User).filter(models.User.uuid == block).first()
                    accounts.append(db_accounts)
                return { 'data' : accounts }
            else:
                return { 'detail' : 'No Block user found'}
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/change_password')
# def ChangePassword(request: Request, update: settingSchema.ChangePassword, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             if db_user.verify_password(update.password):
#                 call_log(logger, description='Current password is not matched', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
#                 raise HTTPException(status_code=400, detail='Current password is not matched')
#             else:
#                 if update.password == update.confirm_password:
#                     db_user.hash_password(update.password)
#                     db.commit()
#                     call_log(logger, description='Password Updated successfully', user_uuid=db_user.uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail' : 'Password Updated successfully' }
#                 else:
#                     exception_msg = 'Passwords does not match'
#                     call_log(logger, description=exception_msg, user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
#                     raise HTTPException(status_code=400, detail=exception_msg)
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')   
    
@router.patch('/change_password')
def ChangePassword(request: Request, update: settingSchema.ChangePassword, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if db_user.verify_password(update.current_password):
                if db_user.verify_password(update.password):
                    call_log(logger, description='The new password should be different from previous used password', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                    raise HTTPException(status_code=400, detail='The new password should be different from previous used password')
                else:
                    if update.password == update.confirm_password:
                        db_user.hash_password(update.password)
                        db.commit()
                        call_log(logger, description='Password Updated successfully', user_uuid=db_user.uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Password Updated successfully' }
                    else:
                        exception_msg = 'Passwords does not match'
                        call_log(logger, description=exception_msg, user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                        raise HTTPException(status_code=400, detail=exception_msg)
            else:
                call_log(logger, description='Current password not matched', user_uuid=db_user.uuid, status_code=400, api=request.url.path, ip=request.client.host)
                raise HTTPException(status_code=400, detail='Current password not matched')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.patch('/upload_document')
def UploadDocument(request: Request, status: settingSchema.VerifyStatus, update: settingSchema.DocumentDetails = Depends(), upload: UploadFile = File(...), extention:str= Form(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_upload = models.Verification(user_uuid=user_uuid, document_type=update.d_type, category=update.d_category, full_name=update.fullname, country =update.country, status=status)
            db.add(db_upload)
            db.commit()
            if upload:
                s3_file_path = 'VerifyDocument' + '/' + str(user_uuid) + '.' + str(extention)
                s3.upload_fileobj(upload.file, verification_bucket_name, s3_file_path)
                url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                db_upload.document_url = cloudfront_url + s3_file_path
                db.commit()
                db.refresh(db_upload)
            call_log(logger, description='Document added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail': 'Document added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')    

@router.get("/get_verification_details")
def GetVerifyDetails(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_verify = db.query(models.Verification).filter(models.Verification.user_uuid == profile_uuid).all()
            Verifies=[]
            if db_verify:
                for verify in db_verify:
                    db_verify_detail = db.query(models.User.uuid, models.User.fullname, models.User.profile_photo, models.User.MID, models.Verification.status).filter(models.Verification.user_uuid == profile_uuid).first()
                    # if db_programs_detail:
                    #     Program.append(db_programs_detail)
                return { 'data' : db_verify }
            else:
                raise HTTPException(status_code=400, detail="No Verification list found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/edit_verify_info')
# def EditVerifyInfo(request: Request, update: settingSchema.VerifyInfo, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             if db_user.verify_password(update.password):
#                 if update.email:
#                     db_user.email = update.email
#                 if update.mobile:
#                     db_user.mobile = update.mobile
#                 db.commit()
#                 call_log(logger, description='Email/Mobile Changed', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Email/Mobile Changed' }
#             else:
#                 raise HTTPException(status_code=400, detail='Enter correct Password')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

    
# @router.patch('/personal_edit_info')
# def PersonalEditInfo(request: Request, update: settingSchema.PersonalEditInfo , db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             if update.fullname:
#                 db_user.fullname = update.fullname
#             db_check = db.query(models.Personal).filter(models.Personal.user_uuid == user_uuid, models.Personal.is_deleted == False).first()
#             if db_check:
#                 if update.location:
#                     db_check.location= update.location
#                 if update.DOB:
#                     db_check.DOB= update.DOB
#                 if update.pronounce:
#                     db_check.pronounce= update.pronounce
#                 if update.title:
#                     db_check.title= update.title
#                 if update.mail_address and update.phone_no:
#                     db_check.contact_us = {'mail_address': update.mail_address, 'phone_no': update.phone_no}
#                 db.commit()
#                 call_log(logger, description='Updated Successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Updated Successfully' }
#             else:
#                 raise HTTPException(status_code=400, detail='Profile not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/org_edit_info')
# def OrgEditInfo(request: Request, update: settingSchema.OrgEditInfo , db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()       
#         if db_user:
#             if update.fullname:
#                     db_user.fullname = update.fullname
#             db_check = db.query(models.Organization).filter(models.Organization.user_uuid == user_uuid, models.Organization.is_deleted == False).first()
#             if db_check:
#                 if update.location:
#                     db_check.location= update.location
#                 if update.industry:
#                     db_check.industry= update.industry
#                 if update.website:
#                     db_check.website= update.website
#                 if update.mail_address and update.phone_no:
#                     db_check.contact_us = {'mail_address': update.mail_address, 'phone_no': update.phone_no}
#                 if update.company_size:
#                     db_check.company_size = update.company_size
#                 if update.head_quaters:
#                     db_check.head_quaters = update.head_quaters
#                 if update.established_year:
#                     db_check.established_year = update.established_year
#                 db.commit()
#                 call_log(logger, description='Updated Successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Updated Successfully' }
#             else:
#                 raise HTTPException(status_code=400, detail='Profile not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/ins_edit_info')
# def InstituteEditInfo(request: Request, update: settingSchema.InstituteEditInfo , db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             if update.fullname:
#                 db_user.fullname = update.fullname
#             db_check = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid, models.EduInstitute.is_deleted == False).first()
#             if db_check:
#                 if update.location:
#                     db_check.location= update.location
#                 if update.website:
#                     db_check.website= update.website
#                 if update.mail_address and update.phone_no:
#                     db_check.contact_us = {'mail_address': update.mail_address, 'phone_no': update.phone_no}
#                 if update.established_year:
#                     db_check.established_year = update.established_year
#                 if update.ranking:
#                     db_check.ranking = update.ranking
#                 if update.recognised_by:
#                     db_check.recognised_by = update.recognised_by
#                 if update.strength:
#                     db_check.strength = update.strength
#                 if update.student_placed:
#                     db_check.student_placed = update.student_placed
#                 if update.academic_facilities:
#                     db_check.academic_facilities = update.academic_facilities
#                 if update.entrance_eligibility:
#                     db_check.entrance_eligibility = update.entrance_eligibility
#                 db.commit()
#                 call_log(logger, description='Updated Successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Updated Successfully' }
#             else:
#                 raise HTTPException(status_code=400, detail='Profile not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

@router.post("/partner_and_services")
def add_partner_and_services(request: Request, add: settingSchema.PartnerAndServices, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_create = models.PartnerAndServices( organization_name=add.organization_name, location=add.location, website=add.website, services=add.services, email=add.email, mobile=add.mobile)
            db.add(db_create)
            db.commit()
            db.refresh(db_create)
            return { 'data' : "Successfully Submitted"}
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_app_data')
def GetAppData(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_titles = db.query(models.app_data).all()
            return { 'data' : db_titles }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError: 
          raise HTTPException(status_code=401, detail='Unauthorized')