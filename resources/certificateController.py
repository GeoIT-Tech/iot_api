from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from fastapi_pagination import paginate, Params
from configs import BaseConfig, Configuration
from models.schemas import certificateSchema
from sqlalchemy.orm import Session
from sqlalchemy import or_ , func
from models import models, get_db
from jose import jwt, JWTError
from configs import BaseConfig
from datetime import datetime
from typing import Optional
from uuid import UUID
import boto3
import base64
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
    
    
@router.post('/add_certificate')
def AddCertificate(request: Request, add: certificateSchema.Certificate, certificate_uuid: Optional[UUID] = None, hashtag: list[str]  = Query(None), tags: list[str] = Query(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if certificate_uuid:
                db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.user_uuid == user_uuid, models.Certificate.is_deleted == False).first()
                if db_certificate:
                    db_update = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid).first()
                    db.commit()
                    if add.cover_image_url and not add.cover_image_url.isspace():
                        string=add.cover_image_url
                        idx1 = string.index('/')
                        extention = "png"
                        s3_file_path = 'Certificate' + '/' + str(db_certificate.uuid) + '.' + str(extention)
                        s3.put_object(Bucket=verification_bucket_name, Key=s3_file_path, Body=base64.b64decode(add.cover_image_url))
                        url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                        db_certificate.cover_image_url = cloudfront_url + s3_file_path           
                        db.commit()
                    db_update.name = add.name
                    db_update.link=add.link
                    db_update.is_paid_course=add.is_paid_course
                    db_update.course_amount=0
                    db_update.is_online_course=add.is_online_course
                    db_update.location=''
                    db_update.from_date=add.from_date
                    db_update.to_date=add.to_date 
                    db_update.description=add.description
                    if hashtag and ',' in hashtag[0]:
                        hashtag = hashtag[0].split(", ")
                    if tags and ',' in tags[0]:
                        tags = tags[0].split(", ")
                    if tags:
                        db_update.tags=tags
                    db_update.hashtags = hashtag
                    db.commit()
                    db.refresh(db_update)
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
                    call_log(logger, description='Certificate Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail' : 'Certificate Updated' }
                else:
                    raise HTTPException(status_code=400, detail='Certificate not found')
            else:
                db_certificate = models.Certificate(**add.dict())
                db_certificate.user_uuid = db_user.uuid
                if hashtag and ',' in hashtag[0]:
                    hashtag = hashtag[0].split(", ")
                if tags and ',' in tags[0]:
                    tags = tags[0].split(", ")
                db_certificate.hashtags = hashtag
                if tags:
                    db_certificate.tags = tags
                db.add(db_certificate)
                db.commit()
                db.refresh(db_certificate)
                if add.cover_image_url:
                    string=add.cover_image_url
                    idx1 = string.index('/')    
                    extention = "png"
                    s3_file_path = 'Certificate' + '/' + str(db_certificate.uuid) + '.' + str(extention)
                    s3.put_object(Bucket=verification_bucket_name, Key=s3_file_path, Body=base64.b64decode(add.cover_image_url))
                    url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                    db_certificate.cover_image_url = cloudfront_url + s3_file_path 
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
                call_log(logger, description='Certificate Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Certificate Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')     
    
   
# @router.post('/add_hashtag')
# def AddHashtag(request: Request, certificate_uuid: UUID, add: certificateSchema.Hashtag, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.user_uuid == user_uuid, models.Certificate.is_deleted == False).first()
#             if db_certificate:
#                 db_hastags = db.query(models.Hashtag).filter(models.Hashtag.certificate_uuid == certificate_uuid).first()
#                 if db_hastags and db_hastags.certificate_uuid:
#                     db_hastags.caption = add.caption
#                     db.commit()
#                     call_log(logger, description='Hastag updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag updated' }
#                 else:
#                     db_hastag = models.Hashtag(user_uuid=user_uuid, certificate_uuid=certificate_uuid, caption=add.caption)
#                     db.add(db_hastag)
#                     db.commit()
#                     call_log(logger, description='Hastag added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag added' }
#             else:
#                 raise HTTPException(status_code=400, detail='Certificate not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
@router.get('/search_certificate')
def SearchCertificate(request:Request, text: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
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
                if db_dont_recommend.certificate_uuid:
                   db_dont_rec=db_dont_recommend.certificate_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Certificate").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_certificates = db.query(models.Certificate).filter(models.Certificate.is_deleted == False, ~models.Certificate.user_uuid.in_(db_block), ~models.Certificate.uuid.in_(db_report), ~models.Certificate.uuid.in_(db_dont_rec),(or_(models.Certificate.name.ilike(input), models.Certificate.description.ilike(input)))).order_by(func.random()).all()
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
            for certificate in db_certificates:
                if certificate.user_uuid in boosting_list:
                    certificate.boostingstatus = True
                else:
                    certificate.boostingstatus = False

                if certificate.user_uuid in request_list:
                    certificate.requeststatus = True
                else:
                    certificate.requeststatus = False
            for certificate in db_certificates:
                db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                certificate.user_profile = db_c_user
                db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if certificate.tags:
                    for tag in certificate.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                certificate.tag_details = Tags
                certificate.comments = db_comments
                certificate.likes = db_likes         
            return { 'data' : { 'items': db_certificates,'total': 1 ,'page':1 ,'size':1}  }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

       
@router.post('/add_comment')
def AddComments(request: Request, certificate_uuid: UUID, comment: certificateSchema.AddComment, comment_uuid: Optional[UUID]= None, hashtag: list[str]  = Query(None), tags: list[str]  = Query(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.is_deleted == False).first()
            if db_certificate:
                db_comments = db.query(models.Comment).filter(models.Comment.uuid == comment_uuid, models.Comment.user_uuid == user_uuid, models.Comment.is_deleted == False).first()
                if db_comments:
                    db_update = db.query(models.Comment).filter(models.Comment.uuid == comment_uuid).first()
                    db.commit()
                    db_comments.comment_details = comment.comment_detail
                    db_update.tags=tags
                    db_update.hashtags=hashtag
                    db.commit()
                    call_log(logger, description='Comment updated successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'status' : 'Comment updated successfully' }
                else:
                    db_comment = models.Comment(user_uuid=user_uuid, certificate_uuid=certificate_uuid, comment_details=comment.comment_detail, tags=tags, hashtags = hashtag)
                    db.add(db_comment)
                    db.commit()
                    db.refresh(db_comment)
                    db_certificate_comment = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate_uuid, models.Comment.is_deleted == False).all()
                    db_certificate.comments_count = len(db_certificate_comment)
                    db.commit()
                    call_log(logger, description='Comment added successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'status' : 'Comment added successfully' }
            else:
                raise HTTPException(status_code=400, detail='Certificate not Found')
        else:
             raise HTTPException(status_code=400, detail='User not found')         
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_comments')
def GetCertificateComments(request:Request, certificate_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate_uuid, models.Comment.is_deleted == False).order_by(models.Comment.created_at.desc()).all()
            if db_comments:
                for comments in db_comments:
                    db_commented_user = db.query(models.User).filter(models.User.uuid == comments.user_uuid).all()
                    for c_user in db_commented_user:
                        if c_user.hashed_password and c_user.verification_code:
                            del(c_user.hashed_password)
                            del(c_user.verification_code)
                    comments.commented_by = db_commented_user
                    db_comment_liked = db.query(models.CommentLikes).filter(models.CommentLikes.comment_uuid == comments.uuid).all()
                    comments.liked = len(db_comment_liked)
                    comments.liked_by =db_comment_liked
                    Tags=[]
                    if comments.tags:
                        for tag in comments.tags:
                            db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                            Tags.append(db_tag)
                    comments.tag_details = Tags
                return { 'data' : db_comments }
            else:
                raise HTTPException(status_code=400, detail='Comments not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.patch('/delete_certificate_comment')
def DeleteComment(request: Request, comment_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_comment = db.query(models.Comment).filter(models.Comment.uuid == comment_uuid, models.Comment.is_deleted == False, models.Comment.user_uuid == user_uuid).first()
            if db_comment:
                db_comment.is_deleted = True
                db.commit()
                db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == db_comment.certificate_uuid, models.Certificate.is_deleted == False).first()
                db_certificate_comment = db.query(models.Comment).filter(models.Comment.certificate_uuid == db_comment.certificate_uuid, models.Comment.is_deleted == False).all()
                db_certificate.comments_count = len(db_certificate_comment)
                db.commit()
                call_log(logger, description='Comment Deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Comment Deleted' }
            else:
                raise HTTPException(status_code=400, detail='Comment not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')    

@router.post('/like_certificate')
def LikeCertificate(request: Request, certificate_uuid: UUID, like: certificateSchema.Like, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.is_deleted == False).first()
            if db_certificate:
                if like.is_liked:
                    db_query=db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.certificate_uuid == certificate_uuid, models.Like.is_liked == True).first()
                    if db_query:
                        return {'status': 'Liked already'}
                    else:
                        db_like = models.Like(user_uuid=user_uuid,certificate_uuid=certificate_uuid, is_liked=like.is_liked)
                        db.add(db_like)
                        db.commit()
                        db.refresh(db_like)
                        db_certificate_like = db.query(models.Like).filter(models.Like.certificate_uuid == certificate_uuid, models.Like.is_liked == True).all()
                        db_certificate.like_count = len(db_certificate_like)
                        db.commit()
                        call_log(logger, description='Liked Certificate', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Liked Certificate'}   
                else:

                    # to remove the user uuid from the liked table
                    db_remove_like = db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.certificate_uuid == certificate_uuid, models.Like.is_liked == True).delete()
                   # db.delete(db_remove_like)
                    db.commit()
                    if db_remove_like:
                        # db.refresh(db_like)
                        db_certificate_like = db.query(models.Like).filter(models.Like.certificate_uuid == certificate_uuid, models.Like.is_liked == True).all()
                        db_certificate.like_count = len(db_certificate_like)
                        db.commit()
                        call_log(logger, description='Like Removed', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Like Removed'}
                    else:
                        raise HTTPException(status_code=400, detail='Like not found')
            else:
                raise HTTPException(status_code=400, detail='Certificate not Found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/get_certificate_like')
def GetCertificateLike(request:Request, certificate_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_like = db.query(models.Like).filter(models.Like.certificate_uuid == certificate_uuid).order_by(models.Like.created_at.desc()).all()
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


@router.patch('/delete_certificate')
def DeleteCertificate(request: Request, certificate_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
        if db_user:
            db_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.is_deleted == False).first()
            if db_certificate:
                db_certificate.is_deleted = True
                db.commit()
                call_log(logger, description='Certificate Deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Certificate Deleted' }
            else:
                raise HTTPException(status_code=400, detail='Certificate not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.post('/dont_recommend_certificate')
# def DontRecommendCertificate(request: Request, add: certificateSchema.DontRecomment, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_dont_recomment = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
#             if db_dont_recomment:
#                 certificates=[]
#                 if add.certificate_uuid:
#                     for certificate in db_dont_recomment.certificate_uuid:
#                         certificates.append(certificate)
#                     for certificate in add.certificate_uuid:
#                         certificates.append(certificate)
#                     db_dont_recomment.certificate_uuid = certificates
#                     db.commit()
#                     call_log(logger, description='Dont Recommend Certificate Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail' : 'You will not see this certificate again' }
#                 else:
#                     raise HTTPException(status_code=400, detail='Add any certificate to not recommend')
#             else:
#                 db_add_dont_recomment = models.DontRecomment(certificate_uuid = add.certificate_uuid)
#                 db.add(db_add_dont_recomment)
#                 db.commit()
#                 call_log(logger, description='Dont Recommend Certificate Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'You will not see this certificate again' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
@router.post('/dont_recommend_certificate')
def DontRecommendCertificate(request: Request, certificate_uuid: list[UUID], db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_dont_recomment = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recomment:
                certificates=[]
                if certificate_uuid:
                    if db_dont_recomment.certificate_uuid:
                        if certificate_uuid[0] in db_dont_recomment.certificate_uuid:
                           raise HTTPException(status_code=400, detail='already added') 
                        else:
                            for certificate in db_dont_recomment.certificate_uuid:
                                certificates.append(certificate)                               
                            certificates.append(certificate_uuid[0])
                            db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                            db_update.certificate_uuid = certificates
                            db.commit()
                            call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                            return { 'detail' : 'Dont recommend certificate Updated' } 
                    else:
                        certificates.append(certificate_uuid[0])
                        db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                        db_update.certificate_uuid = certificates
                        db.commit()
                        call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Dont recommend certificate Updated' }                    
                else:
                    raise HTTPException(status_code=400, detail='Add any certificate to dont recommend')                
            else:
                 db_add_dont_recomment=models.DontRecomment(user_uuid=user_uuid, certificate_uuid=certificate_uuid)           
                 db.add(db_add_dont_recomment)
                 db.commit()
                 call_log(logger, description='Dont Recommend Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                 return { 'detail' : 'Dont recommend certificate Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get('/get_all_certificates')
# def GetAllCertificates(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             certificates=[]
#             db_my_certificates = db.query(models.Certificate).filter(models.Certificate.user_uuid == user_uuid, models.Certificate.is_deleted == False).order_by(models.Certificate.created_at.desc()).all()
#             if db_my_certificates:
#                 for certificate in db_my_certificates:
#                     db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False).first()
#                     if db_c_user.hashed_password and db_c_user.verification_code:
#                         del(db_c_user.hashed_password)
#                         del(db_c_user.verification_code)
#                     certificate.user_profile = db_c_user
#                     db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
#                     db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
#                     db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.certificate_uuid == certificate.uuid).all()
#                     certificate.hashtag = db_hashtag
#                     certificate.comments = db_comments
#                     certificate.likes = db_likes
#                     certificates.append(certificate)
#             db_boosts = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.boosting_count != None).first()
#             # db_boosts = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.booster_count != None).first()
#             if db_boosts:
#                 for boosting in db_boosts.boosting_uuid:
#                     db_certificates = db.query(models.Certificate).filter(models.Certificate.user_uuid == boosting, models.Certificate.is_deleted == False).all()
#                 # for booster in db_boosts.booster_uuid:
#                 #     db_certificates = db.query(models.Certificate).filter(models.Certificate.user_uuid == booster, models.Certificate.is_deleted == False).all()
#                     for certificate in db_certificates:
#                         db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False).first()
#                         if db_c_user.hashed_password and db_c_user.verification_code:
#                             del(db_c_user.hashed_password)
#                             del(db_c_user.verification_code)
#                         certificate.user_profile = db_c_user
#                         db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
#                         db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
#                         db_hashtag = db.query(models.Hashtag).filter(models.Hashtag.certificate_uuid == certificate.uuid).all()
#                         certificate.hashtag = db_hashtag
#                         certificate.comments = db_comments
#                         certificate.likes = db_likes
#                         certificates.append(certificates)
#             # db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid).first()
#             # if db_reports:
#             #     for report in db_reports.certificate_report:
#             #         if report in certificates:
#             #             db_report_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == report).first()
#             #             certificates.remove(db_report_certificate)  
#             db_dont_recommend = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
#             if db_dont_recommend:
#                 for dontrecommend in db_dont_recommend.certificate_uuid:
#                     if dontrecommend in certificates:
#                         db_dontrecommend_certificate = db.query(models.Certificate).filter(models.Certificate.uuid == dontrecommend).first()
#                         certificates.remove(db_dontrecommend_certificate)
#             return { 'data' : paginate(certificates, params) }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_my_certificates')
def GetMyCertificates(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_certificates = db.query(models.Certificate).filter(models.Certificate.user_uuid == profile_uuid, models.Certificate.is_deleted == False).order_by(models.Certificate.created_at.desc()).all()
            if db_certificates:
                for certificate in db_certificates:
                    db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    if db_c_user.hashed_password and db_c_user.verification_code:
                        del(db_c_user.hashed_password)
                        del(db_c_user.verification_code)
                    certificate.user_profile = db_c_user
                    db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).order_by(models.Comment.created_at.desc()).all()
                    db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
                    Tags=[]
                    if certificate.tags:
                        for tag in certificate.tags:
                            db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                            Tags.append(db_tag)
                    certificate.tag_details = Tags
                    certificate.comments = db_comments
                    certificate.likes = db_likes
                return { 'data' : { 'items': db_certificates,'total': 1 ,'page':1 ,'size':1}  }
            else:
                raise HTTPException(status_code=400, detail='No Certificates yet')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_certificate_by_id')
def GetCertificatebyID(request:Request, certificate_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
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
                if db_dont_recommend.certificate_uuid:
                   db_dont_rec=db_dont_recommend.certificate_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Certificate").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_certificates = db.query(models.Certificate).filter(models.Certificate.uuid == certificate_uuid, models.Certificate.is_deleted == False, ~models.Certificate.user_uuid.in_(db_block), ~models.Certificate.uuid.in_(db_report), ~models.Certificate.uuid.in_(db_dont_rec)).order_by(func.random()).all()
           
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
            for certificate in db_certificates:
                if certificate.user_uuid in boosting_list:
                    certificate.boostingstatus = True
                else:
                    certificate.boostingstatus = False

                if certificate.user_uuid in request_list:
                    certificate.requeststatus = True
                else:
                    certificate.requeststatus = False
            for certificate in db_certificates:
                db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                certificate.user_profile = db_c_user
                db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if certificate.tags:
                    for tag in certificate.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                certificate.tag_details = Tags
                certificate.comments = db_comments
                certificate.likes = db_likes         
            return { 'data' : { 'items': db_certificates,'total': 1 ,'page':1 ,'size':1}  }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_suggested_certificates')
def GetSuggestedCertificates(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
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
                if db_dont_recommend.certificate_uuid:
                   db_dont_rec=db_dont_recommend.certificate_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Certificate").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_certificates = db.query(models.Certificate).filter(models.Certificate.is_deleted == False, ~models.Certificate.user_uuid.in_(db_block), ~models.Certificate.uuid.in_(db_report), ~models.Certificate.uuid.in_(db_dont_rec)).order_by(func.random()).all()
           
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
            for certificate in db_certificates:
                if certificate.user_uuid in boosting_list:
                    certificate.boostingstatus = True
                else:
                    certificate.boostingstatus = False

                if certificate.user_uuid in request_list:
                    certificate.requeststatus = True
                else:
                    certificate.requeststatus = False
            for certificate in db_certificates:
                db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                certificate.user_profile = db_c_user
                db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if certificate.tags:
                    for tag in certificate.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                certificate.tag_details = Tags
                certificate.comments = db_comments
                certificate.likes = db_likes         
            return { 'data' : paginate(db_certificates, params) }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
        
@router.get('/get_trending_certificates')
def GetTrendingCertificates(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_certificates = db.query(models.Certificate).filter(models.Certificate.is_deleted == False).order_by(models.Certificate.like_count.desc()).all()
            for certificate in db_certificates: 
                db_c_user = db.query(models.User).filter(models.User.uuid == certificate.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                if db_c_user.hashed_password and db_c_user.verification_code:
                    del(db_c_user.hashed_password)
                    del(db_c_user.verification_code)
                certificate.user_profile = db_c_user
                db_comments = db.query(models.Comment).filter(models.Comment.certificate_uuid == certificate.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.certificate_uuid == certificate.uuid, models.Like.is_liked == True).all()
                certificate.comments = db_comments
                certificate.likes = db_likes
            return { 'data' : db_certificates[:10] }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')