from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from models.schemas import coreSchema
from sqlalchemy.orm import Session
from models import models, get_db
from jose import jwt, JWTError
from configs import BaseConfig, Configuration
from typing import Optional
from sqlalchemy import delete, or_
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

# @router.post('/add_core_users')
# def AddCoreUsers(request: Request, add: coreSchema.CoreUser, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User, models.EduInstitute).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.EduInstitute.user_uuid == models.User.uuid).first()
#         if db_user:
#             if add.admin_management_uuid:
#                 admin_management = []
#                 for user in add.admin_management_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIAdminManagement).filter(models.EIAdminManagement.user_uuid == user).first()
#                     if db_core:
#                         True
#                     else:
#                         db_add_core = models.EIAdminManagement(user_uuid = user, MID = db_users.MID, edu_institute_uuid = db_user['EduInstitute'].uuid)
#                         db.add(db_add_core)
#                         db.commit()
#                         for users in db_user['EduInstitute'].administration_management:
#                             admin_management.append(users)                              
#                     admin_management.append(user)
#                 db_user['EduInstitute'].administration_management = admin_management
#                 db.commit()
#                 call_log(logger, description='User added as administration_management', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User added as administration_management' }
#             elif add.faculty_uuid:
#                 faculty = []
#                 for user in add.faculty_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIFaculty).filter(models.EIFaculty.user_uuid == user).first()
#                     if db_core:
#                         True
#                     else:
#                         db_add_core = models.EIFaculty(user_uuid = user, MID = db_users.MID, edu_institute_uuid = db_user['EduInstitute'].uuid)
#                         db.add(db_add_core)
#                         db.commit()
#                         for users in db_user['EduInstitute'].faculties:
#                             faculty.append(users)                              
#                     faculty.append(user)
#                 db_user['EduInstitute'].faculties = faculty
#                 db.commit()
#                 call_log(logger, description='User added as faculty', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User added as faculty' }
#             elif add.alumini_uuid:
#                 alumini = []
#                 for user in add.alumini_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIAlumini).filter(models.EIAlumini.user_uuid == user).first()
#                     if db_core:
#                         True
#                     else:
#                         db_add_core = models.EIAlumini(user_uuid = user, MID = db_users.MID, edu_institute_uuid = db_user['EduInstitute'].uuid)
#                         db.add(db_add_core)
#                         db.commit()
#                         for users in db_user['EduInstitute'].aluminies:
#                             alumini.append(users)                              
#                     alumini.append(user)
#                 db_user['EduInstitute'].aluminies = alumini
#                 db.commit()
#                 call_log(logger, description='User added as alumini', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User added as alumini' }
#             else:
#                 raise HTTPException(status_code=400, detail='Enter any user to add')
#         else:
#             raise HTTPException(status_code=400, detail='Only Admin can add users')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
# @router.post('/remove_core_users')
# def RemoveCoreUsers(request: Request, remove: coreSchema.CoreUser, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User, models.EduInstitute).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.EduInstitute.user_uuid == models.User.uuid).first()
#         if db_user:
#             if remove.admin_management_uuid:
#                 admin_management = []
#                 for user in remove.admin_management_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIAdminManagement).filter(models.EIAdminManagement.user_uuid == user).first()
#                     if not db_core:
#                         True
#                     else:
#                         db_remove_core = db.query(models.EIAdminManagement).filter(models.EIAdminManagement.user_uuid == user).delete()
#                         db.commit()
#                         for users in db_user['EduInstitute'].administration_management:
#                             admin_management.append(users)                              
#                     admin_management.remove(user)
#                 db_user['EduInstitute'].administration_management = admin_management
#                 db.commit()
#                 call_log(logger, description='User removed from administration_management', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User removed from administration_management' }
#             elif remove.faculty_uuid:
#                 faculty = []
#                 for user in remove.faculty_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIFaculty).filter(models.EIFaculty.user_uuid == user).first()
#                     if not db_core:
#                         True
#                     else:
#                         db_romove_core = db.query(models.EIFaculty).filter(models.EIFaculty.user_uuid == user).delete()
#                         db.commit()
#                         for users in db_user['EduInstitute'].faculties:
#                             faculty.append(users)                              
#                     faculty.remove(user)
#                 db_user['EduInstitute'].faculties = faculty
#                 db.commit()
#                 call_log(logger, description='User removed from faculty', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User removed from faculty' }
#             elif remove.alumini_uuid:
#                 alumini = []
#                 for user in remove.alumini_uuid:
#                     db_users = db.query(models.User).filter(models.User.uuid == user, models.User.is_deleted == False).first()
#                     db_core = db.query(models.EIAlumini).filter(models.EIAlumini.user_uuid == user).first()
#                     if not db_core:
#                         True
#                     else:
#                         db_remove_core = db.query(models.EIAlumini).filter(models.EIAlumini.user_uuid == user).delete()
#                         db.commit()
#                         for users in db_user['EduInstitute'].aluminies:
#                             alumini.append(users)                              
#                     alumini.remove(user)
#                 db_user['EduInstitute'].aluminies = alumini
#                 db.commit()
#                 call_log(logger, description='User removed from alumini', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'User removed from alumini' }
#             else:
#                 raise HTTPException(status_code=400, detail='Enter any user to remove')
#         else:
#             raise HTTPException(status_code=400, detail='Only Admin can remove users')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.post('/add_core_program')
def AddCoreProgram(request: Request, add: coreSchema.AddProgram = Depends(), upload: UploadFile = File(None), extention:str= Form(None), program_uuid:Optional[UUID]= None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User, models.EduInstitute).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True , models.EduInstitute.user_uuid == models.User.uuid).first()
        if db_user:
            if program_uuid:
                db_core = db.query(models.EIProgramOffer).filter(models.EIProgramOffer.user_uuid == user_uuid, models.EIProgramOffer.uuid == program_uuid).first()
                if db_core:
                    db_core.detail = add.detail
                    db_core.no_of_seat=add.no_of_seat
                    db_core.course_year=add.course_year
                    db_core.course_mode=add.course_mode
                    # db.add(db_core)
                    db.commit()
                    db.refresh(db_core)
                    call_log(logger, description='Program Detail Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail': 'Program Detail Updated' }
                else:
                    raise HTTPException(status_code=400, detail='Program Details not found')
            else:
                db_add_core = models.EIProgramOffer(user_uuid = user_uuid, edu_institute_uuid = db_user['EduInstitute'].uuid, detail=add.detail, no_of_seat=add.no_of_seat, course_year=add.course_year, course_mode=add.course_mode)
                db.add(db_add_core)
                db.commit()
                db.refresh(db_add_core)
                if upload:
                    s3_file_path = 'InstituteDocument' + '/' + str(user_uuid) + '.' + str(extention)
                    s3.upload_fileobj(upload.file, verification_bucket_name, s3_file_path)
                    url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                    db_add_core.document_link = cloudfront_url + s3_file_path
                    db.commit()
                    db.refresh(db_add_core)
           
                call_log(logger, description='Program offer posted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Program offer posted' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.post("/remove_core_program")
def RemoveCoreProgram(request:Request, program_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_core = db.query(models.EIProgramOffer).filter(models.EIProgramOffer.uuid == program_uuid).first()
            if db_core:
                db.execute(delete(models.EIProgramOffer).where(models.EIProgramOffer.uuid == program_uuid))
                db.commit()
                return { 'detail' : 'Program offered removed' }
            # db_institute = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid).first()
            # if db_institute and db_institute.programs_offer:
            #     Programs=db_institute.programs_offer
            #     if str(program_uuid) in Programs:
            #         Programs.remove(str(program_uuid))
            #         db_institute.programs_offer = Programs
            #         db.commit()
            #         db_institute.programs_offer = Programs
            #         db.commit()
                    
            else:
                raise HTTPException(status_code=400, detail="Program details not found")    
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get("/get_program_list")
def GetProgramList(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_programs_offer = db.query(models.EIProgramOffer).filter(models.EIProgramOffer.user_uuid == profile_uuid).all()
            Program=[]
            if db_programs_offer:
                for program in db_programs_offer:
                    db_programs_detail = db.query(models.EIProgramOffer).filter(models.EIProgramOffer.user_uuid == profile_uuid).first()
                    # if db_programs_detail:
                    #     Program.append(db_programs_detail)
                return { 'data' : db_programs_offer }
            else:
                raise HTTPException(status_code=400, detail="No program list found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post('/add_core_admission')
def AddCoreAdmission(request: Request, add: coreSchema.Admission, admission_uuid:Optional[UUID]= None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User, models.EduInstitute).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True , models.EduInstitute.user_uuid == models.User.uuid).first()
        if db_user:
            if admission_uuid:
                db_admission = db.query(models.EIAdmissionDetail).filter(models.EIAdmissionDetail.user_uuid == user_uuid, models.EIAdmissionDetail.edu_institute_uuid == db_user['EduInstitute'].uuid, models.EIAdmissionDetail.uuid == admission_uuid).first()
                if db_admission:
                    db_admission.detail = add.detail
                    db_admission.start_date=add.start_date
                    db_admission.end_date=add.end_date
                    db_admission.course_title=add.course_title 
                    db_admission.academic_year=add.academic_year
                    db_admission.admission_url=add.admission_url
                    db.add(db_admission)
                    db.commit()
                    call_log(logger, description='Admission Detail Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail': 'Admission Detail Updated' }
                else:
                    raise HTTPException(status_code=400, detail='Admission Details not found')
            else:
                db_add_core = models.EIAdmissionDetail(user_uuid = user_uuid, edu_institute_uuid = db_user['EduInstitute'].uuid, detail=add.detail, start_date=add.start_date, end_date=add.end_date, course_title=add.course_title, academic_year=add.academic_year, admission_url=add.admission_url)
                db.add(db_add_core)
                db.commit()
                db.refresh(db_add_core)
                call_log(logger, description='Admission details posted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Admission details posted' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post("/remove_core_admission")
def RemoveCoreAdmission(request:Request, admission_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_core = db.query(models.EIAdmissionDetail).filter(models.EIAdmissionDetail.uuid == admission_uuid).first()
            if db_core:
                db.execute(delete(models.EIAdmissionDetail).where(models.EIAdmissionDetail.uuid == admission_uuid))
                db.commit()
                return { 'detail' : 'Admission details removed' }
            else:
                 raise HTTPException(status_code=400, detail="Admission details not found")  
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.get("/get_admission_list")
def GetAdmissionList(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_admission = db.query(models.EIAdmissionDetail).filter(models.EIAdmissionDetail.user_uuid == profile_uuid).all()
            Admission=[]
            if db_admission:
                for admission in db_admission:
                    db_admission_detail = db.query(models.EIAdmissionDetail).filter(models.EIAdmissionDetail.user_uuid == profile_uuid).first()
                    # if db_admission_detail:
                    #     Admission.append(db_admission_detail)
                return { 'data' :db_admission }
            else:
                raise HTTPException(status_code=400, detail="No admission list found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.post('/add_core_placement')
def AddCorePlacement(request: Request, add: coreSchema.Placement = Depends() , placement_uuid:Optional[UUID]= None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User, models.EduInstitute).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True, models.EduInstitute.user_uuid == user_uuid).first()
        if db_user:
            if placement_uuid:
                # db_core = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.edu_institute_uuid == db_user['EduInstitute'].uuid, models.EIPlacementPartner.placement_partner_description == add.description, models.EIPlacementPartner.placement_partner_id == add.placement_partner_id).first()
                db_placement_partner = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.edu_institute_uuid == db_user['EduInstitute'].uuid, models.EIPlacementPartner.user_uuid == user_uuid).first()
                if db_placement_partner:
                    db_placement_partner.placement_partner_description = add.description
                    db_placement_partner.placement_partner_id = add.placement_partner_id
                   # db.add(db_placement_partner)
                    db.commit()
                    call_log(logger, description='Placement Pratner Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail': 'Placement Partner Updated' }
                else:
                    raise HTTPException(status_code=400, detail='Placement details not found')
            else:
                db_placement_partner = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.edu_institute_uuid == db_user['EduInstitute'].uuid, models.EIPlacementPartner.user_uuid == user_uuid).first()
                if db_placement_partner:
                    if (models.EIPlacementPartner.edu_institute_uuid == db_user['EduInstitute'].uuid):       
                        raise HTTPException(status_code=400, detail='You are posted the placement partner')
                else:
                    db_add_core = models.EIPlacementPartner(edu_institute_uuid = db_user['EduInstitute'].uuid, placement_partner_description=add.description, placement_partner_id=add.placement_partner_id,  user_uuid=user_uuid)
                    db.add(db_add_core)
                    db.commit()
                    db.refresh(db_add_core)
                call_log(logger, description='Placement Partner Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Placement Partner Created' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post("/remove_core_placement")
def RemoveCorePlacement(request:Request, placement_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_core = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.uuid == placement_uuid).first()
            if db_core:
                db.execute(delete(models.EIPlacementPartner).where(models.EIPlacementPartner.uuid == placement_uuid))
                db.commit()
                return { 'detail' : 'Placement details removed' }
            else:
                raise HTTPException(status_code=400, detail="Placement details not found")           
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.get("/get_placement_list")
def GetPlacementList(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_partner = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.user_uuid == profile_uuid).all()
            Partner=[]
            if db_partner:
                for placement in db_partner:
                    db_partner_detail = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.user_uuid == profile_uuid).first()
                    if db_partner_detail:
                        for partner_uuid in db_partner_detail.placement_partner_id:
                            db_partner = db.query(models.User.uuid, models.User.fullname, models.User.profile_photo, models.User.tagline, models.User.MID).filter(models.User.uuid == partner_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                            Partner.append(db_partner)
                        db_partner_detail.user_details = Partner
                         
                return { 'data' : db_partner_detail }
            else:
                raise HTTPException(status_code=400, detail="No placement list found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.get('/get_user_partner')
# def GetUserPartner(placement_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#                 db_partner = db.query(models.EIPlacementPartner).filter(models.EIPlacementPartner.uuid == placement_uuid).all()
#                 for placement in db_partner:
#                     db_partner_details = db.query(models.User).filter(models.User.uuid == db_partner.user_uuid, models.User.is_deleted == False).first()
#                     db_partner_id = db.query(models.User).filter(models.User.uuid == db_partner.placement_uuid, models.User.is_deleted == False).first()
#                     db_partner.user_details = db_partner_details
#                     db_partner.partner_details = db_partner_id
#                 return { 'data' : db_partner }  
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

# @router.get("/get_administration_management_list")
# def GetAdministrationManagementList(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_administration = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid).order_by(models.EduInstitute.administration_management.created_at.desc()).first()
#             Administration=[]
#             if db_administration and db_administration.administration_management:
#                 for administration_uuid in db_administration.administration_management:
#                     db_administration_management = db.query(models.User).filter(models.User.uuid == administration_uuid, models.User.is_deleted == False).first()
#                     if db_administration_management:
#                         del(db_administration_management.hashed_password)
#                         del(db_administration_management.verification_code)
#                     Administration.append(db_administration_management)
#                 return { 'data' : Administration }
#             else:
#                 raise HTTPException(status_code=400, detail="No Administration list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_faculties_list")
# def GetFacultiesList(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_faculty = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid).order_by(models.EduInstitute.created_at.desc()).first()
#             Faculty=[]
#             if db_faculty and db_faculty.faculties:
#                 for faculty_uuid in db_faculty.faculties:
#                     db_faculties = db.query(models.User).filter(models.User.uuid == faculty_uuid, models.User.is_deleted == False).first()
#                     if db_faculties:
#                         del(db_faculties.hashed_password)
#                         del(db_faculties.verification_code)
#                     Faculty.append(db_faculties)
#                 return { 'data' : Faculty }
#             else:
#                 raise HTTPException(status_code=400, detail="No Faculty list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_aluminies_list")
# def GetAluminiesList(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_alumini = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == user_uuid).first()
#             Alumini=[]
#             if db_alumini and db_alumini.aluminies:
#                 for alumini_uuid in db_alumini.aluminies:
#                     db_aluminies = db.query(models.User).filter(models.User.uuid == alumini_uuid, models.User.is_deleted == False).first()
#                     if db_aluminies:
#                         del(db_aluminies.hashed_password)
#                         del(db_aluminies.verification_code)
#                     Alumini.append(db_aluminies)
#                 return { 'data' : Alumini }
#             else:
#                 raise HTTPException(status_code=400, detail="No alumini list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
