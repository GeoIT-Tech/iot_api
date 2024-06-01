from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Query, Form
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from fastapi_pagination import paginate, Params
from botocore.signers import CloudFrontSigner
from configs import BaseConfig, Configuration
from models.schemas import postSchema
from sqlalchemy.orm import Session
from sqlalchemy import or_ , func
from models import models, get_db
from jose import jwt, JWTError
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

@router.post('/add_post_media')
def AddPostMedia(request: Request,  m_type: postSchema.MediaType, hashtag: list[str]  = Query(None), caption:str = Form(...), extention:str= Form(None), tags: list[str] = Query(None),  file: UploadFile = File(None), post_uuid: Optional[UUID]= None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            if post_uuid:
                db_post = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.user_uuid == user_uuid, models.Post.is_deleted == False).first()
                if db_post: 
                    # if file:
                    #     file_type = file.content_type
                    #     extention = file_type.split('/')[-1]
                    #     s3_file_path = str(user_uuid) + '/' + 'Post' + '/' + str(db_post.uuid) + '.' + str(extention)
                    #     s3.upload_fileobj(file.file, newsfeed_bucket_name, s3_file_path)
                    #     url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': newsfeed_bucket_name, 'Key': s3_file_path }, ExpiresIn = 600000)
                    #     db_post.media_link = url
                    #     db.commit()
                    #     db.refresh(db_post)
                    db_post.caption = caption
                    if hashtag and ',' in hashtag[0]:
                        hashtag = hashtag[0].split(", ")
                    if tags and ',' in tags[0]:
                        tags = tags[0].split(", ")
                    db_post.hashtags = hashtag
                    if tags:
                       db_post.tags=tags
                    if hashtag:
                        for hasht in hashtag:
                            db_check = db.query(models.Hashtag).filter(models.Hashtag.hashtags == hasht).first()
                            if db_check:
                                db_check.hashtags_count = db_check.hashtags_count+1
                                print(db_check.hashtags_count)
                                db.commit()
                            else:
                                db_hashtag = models.Hashtag(hashtags=hasht)
                                db.add(db_hashtag)
                                db.commit()
                                db.refresh(db_hashtag)
                                db_hashtag.hashtags_count = 1
                                db.commit()
                    # db_post.media_type = m_type
                    db.commit()
                    db.refresh(db_post)
                    call_log(logger, description='Post Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail': 'Post Updated'  }
                else:
                    raise HTTPException(status_code=400, detail='Post not found')
            else:
                if hashtag and ',' in hashtag[0]:
                    hashtag = hashtag[0].split(", ")
                if tags and ',' in tags[0]:
                    tags = tags[0].split(", ")
                db_post = models.Post(user_uuid=user_uuid, caption=caption, media_type = m_type, tags=tags, hashtags = hashtag)
                db.add(db_post)
                db.commit()
                db.refresh(db_post)
                if file:
                 # file_type = file.content_type
                 # extention = file_type.split('/')[-1]
                  s3_file_path = 'Post' + '/' + str(db_post.uuid) + '.' + str(extention)
                  s3.upload_fileobj(file.file, verification_bucket_name, s3_file_path)
                  url = s3.generate_presigned_url(ClientMethod = 'get_object', Params = { 'Bucket': verification_bucket_name, 'Key': s3_file_path }, ExpiresIn=None)
                  db_post.media_link = cloudfront_url + s3_file_path
                db.commit()
                db.refresh(db_post)
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
                call_log(logger, description='Post created', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail': 'Post created' }        
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.post('/add_hashtag')
# def AddHashtag(request: Request, post_uuid: UUID, add: postSchema.Hashtag, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_post = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.user_uuid == user_uuid, models.Post.is_deleted == False).first()
#             if db_post:
#                 db_hastags = db.query(models.Hashtag).filter(models.Hashtag.post_uuid == post_uuid).first()
#                 if db_hastags and db_hastags.post_uuid:
#                     db_hastags.caption = add.caption
#                     db.commit()
#                     call_log(logger, description='Hastag updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag updated' }
#                 else:
#                     db_hastag = models.Hashtag(user_uuid=user_uuid, post_uuid=post_uuid, caption=add.caption)
#                     db.add(db_hastag)
#                     db.commit()
#                     call_log(logger, description='Hastag added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Hastag added' }
#             else:
#                 raise HTTPException(status_code=400, detail='Post not found')
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

    
@router.post('/add_comment')
def AddComments(request: Request, post_uuid: UUID, comment: postSchema.AddComment, comment_uuid: Optional[UUID]= None, hashtag: list[str]  = Query(None), tags: list[str]  = Query(None),db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_post = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.is_deleted == False).first()
            if db_post:
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
                    db_comment = models.Comment(user_uuid=user_uuid, post_uuid=post_uuid, comment_details=comment.comment_detail, tags=tags, hashtags = hashtag)
                    db.add(db_comment)
                    db.commit()
                    db.refresh(db_comment)
                    db_post_comment = db.query(models.Comment).filter(models.Comment.post_uuid == post_uuid, models.Comment.is_deleted == False).all()
                    db_post.comments_count = len(db_post_comment)
                    db.commit()
                    call_log(logger, description='Comment added successfully', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'status' : 'Comment added successfully' }
            else:
                raise HTTPException(status_code=400, detail='Post not Found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_comments')
def GetPostComments(request:Request, post_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post_uuid, models.Comment.is_deleted == False).order_by(models.Comment.created_at.desc()).all()
            if db_comments:
                for comments in db_comments:
                    comments.comment_detail = "😁"
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


@router.patch('/delete_post_comment') 
def DeletePostComment(request: Request, comment_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_comment = db.query(models.Comment).filter(models.Comment.uuid == comment_uuid, models.Comment.is_deleted == False, models.Comment.user_uuid == user_uuid).first()
            if db_comment:
                db_comment.is_deleted = True
                db.commit()
                db_post = db.query(models.Post).filter(models.Post.uuid == db_comment.post_uuid, models.Post.is_deleted == False).first()
                db_post_comment = db.query(models.Comment).filter(models.Comment.post_uuid == db_comment.post_uuid, models.Comment.is_deleted == False).all()
                db_post.comments_count = len(db_post_comment)
                db.commit()
                call_log(logger, description='Comment Deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Comment Deleted' }
            else:
                raise HTTPException(status_code=400, detail='Comment not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')    


@router.post('/like_post')
def LikePost(request: Request, post_uuid: UUID, like: postSchema.Like, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_post = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.is_deleted == False).first()
            if db_post:
                # if not already liked then
                if like.is_liked:
                    db_query=db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.post_uuid== post_uuid, models.Like.is_liked == True).first()
                    if db_query:
                         return {'status': 'Liked already'}
                    else:
                        db_like = models.Like(user_uuid=user_uuid, post_uuid=post_uuid, is_liked=like.is_liked)
                        db.add(db_like)
                        db.commit()
                        db.refresh(db_like)
                        db_post_like = db.query(models.Like).filter(models.Like.post_uuid == post_uuid, models.Like.is_liked == True).all()
                        db_post.like_count = len(db_post_like)
                        db.commit()
                        # fcmToken = [fcmToken]
                        # resp = fcm.send_notification("Message","Liked your post", fcmToken)
                        call_log(logger, description='Liked Post', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Liked Post'}
                else:
                    # to remove the useruuid from the liked table
                    db_remove_like = db.query(models.Like).filter(models.Like.user_uuid == user_uuid, models.Like.post_uuid == post_uuid, models.Like.is_liked == True).delete()
                    # db.add(db_remove_like)
                    db.commit()
                    if db_remove_like:
                        db_post_like = db.query(models.Like).filter(models.Like.post_uuid == post_uuid, models.Like.is_liked == True).all()
                        db_post.like_count = len(db_post_like)
                        db.commit()
                        call_log(logger, description='Like Removed', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Like Removed'}
                    else:
                        raise HTTPException(status_code=400, detail='Like not found')
            else:   
                raise HTTPException(status_code=400, detail='Post not Found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/get_all_like')
def GetallLike(request:Request, media_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_like = db.query(models.Like).filter(or_(models.Like.post_uuid == media_uuid,models.Like.certificate_uuid == media_uuid,models.Like.ebattle_uuid == media_uuid)).order_by(models.Like.created_at.desc()).all()
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


@router.post('/like_comment')
def LikeComment(request: Request, comment_uuid: UUID, like: postSchema.Like, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_comment = db.query(models.Comment).filter(models.Comment.uuid == comment_uuid, models.Comment.is_deleted == False).first()
            if db_comment:
                if like.is_liked:
                    db_query=db.query(models.CommentLikes).filter(models.CommentLikes.user_uuid == user_uuid, models.CommentLikes.comment_uuid == comment_uuid, models.CommentLikes.is_liked == True).first()
                    if db_query:
                        return {'status': 'Liked already'}
                    else:
                        db_like = models.CommentLikes(user_uuid=user_uuid, comment_uuid=comment_uuid, is_liked=like.is_liked)
                        db.add(db_like)
                        db.commit()
                        db.refresh(db_like)
                        db_comment_like = db.query(models.CommentLikes).filter(models.CommentLikes.comment_uuid == comment_uuid, models.CommentLikes.is_liked == True).all()
                        db_comment.like_count = len(db_comment_like)
                        db.commit()
                        call_log(logger, description='Liked Comment', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Liked Comment'}
                else:
                    # to remove the user uuid from the liked table
                    db_remove_like = db.query(models.CommentLikes).filter(models.CommentLikes.user_uuid == user_uuid, models.CommentLikes.comment_uuid == comment_uuid, models.CommentLikes.is_liked == True).delete()
                   # db.delete(db_remove_like)
                    db.commit()
                    if db_remove_like:
                        # db.refresh(db_like)
                        db_comment_like = db.query(models.CommentLikes).filter(models.CommentLikes.comment_uuid == comment_uuid, models.CommentLikes.is_liked == True).all()
                        db_comment.like_count = len(db_comment_like)
                        db.commit()
                        call_log(logger, description='Like Removed', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return {'status': 'Like Removed'}
                    else:
                         raise HTTPException(status_code=400, detail='Like not found')
            else:
                raise HTTPException(status_code=400, detail='Comment not Found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.patch('/delete_post')
def DeletePost(request: Request, post_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_post = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.is_deleted == False, models.Post.user_uuid == user_uuid).first()
            if db_post:
                db_post.is_deleted = True
                db.commit()
                call_log(logger, description='Post Deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Post Deleted' }
            else:
                raise HTTPException(status_code=400, detail='You can delete only your own post')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')  
    
@router.post('/dont_recommend_posts')
def DontRecommendposts(request: Request, post_uuid: list[UUID], db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_dont_recomment = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
            if db_dont_recomment:
                posts=[]
                if post_uuid:
                    print(post_uuid)
                    if db_dont_recomment.post_uuid:
                        if post_uuid[0] in db_dont_recomment.post_uuid:
                           raise HTTPException(status_code=400, detail='Already added') 
                        else:
                            for post in db_dont_recomment.post_uuid:
                                posts.append(post)                             
                            posts.append(post_uuid[0])
                            db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                            print(posts)
                            db_update.post_uuid = posts
                            db.commit()
                            call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                            return { 'detail' : 'Dont recommend Post Updated' }     
                    else:
                        posts.append(post_uuid[0])
                        db_update = db.query(models.DontRecomment).filter(models.DontRecomment.user_uuid == user_uuid).first()
                        db_update.post_uuid = posts
                        db.commit()
                        call_log(logger, description='Dont Recommend Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                        return { 'detail' : 'Dont recommend Post Updated' }             
                else:
                    raise HTTPException(status_code=400, detail='Add any Post to dont recommend')               
            else:
                print(post_uuid,1)
                db_add_dont_recomment=models.DontRecomment(user_uuid=user_uuid, post_uuid=post_uuid)           
                db.add(db_add_dont_recomment)
                db.commit()
                call_log(logger, description='Dont Recommend Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail' : 'Dont recommend Post Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_post_search')
def GetPostSearch(request:Request, text: str = Query(...), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        input = f'%{text}%'
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
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
                if db_dont_recommend.post_uuid:
                   db_dont_rec=db_dont_recommend.post_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Post").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_posts = db.query(models.Post).filter(models.Post.is_deleted == False, ~models.Post.user_uuid.in_(db_block), ~models.Post.uuid.in_(db_report), ~models.Post.uuid.in_(db_dont_rec), models.Post.caption.ilike(input)).order_by(func.random()).all() 
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
            for post in db_posts:
                if post.user_uuid in boosting_list:
                    post.boostingstatus = True
                else:
                    post.boostingstatus = False

                if post.user_uuid in request_list:
                    post.requeststatus = True
                else:
                    post.requeststatus = False
            
                db_p_user = db.query(models.User).filter(models.User.uuid == post.user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
                # if db_p_user.hashed_password and db_p_user.verification_code:
                #     del(db_p_user.hashed_password)
                #     del(db_p_user.verification_code)
                post.user_profile = db_p_user
                db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.post_uuid == post.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if post.tags:
                    for tag in post.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                post.tag_details = Tags
                post.comments = db_comments
                post.likes = db_likes  
                
            return { 'data' : { 'items': db_posts,'total': 1,'page':1,'size':1}  }
       
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')

    
@router.get('/get_my_posts')
def GetMyPosts(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_posts = db.query(models.Post).filter(models.Post.user_uuid == profile_uuid, models.Post.is_deleted == False).order_by(models.Post.created_at.desc()).all()
            if db_posts:
                for post in db_posts:
                    db_p_user = db.query(models.User).filter(models.User.uuid == post.user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
                    if db_p_user.hashed_password and db_p_user.verification_code:
                        del(db_p_user.hashed_password)
                        del(db_p_user.verification_code)
                    post.user_profile = db_p_user
                    db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post.uuid, models.Comment.is_deleted == False).all()
                    db_likes = db.query(models.Like).filter(models.Like.post_uuid == post.uuid, models.Like.is_liked == True).all()                  
                    Tags=[]
                    if post.tags:
                        for tag in post.tags:
                            db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                            Tags.append(db_tag)
                    post.tag_details = Tags
                    post.comments = db_comments
                    post.likes = db_likes
                return { 'data' : { 'items': db_posts,'total': 1,'page':1,'size':1}  }
            else:
                raise HTTPException(status_code=400, detail='No Posts yet')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_trending_posts')
def GetTrendingPosts(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_posts = db.query(models.Post).filter(models.Post.is_deleted == False).order_by(models.Post.like_count.desc()).all()
            for post in db_posts:
                db_p_user = db.query(models.User).filter(models.User.uuid == post.user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
                if db_p_user.hashed_password and db_p_user.verification_code:
                    del(db_p_user.hashed_password)
                    del(db_p_user.verification_code)
                post.user_profile = db_p_user
                db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.post_uuid == post.uuid, models.Like.is_liked == True).all()
                post.comments = db_comments
                post.likes = db_likes
            return { 'data' : db_posts[:10] }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_suggested_posts')
def GetSuggestedPosts(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
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
                if db_dont_recommend.post_uuid:
                   db_dont_rec=db_dont_recommend.post_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Post").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_posts = db.query(models.Post).filter(models.Post.is_deleted == False, ~models.Post.user_uuid.in_(db_block), ~models.Post.uuid.in_(db_report), ~models.Post.uuid.in_(db_dont_rec)).order_by(func.random()).all()
           
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
            for post in db_posts:
                if post.user_uuid in boosting_list:
                    post.boostingstatus = True
                else:
                    post.boostingstatus = False

                if post.user_uuid in request_list:
                    post.requeststatus = True
                else:
                    post.requeststatus = False
            
                db_p_user = db.query(models.User).filter(models.User.uuid == post.user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
                # if db_p_user.hashed_password and db_p_user.verification_code:
                #     del(db_p_user.hashed_password)
                #     del(db_p_user.verification_code)
                post.user_profile = db_p_user
                db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.post_uuid == post.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if post.tags:
                    for tag in post.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                post.tag_details = Tags
                post.comments = db_comments
                post.likes = db_likes  
                
            return { 'data' : paginate( db_posts, params) }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_post_by_id')
def GetPostbyID(request:Request, post_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
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
                if db_dont_recommend.post_uuid:
                   db_dont_rec=db_dont_recommend.post_uuid
            db_reports = db.query(models.Report).filter(models.Report.user_uuid == user_uuid, models.Report.media_type == "Post").all()
            if db_reports:
                for report in db_reports:
                   db_report.append(report.media_uuid)
            db_posts = db.query(models.Post).filter(models.Post.uuid == post_uuid, models.Post.is_deleted == False, ~models.Post.user_uuid.in_(db_block), ~models.Post.uuid.in_(db_report), ~models.Post.uuid.in_(db_dont_rec)).order_by(func.random()).all()
           
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
            for post in db_posts:
                if post.user_uuid in boosting_list:
                    post.boostingstatus = True
                else:
                    post.boostingstatus = False

                if post.user_uuid in request_list:
                    post.requeststatus = True
                else:
                    post.requeststatus = False
            
                db_p_user = db.query(models.User).filter(models.User.uuid == post.user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
                # if db_p_user.hashed_password and db_p_user.verification_code:
                #     del(db_p_user.hashed_password)
                #     del(db_p_user.verification_code)
                post.user_profile = db_p_user
                db_comments = db.query(models.Comment).filter(models.Comment.post_uuid == post.uuid, models.Comment.is_deleted == False).all()
                db_likes = db.query(models.Like).filter(models.Like.post_uuid == post.uuid, models.Like.is_liked == True).all()
                Tags=[]
                if post.tags:
                    for tag in post.tags:
                        db_tag = db.query(models.User.MID, models.User.uuid).filter(models.User.MID == tag, models.User.is_deleted == False, models.User.is_active == True).first()
                        Tags.append(db_tag)
                post.tag_details = Tags
                post.comments = db_comments
                post.likes = db_likes      
            return { 'data' : { 'items': db_posts,'total': 1,'page':1,'size':1}  }
            # else:
            #     raise HTTPException(status_code=400, detail='Post not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')