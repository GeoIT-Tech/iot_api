from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from models.schemas import reviewSchema
from sqlalchemy.orm import Session
from sqlalchemy import delete , func
from models import models, get_db
from configs import BaseConfig
from jose import jwt, JWTError
from datetime import datetime
from uuid import UUID

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

@router.post('/add_review')
def AddReview(request: Request, add: reviewSchema.Reviews, hashtag: list[str]  = Query(None), tags: list[str]  = Query(None), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if str(add.reviewer_uuid) == str(user_uuid):
                raise HTTPException(status_code=400, detail='You didnt Review yourself')
            db_review = db.query(models.Review).filter(models.Review.user_uuid == user_uuid, models.Review.reviewer_uuid == add.reviewer_uuid, models.Review.is_deleted == False).first()
            if db_review:
                db_review.reviewer_uuid = add.reviewer_uuid
                db_review.review = add.review
                db_review.rating = add.rating
                if hashtag and ',' in hashtag[0]:
                    hashtag = hashtag[0].split(", ")
                if tags and ',' in tags[0]:
                    tags = tags[0].split(", ")
                if tags:
                    db_review.tags=tags
                db_review.hashtags=hashtag
                db.commit()
                call_log(logger, description='Review Updated', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail': 'Review Updated' }
            else:
                if hashtag and ',' in hashtag[0]:
                    hashtag = hashtag[0].split(", ")
                if tags and ',' in tags[0]:
                    tags = tags[0].split(", ")
                db_add_review = models.Review(**add.dict(), user_uuid = user_uuid, tags=tags, hashtags = hashtag)
                db.add(db_add_review)
                db.commit()
                call_log(logger, description='Review Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail': 'Review Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.patch('/delete_review')
def DeleteReview(request: Request, review_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_review = db.query(models.Review).filter(models.Review.uuid == review_uuid).first()
            if db_review:
                db_admin = db.query(models.Review).filter(models.Review.uuid == review_uuid, models.Review.user_uuid == user_uuid).first()
                if db_admin:
                    db_review.is_deleted = True
                    db.commit()
                    call_log(logger, description='Review deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'detail': 'Review deleted' }
                else:
                    raise HTTPException(status_code=400, detail='You can only delete review created by you')
            else:
                    raise HTTPException(status_code=400, detail='Review not found') 
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.patch('/review_reply')
def ReviewReply(request: Request, review_uuid: UUID, add: reviewSchema.Reply, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_admin = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_admin:
            db_review = db.query(models.Review).filter(models.Review.uuid == review_uuid, models.Review.reviewer_uuid == user_uuid).first()
            if db_review:
                db_review.reply = add.reply
                db_review.replied_at = datetime.utcnow()
                db.commit()
                call_log(logger, description='Reply Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                return { 'detail': 'Reply Added' }
            else:
               raise HTTPException(status_code=400, detail='You can reply only to your reviews') 
        else:
            raise HTTPException(status_code=400, detail='Only Admin can reply reviews')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

# @router.patch('/delete_reply')
# def DeleteReply(request: Request, review_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_user:
#             db_review = db.query(models.Review).filter(models.Review.uuid == review_uuid).first()
#             if db_review:
#                 db_reply = db.query(models.Review).filter(models.Review.uuid == review_uuid, models.Review.reviewer_uuid == user_uuid).first()
#                 if db_reply:
#                     db.execute(delete(models.Review).where(models.Review.reply == db_reply.reply))
#                     db.commit()
#                     call_log(logger, description='Reply deleted', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail': 'Reply deleted' }
#                 else:
#                     raise HTTPException(status_code=400, detail='You can only delete reply created by you')
#             else:
#                     raise HTTPException(status_code=400, detail='Reply not found') 
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.patch('/report_reply')
# def ReportReply(request: Request, review_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_admin = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
#         if db_admin:
#             db_review = db.query(models.Review).filter(models.Review.uuid == review_uuid).first()
#             if db_review:
#                 db_review.is_reported = True
#                 db_review.reported_at = datetime.utcnow()
#                 db.commit()
#                 call_log(logger, description='Review reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail': 'Review reported' }
#             else:
#                raise HTTPException(status_code=400, detail='Review not found') 
#         else:
#             raise HTTPException(status_code=400, detail='Report Failed')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/get_all_reviews')
def GetAllReviews(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            if db_user.category == "Personal":
                return { 'detail': 'Individual user dont get review details' }
            else: #report review removed in db_review
                db_reviews = db.query(models.Review).filter(models.Review.reviewer_uuid == user_uuid, models.Review.is_deleted == False).order_by(models.Review.created_at.asc()).all() 
                for reviews in db_reviews:
                    db_reviewer = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    # del(db_reviewer.hashed_password)
                    # del(db_reviewer.verification_code)
                    reviews.reviewer = db_reviewer
                return { 'data' : db_reviews }  
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')

@router.get('/get_user_reviews')
def GetUserReviews(request:Request, reviewer_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_reviews = db.query(models.Review).filter(models.Review.reviewer_uuid == reviewer_uuid, models.Review.is_deleted == False).order_by(func.random()).all()
            if db_reviews:    
                for reviews in db_reviews:
                    db_users = db.query(models.User).filter(models.User.uuid == reviews.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    db_reviewer = db.query(models.User).filter(models.User.uuid == reviews.reviewer_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    # if db_reviewer.hashed_password and db_reviewer.verification_code:
                    # del(db_reviewer.hashed_password)
                    # del(db_reviewer.verification_code)
                    reviews.reviewer_detail = db_reviewer
                    reviews.user_detail = db_users
                return { 'data' : db_reviews }  
            else:
                raise HTTPException(status_code=400, detail='Review not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_review_by_id')
def GetReviewbyID(request:Request, review_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_reviews = db.query(models.Review).filter(models.Review.uuid == review_uuid, models.Review.is_deleted == False).first()
            if db_reviews:
                db_users = db.query(models.User).filter(models.User.uuid == db_reviews.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                db_reviewer = db.query(models.User).filter(models.User.uuid == db_reviews.user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                db_reviews.reviewer_detail = db_reviewer
                db_reviews.user_detail = db_users
                return { 'data' : db_reviews }
            else:
                raise HTTPException(status_code=400, detail='Ebattles not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=400, detail='Unauthorized')