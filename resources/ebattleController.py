from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, Form
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from fastapi_pagination import paginate, Params
from configs import BaseConfig, Configuration
from models.schemas import ebattleSchema
from sqlalchemy.orm import Session
from sqlalchemy import or_ , func
from models import models, get_db
from configs import BaseConfig
from jose import jwt, JWTError
from typing import Optional
from uuid import UUID
import boto3
import base64
from datetime import datetime, date
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
    
@router.post('/add_ebattle')
def AddEBattle(request: Request, add: ebattleSchema.AddEBattle, battle_uuid: Optional[UUID] = None, hashtag: list[str] = Query(None), tags: list[str] = Query(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if battle_uuid:
                db_ebattle = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid, models.EBattle.user_uuid == user_uuid, models.EBattle.is_deleted == False).first()
                if db_ebattle:
                    db_update = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid).first()
                    db.commit()
                    if add.cover_image_url and not add.cover_image_url.isspace():
                        string=add.cover_image_url
                        idx1 = string.index('/')              
                        extention = "png"
                        s3_file_path = 'Explore - Activities' + '/' + str(db_ebattle.uuid) + '.' + str(extention)
                        s3.put_object(Bucket=verification_bucket_name, Key=s3_file_path, Body=base64.b64decode(add.cover_image_url))
                        url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                        db_ebattle.cover_image_url = cloudfront_url + s3_file_path 
                        db.commit()
                    db_ebattle.category = add.category
                    db_ebattle.title = add.title
                    db_ebattle.is_online_battle = add.is_online_battle
                    db_ebattle.activity_url = add.activity_url
                    db_ebattle.location = add.location
                    db_ebattle.description = add.description  
                    db_ebattle.timezone = add.timezone
                    db_ebattle.start_date= add.start_date
                    db_ebattle.end_date = add.end_date
                    db_ebattle.start_time= add.start_time
                    db_ebattle.end_time = add.end_time                 
                    db_ebattle.guests = add.guests
                    db_ebattle.collab_acc = add.collab_acc
                    if hashtag and ',' in hashtag[0]:
                        hashtag = hashtag[0].split(", ")
                    if tags and ',' in tags[0]:
                        tags = tags[0].split(", ")
                    db_ebattle.hashtags = hashtag
                    if tags:
                        db_ebattle.tags = tags
                    db.commit()
                    db.refresh(db_ebattle)
                    if hashtag:
                        for hasht in hashtag:
                            db_check = db.query(models.Hashtag).filter(models.Hashtag.hashtags == hasht).first()
                            if db_check:
                                db_check.hashtags_count = db_check.hashtags_count+1                           
                                db.commit()
                            else:
                                db_hashtag = models.Hashtag(hashtags=hasht)
                                db.add(db_hashtag)
                                db.commit()
                                db.refresh(db_hashtag)
                                db_hashtag.hashtags_count = 1
                                db.commit()
                    call_log(logger, description='Explore - Activities Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'Explore - Activities Updated' }
                else:
                    raise HTTPException(status_code=400, detail='Explore - Activities not found')
            else:
                db_ebattle = models.EBattle(**add.dict())
                db_ebattle.user_uuid = db_user.uuid
                if hashtag and ',' in hashtag[0]:
                    hashtag = hashtag[0].split(", ")
                if tags and ',' in tags[0]:
                    tags = tags[0].split(", ")
                db_ebattle.tags = tags
                db_ebattle.hashtags = hashtag
                db.add(db_ebattle)
                db.commit()
                db.refresh(db_ebattle)
                if add.cover_image_url:
                    string=add.cover_image_url
                    idx1 = string.index('/')                    
                    extention = "png"
                    s3_file_path = 'Explore - Activities' + '/' + str(db_ebattle.uuid) + '.' + str(extention)
                    s3.put_object(Bucket=verification_bucket_name, Key=s3_file_path, Body=base64.b64decode(add.cover_image_url))
                    url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                    db_ebattle.cover_image_url = cloudfront_url + s3_file_path 
                    db.commit()
                if hashtag:
                    for hasht in hashtag:
                        db_check = db.query(models.Hashtag).filter(models.Hashtag.hashtags == hasht).first()
                        if db_check:
                            db_check.hashtags_count = db_check.hashtags_count+1                        
                            db.commit()
                        else:
                            db_hashtag = models.Hashtag(hashtags=hasht)
                            db.add(db_hashtag)
                            db.commit()
                            db.refresh(db_hashtag)
                            db_hashtag.hashtags_count = 1
                            db.commit()
                call_log(logger, description='Explore - Activities Created', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail' : 'Explore - Activities Created' }
        else:
            raise HTTPException(status_code=400, detail='User not Found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.post('/add_hashtag')
# def AddHashtag(request: Request, battle_uuid: UUID, add: ebattleSchema.Hashtag, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_battle = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid, models.EBattle.user_uuid == user_uuid, models.EBattle.is_deleted == False).first()
#             if db_battle:
#                 db_hastags = db.query(models.Hashtag).filter(models.Hashtag.e_battle_uuid == battle_uuid).first()
#                 if db_hastags and db_hastags.e_battle_uuid:
#                     db_hastags.caption = add.caption
#                     db.commit()
#                     call_log(logger, description='Hastag updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag updated' }
#                 else:
#                     db_hastag = models.Hashtag(user_uuid=user_uuid,e_battle_uuid=battle_uuid, caption=add.caption)
#                     db.add(db_hastag)
#                     db.commit()
#                     call_log(logger, description='Hastag added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag added' }
#             else:
#                 raise HTTPException(status_code=400, detail='EBattle not found')
#         else:
#             raise HTTPException(status_code=400, detail='You can only add or update Hashtag to EBattle created by You')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/search_ebattle')
def Searchebattle(request:Request, text: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{text}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_block=[]
            db_dont_rec=[]
            db_report=[]
            db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_my_settings:
                if db_my_settings.blocked_account:
                    db_block=db_my_settings.blocked_account
            db_dont_recommend = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recommend:
                if db_dont_recommend.ebattle_uuid:
                   db_dont_rec=db_dont_recommend.ebattle_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Ebattle").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_ebattle = db.query(models.EBattle).filter( models.EBattle.is_deleted == False, ~models.EBattle.user_uuid.in_(db_block), ~models.EBattle.uuid.in_(db_report), ~models.EBattle.uuid.in_(db_dont_rec), (or_(models.EBattle.category.ilike(input),models.EBattle.title.ilike(input),models.EBattle.description.ilike(input)))).order_by(func.random()).all()           
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            boosting_list=[]
            for sender_id in db_sender:
                boosting_list.append(sender_id.receiver_uuid)
            for receive_id in db_receive:
                boosting_list.append(receive_id.sender_uuid)
            db_sender_r = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Pending").all()
            db_receive_r = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Pending").all()
            request_list=[]
            for senders_id in db_sender_r:
                request_list.append(senders_id.receiver_uuid)
            for receives_id in db_receive_r:
                request_list.append(receives_id.sender_uuid)
            for ebattle in db_ebattle:
                if ebattle.user_uuid in boosting_list:
                    ebattle.boostingstatus = True
                else:
                    ebattle.boostingstatus = False

                if ebattle.user_uuid in request_list:
                    ebattle.requeststatus = True
                else:
                    ebattle.requeststatus = False
            for ebattle in db_ebattle:
                db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                ebattle.user_profile = db_e_user
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
                db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==ebattle.uuid).all()
                if db_attender:
                    ebattle.attenderCount=len(db_attender)
                else:
                    ebattle.attenderCount=0
                Guests=[]
                if len(ebattle.guests)>0:
                    for guests in ebattle.guests:
                        db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                        if db_guestsdetails:
                           Guests.append(db_guestsdetails)
                ebattle.guestList=Guests
                CollabPart=[]
                if len(ebattle.collab_acc)>0:
                    for collac in ebattle.collab_acc:
                        db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                        if db_colabssdetails:
                           CollabPart.append(db_colabssdetails)
                ebattle.CollabList=CollabPart
                Tags=[]
                if ebattle.tags:
                    for tag in ebattle.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                ebattle.tag_details = Tags
                ebattle.likes = db_likes          
            return { 'data' : { 'items': db_ebattle,'total': 1 ,'page':1 ,'size':1}  }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.post('/like_ebattle')
def LikeEBattle(request: Request, ebattle_uuid: UUID, like: ebattleSchema.Like, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_ebattle = db.query(models.EBattle).filter(models.EBattle.uuid == ebattle_uuid, models.EBattle.is_deleted == False).first()
            if db_ebattle:
                if like.is_liked:
                    db_query=db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.ebattle_uuid == ebattle_uuid, models.Like.is_liked == True).first()
                    if db_query:
                        return {'status': 'Liked already'}
                    else:
                        db_like = models.Like(user_uuid=user_uuid,ebattle_uuid=ebattle_uuid, is_liked=like.is_liked)
                        db.add(db_like)
                        db.commit()
                        db.refresh(db_like)
                        db_ebattle_like = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle_uuid, models.Like.is_liked == True).all()
                        db_ebattle.like_count = len(db_ebattle_like)
                        db.commit()
                        call_log(logger, description='Liked ebattle', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Liked ebattle'}
                else:
                    # to remove the user uuid from the liked table
                    db_remove_like = db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.ebattle_uuid == ebattle_uuid, models.Like.is_liked == True).delete()
                    # db.add(db_remove_like)
                    db.commit()
                    if db_remove_like:
                        db_ebattle_like = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle_uuid, models.Like.is_liked == True).all()
                        db_ebattle.like_count = len(db_ebattle_like)
                        db.commit()
                        call_log(logger, description='Like Removed', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Like Removed'}
                    else:
                        raise HTTPException(status_code=400, detail='Like not found')
            else:
                raise HTTPException(status_code=400, detail='EBattle not Found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.get('/get_ebattle_like')
def GetEbattleLike(request:Request, ebattle_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_like = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle_uuid).order_by(models.Like.created_at.desc()).all()
            if db_like:
                Liked_by=[]
                for d_like in db_like:
                    db_liked_user = db.query(models.User).filter(models.User.uuid == d_like.user_uuid).first()
                    del(db_liked_user.hashed_password)
                    del(db_liked_user.verification_code)
                    Liked_by.append(db_liked_user)
                return { 'Liked_by' : Liked_by }
            else:
                raise HTTPException(status_code=400, detail='Like not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get('/suggested_ebattle')
# def SuggestedEBattle(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_ebattle = db.query(models.EBattle).filter(models.EBattle.to_date >= datetime.utcnow().date()).all()
#             return { 'data' : paginate(db_ebattle, params) }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.post('/dont_recommend_ebattle')
# def DontRecommendEBattle(request: Request, add: ebattleSchema.DontRecomment, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_dont_recomment = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
#             if db_dont_recomment:
#                 ebattles=[]
#                 if add.ebattle_uuid:
#                     for ebattle in db_dont_recomment.ebattle_uuid:
#                         ebattles.append(ebattle)
#                     for ebattle in add.ebattle_uuid:
#                         ebattles.append(ebattle)
#                     db_dont_recomment.ebattle_uuid = ebattles
#                     db.commit()
#                     call_log(logger, description='Dont Recommend EBattle Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail' : 'You will not see this EBattle again' }
#                 else:
#                     raise HTTPException(status_code=400, detail='Add any EBattle to not recommend')
#             else:
#                 db_add_dont_recomment = models.DontRecomment(ebattle_uuid = add.ebattle_uuid)
#                 db.add(db_add_dont_recomment)
#                 db.commit()
#                 call_log(logger, description='Dont Recommend EBattle Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'You will not see this EBattle again' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

@router.post('/dont_recommend_Ebattle')
def DontRecommendEbattle(request: Request, ebattle_uuid: list[UUID], db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_dont_recomment = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recomment:
                ebattles=[]
                if ebattle_uuid:
                    if db_dont_recomment.ebattle_uuid:
                        if ebattle_uuid[0] in db_dont_recomment.ebattle_uuid:
                           raise HTTPException(status_code=400, detail='Already added') 
                        else:
                            for ebattle in db_dont_recomment.ebattle_uuid:
                                ebattles.append(ebattle)                             
                            ebattles.append(ebattle_uuid[0])
                            db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                            print(ebattles)
                            db_update.ebattle_uuid = ebattles
                            db.commit()
                            call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                            return { 'detail' : 'Dont recommend Ebattle Updated' }     
                    else:
                        ebattles.append(ebattle_uuid[0])
                        db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                        db_update.ebattle_uuid = ebattles
                        db.commit()
                        call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Dont recommend ebattle Updated' }             
                else:
                    raise HTTPException(status_code=400, detail='Add any ebattle to dont recommend')               
            else:
                print(ebattle_uuid,1)
                db_add_dont_recomment=models.DontRecomment(user_uuid=user_uuid, ebattle_uuid=ebattle_uuid)           
                db.add(db_add_dont_recomment)
                db.commit()
                call_log(logger, description='Dont Recommend Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Dont recommend ebattle Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.patch('/delete_ebattle')
def DeleteEBattle(request: Request, battle_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_battle = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid, models.EBattle.user_uuid == user_uuid, models.EBattle.is_deleted == False).first()
            if db_battle:
                db_battle.is_deleted = True
                db.commit()
                call_log(logger, description='EBattle Deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail': 'EBattle Deleted' }
            else:
                raise HTTPException(status_code=400, detail='EBattle not found')
        else:
            raise HTTPException(status_code=400, detail='You can only delete EBattle created by You')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.post('/join_ebattle')
# def JoinEBattle(request: Request, form_data: ebattleSchema.JoinEBattle = Depends(),  extention:str= Form(None), file: UploadFile = File(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_battle = db.query(models.EBattle).filter(models.EBattle.uuid == form_data.e_battle_uuid, models.EBattle.is_deleted == False).first()
#             if db_battle:
#                 db_join_ebattle = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid == form_data.e_battle_uuid, models.JoinEBattle.user_uuid == user_uuid).first()
#                 if not db_join_ebattle:                
#                     if db_battle.to_date > datetime.datetime.utcnow():
#                         db_join_update=models.JoinEBattle(e_battle_uuid=form_data.e_battle_uuid, caption=form_data.caption, email=form_data.email, mobile= form_data.mobile, user_uuid= user_uuid)
#                         db.add(db_join_update)
#                         db.commit()
#                         db.refresh(db_join_update)
#                         if file:
#                             s3_file_path = 'Explore' + '/' + 'Joined Person' + '/' + str(db_join_update.uuid) + '.' + str(extention)
#                             s3.upload_fileobj(file.file, verification_bucket_name, s3_file_path)
#                             url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
#                             db_join_update.image_url = cloudfront_url + s3_file_path
#                             db.commit()
#                             db.refresh(db_join_update)
#                         call_log(logger, description='Joined in activities', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                         return { 'detail' : 'Joined in activities' }
#                     else:
#                         raise HTTPException(status_code=400, detail='Activities joining date closed')
#                 else:
#                     raise HTTPException(status_code=400, detail='You have already joined this Activities')
#             else:
#                 raise HTTPException(status_code=400, detail='Activities not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not Found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

@router.post('/join_ebattle')
def JoinEBattle(request: Request, form_data: ebattleSchema.JoinEBattle = Depends(), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_battle = db.query(models.EBattle).filter(models.EBattle.uuid == form_data.e_battle_uuid, models.EBattle.is_deleted == False).first()
            if db_battle:
                db_join_ebattle = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid == form_data.e_battle_uuid, models.JoinEBattle.user_uuid == user_uuid).first()
                if not db_join_ebattle:  
                    if datetime.datetime.strptime(db_battle.end_date, "%d %b %Y")  > datetime.datetime.utcnow():
                        db_join_update=models.JoinEBattle(e_battle_uuid=form_data.e_battle_uuid, caption=form_data.caption, email=form_data.email, mobile= form_data.mobile, user_uuid= user_uuid)
                        db.add(db_join_update)
                        db.commit()
                        db.refresh(db_join_update)
                        call_log(logger, description='Joined in activities', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Joined in activities' }
                    else:
                        raise HTTPException(status_code=400, detail='Activities joining date closed')
                else:
                    raise HTTPException(status_code=400, detail='You have already joined this Activities')
            else:
                raise HTTPException(status_code=400, detail='Activities not found')
        else:
            raise HTTPException(status_code=400, detail='User not Found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/Getuser_join_ebattle')
def GetuserJoinEBattle(request:Request, ebattle_uuid : UUID ,db: Session = Depends(get_db) , token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==ebattle_uuid).order_by(models.JoinEBattle.created_at.desc()).all()
            Attender=[]
            if db_attender:
                for attender in db_attender:
                    db_userdetails = db.query(models.User).filter(models.User.uuid == attender.user_uuid).first()
                    attender.user_profile=db_userdetails
            return {'data':db_attender}
        else:
             raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
        

@router.get('/Get_joined_activity')
def GetJoinedActivity(request:Request, user_uuid : UUID ,db: Session = Depends(get_db) , token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.user_uuid==user_uuid).order_by(models.JoinEBattle.created_at.desc()).all()
            Attender=[]
            if db_attender:
                for attender in db_attender:
                    db_ebattle = db.query(models.EBattle).filter(models.EBattle.is_deleted == False, models.EBattle.uuid==attender.e_battle_uuid).first()
                    Attender.append(db_ebattle)
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == db_ebattle.uuid, models.Like.is_liked == True).all()
                db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==db_ebattle.uuid).all()
                if db_attender:
                    db_ebattle.attenderCount=len(db_attender)
                    for attender in db_attender:
                       if str(user_uuid) == str(attender.user_uuid):
                           db_ebattle.isJoined = True
                       else:
                           db_ebattle.isJoined = False
                else:
                    db_ebattle.attenderCount=0
                    db_ebattle.isJoined = False
                Guests=[]
                if len(db_ebattle.guests)>0:
                    for guests in db_ebattle.guests:
                        db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                        if db_guestsdetails:
                           Guests.append(db_guestsdetails)
                db_ebattle.guestList=Guests
                CollabPart=[]
                if len(db_ebattle.collab_acc)>0:
                    for collac in db_ebattle.collab_acc:
                        db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                        if db_colabssdetails:
                           CollabPart.append(db_colabssdetails)
                db_ebattle.CollabList=CollabPart
                Tags=[]
                if db_ebattle.tags:
                    for tag in db_ebattle.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                db_ebattle.tag_details = Tags
                db_ebattle.likes = db_likes
            return {'data':Attender}
        else:
             raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get('/get_all_ebattles')
# def GetAllEBattles(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             ebattles=[]
#             db_my_ebattles = db.query(models.EBattle).filter(models.EBattle.user_uuid == user_uuid, models.EBattle.is_deleted == False).order_by(models.EBattle.created_at.desc()).all()
#             if db_my_ebattles:
#                 for ebattle in db_my_ebattles:
#                     db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False).first()
#                     if db_e_user.hashed_password and db_e_user.verification_code:
#                         del(db_e_user.hashed_password)
#                         del(db_e_user.verification_code)
#                     ebattle.user_profile = db_e_user
#                     db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
#                     db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.e_battle_uuid == ebattle.uuid).all()
#                     ebattle.hashtag = db_hashtag
#                     ebattle.likes = db_likes
#                     ebattles.append(ebattle)
#             db_boosts = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.boosting_count != None).first()
#             # db_boosts = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.booster_count != None).first()
#             if db_boosts:
#                 for boosting in db_boosts.boosting_uuid:
#                     db_ebattles = db.query(models.EBattle).filter(models.EBattle.user_uuid == boosting, models.EBattle.is_deleted == False).all()
#                 # for booster in db_boosts.booster_uuid:
#                 #     db_ebattles = db.query(models.EBattle).filter(models.EBattle.user_uuid == booster, models.EBattle.is_deleted == False).all()    
#                     for ebattle in db_ebattles:
#                         db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False).first()
#                         if db_e_user.hashed_password and db_e_user.verification_code:
#                             del(db_e_user.hashed_password)
#                             del(db_e_user.verification_code)
#                         ebattle.user_profile = db_e_user
#                         db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
#                         db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.e_battle_uuid == ebattle.uuid).all()
#                         ebattle.hashtag = db_hashtag
#                         ebattle.likes = db_likes
#                         ebattles.append(db_ebattles)
#             # db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid).first()
#             # if db_reports:
#             #     for report in db_reports.ebattle_report:
#             #         if report in ebattles:
#             #             db_report_ebattle = db.query(models.EBattle).filter(models.EBattle.uuid == report).first()
#             #             ebattles.remove(db_report_ebattle)  
#             db_dont_recommend = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
#             if db_dont_recommend:
#                 for dontrecommend in db_dont_recommend.ebattle_uuid:
#                     if dontrecommend in ebattles:
#                         db_dontrecommend_ebattle = db.query(models.EBattle).filter(models.EBattle.uuid == dontrecommend).first()
#                         ebattles.remove(db_dontrecommend_ebattle)
#             return { 'data' : paginate(ebattles, params) }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.get('/get_trending_ebattle')
def GetTrendingEBattle(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_ebattle = db.query(models.EBattle).filter(models.EBattle.is_deleted == False).order_by(models.EBattle.like_count.desc()).all()
            for ebattle in db_ebattle:
                db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                if db_e_user.hashed_password and db_e_user.verification_code:
                    del(db_e_user.hashed_password)
                    del(db_e_user.verification_code)
                ebattle.user_profile = db_e_user
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
                # db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.e_battle_uuid == ebattle.uuid).all()
                # ebattle.hashtag = db_hashtag
                ebattle.likes = db_likes
            return { 'data' : db_ebattle[:10] }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_my_ebattles')
def GetMyEBattles(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_ebattle = db.query(models.EBattle).filter(models.EBattle.user_uuid == profile_uuid, models.EBattle.is_deleted == False).order_by(models.EBattle.created_at.desc()).all()
            if db_ebattle:
                for ebattle in db_ebattle:
                    db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    ebattle.user_profile = db_e_user
                    db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
                    db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==ebattle.uuid).all()
                    if db_attender:
                        ebattle.attenderCount=len(db_attender)
                    else:
                        ebattle.attenderCount=0
                    Guests=[]
                    if len(ebattle.guests)>0:
                        for guests in ebattle.guests:
                            db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                            if db_guestsdetails:
                                Guests.append(db_guestsdetails)
                    ebattle.guestList=Guests
                    CollabPart=[]
                    if len(ebattle.collab_acc)>0:
                        for collac in ebattle.collab_acc:
                            db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                            if db_colabssdetails:
                                CollabPart.append(db_colabssdetails)
                    ebattle.CollabList=CollabPart
                    Tags=[]
                    if ebattle.tags:
                        for tag in ebattle.tags:
                            db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.uuid == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                            Tags.append(db_tag)
                    ebattle.tag_details = Tags
                    ebattle.likes = db_likes         
                return { 'data' : { 'items': db_ebattle,'total': 1 ,'page':1 ,'size':1}  }
            else:
                raise HTTPException(status_code=400, detail='No EBattles yet')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_suggested_ebattle')
def GetSuggestedEBattle(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_block=[]
            db_dont_rec=[]
            db_report=[]
            db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_my_settings:
                if db_my_settings.blocked_account:
                    db_block=db_my_settings.blocked_account
            db_dont_recommend = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recommend:
                if db_dont_recommend.ebattle_uuid:
                   db_dont_rec=db_dont_recommend.ebattle_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Ebattle").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_ebattle = db.query(models.EBattle).filter(models.EBattle.is_deleted == False, ~models.EBattle.user_uuid.in_(db_block), ~models.EBattle.uuid.in_(db_report), ~models.EBattle.uuid.in_(db_dont_rec)).order_by(func.random()).all()
            print(db_ebattle)
            db_ebattle = [
                ebattle for ebattle in db_ebattle
                if datetime.datetime.strptime(ebattle.end_date, "%d %b %Y") > datetime.datetime.utcnow()
            ]
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            boosting_list=[]
            for sender_id in db_sender:
                boosting_list.append(sender_id.receiver_uuid)
            for receive_id in db_receive:
                boosting_list.append(receive_id.sender_uuid)
            db_sender_r = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Pending").all()
            db_receive_r = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Pending").all()
            request_list=[]
            for senders_id in db_sender_r:
                request_list.append(senders_id.receiver_uuid)
            for receives_id in db_receive_r:
                request_list.append(receives_id.sender_uuid)
            for ebattle in db_ebattle:
                if ebattle.user_uuid in boosting_list:
                    ebattle.boostingstatus = True
                else:
                    ebattle.boostingstatus = False

                if ebattle.user_uuid in request_list:
                    ebattle.requeststatus = True
                else:
                    ebattle.requeststatus = False
            for ebattle in db_ebattle:
                print(str(ebattle.end_date).lower())
                db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                ebattle.user_profile = db_e_user
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
                db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==ebattle.uuid).all()
                if db_attender:
                    ebattle.attenderCount=len(db_attender)
                    for attender in db_attender:
                       if str(user_uuid) == str(attender.user_uuid):
                           ebattle.isJoined = True
                       else:
                           ebattle.isJoined = False
                else:
                    ebattle.attenderCount=0
                    ebattle.isJoined = False
                Guests=[]
                if len(ebattle.guests)>0:
                    for guests in ebattle.guests:
                        db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                        if db_guestsdetails:
                           Guests.append(db_guestsdetails)
                ebattle.guestList=Guests
                CollabPart=[]
                if len(ebattle.collab_acc)>0:
                    for collac in ebattle.collab_acc:
                        db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                        if db_colabssdetails:
                           CollabPart.append(db_colabssdetails)
                ebattle.CollabList=CollabPart
                Tags=[]
                if ebattle.tags:
                    for tag in ebattle.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                ebattle.tag_details = Tags
                ebattle.likes = db_likes          
            return { 'data' : paginate(db_ebattle, params)}
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_user_ebattles')
def GetUserEBattles(request:Request, battle_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_ebattles = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid, models.EBattle.is_deleted == False).first()
            if db_ebattles:
                # for ebattle in db_ebattles:
                db_e_user = db.query(models.User).filter(models.User.uuid == db_ebattles.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    # if db_e_user.hashed_password and db_e_user.verification_code:
                    #     del(db_e_user.hashed_password)
                    #     del(db_e_user.verification_code)
                db_ebattles.user_profile = db_e_user
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == db_ebattles.uuid, models.Like.is_liked == True).all()
                # db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.e_battle_uuid == ebattle.uuid).all()
                # ebattle.hashtag = db_hashtag
                db_ebattles.likes = db_likes
                db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==db_ebattles.uuid).all()
                if db_attender:
                    db_ebattles.attenderCount=len(db_attender)
                else:
                    db_ebattles.attenderCount=0
                # Attender=[]
                # if len(db_ebattles.attender)>0:
                #     for attender in db_ebattles.attender:
                #         db_attenderdetails = db.query(models.User).filter(models.User.uuid == attender).first()
                #         if db_attenderdetails:
                #             Attender.append(db_attendersdetails)
                # db_ebattles.attenderList=Attender
                Guests=[]
                if len(db_ebattles.guests)>0:
                    for guests in db_ebattles.guests:
                        db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                        if db_guestsdetails:
                            Guests.append(db_guestsdetails)
                db_ebattles.guestList=Guests
                CollabPart=[]
                if len(db_ebattles.collab_acc)>0:
                    for collac in db_ebattles.collab_acc:
                        db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                        if db_colabssdetails:
                            CollabPart.append(db_colabssdetails)
                db_ebattles.CollabList=CollabPart
                Tags=[]
                if db_ebattles.tags:
                    for tag in db_ebattles.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                db_ebattles.tag_details = Tags
                return { 'data' : db_ebattles }
            else:
                raise HTTPException(status_code=400, detail='No EBattles yet')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/Get_ebattle_by_id')
def GetebattlebyID(request:Request, battle_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_block=[]
            db_dont_rec=[]
            db_report=[]
            db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_my_settings:
                if db_my_settings.blocked_account:
                    db_block=db_my_settings.blocked_account
            db_dont_recommend = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recommend:
                if db_dont_recommend.ebattle_uuid:
                   db_dont_rec=db_dont_recommend.ebattle_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Ebattle").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_ebattle = db.query(models.EBattle).filter(models.EBattle.uuid == battle_uuid, models.EBattle.is_deleted == False, ~models.EBattle.user_uuid.in_(db_block), ~models.EBattle.uuid.in_(db_report), ~models.EBattle.uuid.in_(db_dont_rec)).order_by(func.random()).all()            
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            boosting_list=[]
            for sender_id in db_sender:
                boosting_list.append(sender_id.receiver_uuid)
            for receive_id in db_receive:
                boosting_list.append(receive_id.sender_uuid)
            db_sender_r = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Pending").all()
            db_receive_r = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Pending").all()
            request_list=[]
            for senders_id in db_sender_r:
                request_list.append(senders_id.receiver_uuid)
            for receives_id in db_receive_r:
                request_list.append(receives_id.sender_uuid)
            for ebattle in db_ebattle:
                if ebattle.user_uuid in boosting_list:
                    ebattle.boostingstatus = True
                else:
                    ebattle.boostingstatus = False

                if ebattle.user_uuid in request_list:
                    ebattle.requeststatus = True
                else:
                    ebattle.requeststatus = False
            for ebattle in db_ebattle:
                db_e_user = db.query(models.User).filter(models.User.uuid == ebattle.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                ebattle.user_profile = db_e_user
                db_likes = db.query(models.Like).filter(models.Like.ebattle_uuid == ebattle.uuid, models.Like.is_liked == True).all()
                db_attender = db.query(models.JoinEBattle).filter(models.JoinEBattle.e_battle_uuid==ebattle.uuid).all()
                if db_attender:
                    ebattle.attenderCount=len(db_attender)
                else:
                    ebattle.attenderCount=0
                Guests=[]
                if len(ebattle.guests)>0:
                    for guests in ebattle.guests:
                        db_guestsdetails = db.query(models.User).filter(models.User.uuid == guests).first()
                        if db_guestsdetails:
                           Guests.append(db_guestsdetails)
                ebattle.guestList=Guests
                CollabPart=[]
                if len(ebattle.collab_acc)>0:
                    for collac in ebattle.collab_acc:
                        db_colabssdetails = db.query(models.User).filter(models.User.uuid == collac).first()
                        if db_colabssdetails:
                           CollabPart.append(db_colabssdetails)
                ebattle.CollabList=CollabPart
                Tags=[]
                if ebattle.tags:
                    for tag in ebattle.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                ebattle.tag_details = Tags
                ebattle.likes = db_likes          
            return { 'data' : { 'items': db_ebattle,'total': 1 ,'page':1 ,'size':1}  }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')