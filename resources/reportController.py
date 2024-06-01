from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger
from models.schemas import reportSchema
from sqlalchemy.orm import Session
from typing import Optional
from models import models, get_db
from jose import jwt, JWTError
from configs import BaseConfig
from uuid import UUID

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# @router.post('/profile_report')
# def PostReport(request: Request, reason_type: reportSchema.ReportProfileReasons, add: reportSchema.ProfileReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

# @router.post('/Report_media')
# def ReportMedia (request: Request, reason_type: str , media_type: str, reported_uuid: Optional[UUID] = None, media_uuid: Optional[UUID] = None, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Report).filter(models.Report.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Report(user_uuid=user_uuid,media_type=media_type, report_reason=reason_type, reported_uuid = reported_uuid, media_uuid = media_uuid)
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#             else:
#                 return {'detail': 'Not Reported'}
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

@router.post('/Report_media')
def ReportMedia (request: Request, add: reportSchema.Report_UUID = Depends(), db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_check = db.query(models.Report).filter( models.Report.media_type == add.media_type, models.Report.media_uuid == add.media_uuid,models.Report.user_uuid == user_uuid).first()
            # db_report = db.query(models.Report).filter(models.Report.user_uuid == user_uuid).first()
            if db_check:
                # db_check = db.query(models.Report).filter(models.Report.reported_uuid == add.reported_uuid, models.Report.media_type == add.media_type, models.Report.media_uuid == add.media_uuid, models.Report.report_reason == add.report_reason).first()
                # if db_check:
                #     db_check.reported_count = db_check.reported_count+1
                #     db.commit()
                # call_log(logger, description='Reported already', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                # return { 'detail' : 'Reported already' }
                raise HTTPException(status_code=400, detail='Reported already')
            else:
                db_add_report=models.Report(user_uuid=user_uuid, **add.dict())           
                db.add(db_add_report)
                db.commit()
            call_log(logger, description='Report Added', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail' : 'Report Added' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.post('/post_report')
# def PostReport(request: Request, reason_type: reportSchema.ReportPostReasons, add: reportSchema.PostReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#             #     db_add_report = models.Reports(user_uuid=user_uuid,reported_uuid = add.reported_uuid, post_uuid = add.post_uuid,report_reason=reason_type)
#             #     db.add(db_add_report)
#             #     news_feeds=[]
#             #     for news_feed in db_report.news_feed_report:
#             #         news_feeds.append(news_feed)
#             #     for news_fed in add.news_feed_report:
#             #         news_feeds.append(news_fed)
#             #     db_report.news_feed_report = news_feeds
#             #     db.commit()
#             #     call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#             #     return { 'detail' : 'Reported successfully' }
#             # else:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.post('/comment_report')
# def CommentReport(request: Request, reason_type: reportSchema.ReportPostReasons, add: reportSchema.CommentReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

# @router.post('/certificate_report')
# def CertificateReport(request: Request, reason_type: reportSchema.ReportPostReasons, add: reportSchema.CertificateReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')    

# # @router.post('/certificate_report')
# # def CertifficateReport(request: Request, add: reportSchema.CertificateReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
# #     try:
# #         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
# #         uuid: str = payload.get("sub")
# #         user_uuid = uuid
# #         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
# #         if db_user:
# #             db_report = db.query(models.Report).filter(models.Report.user_uuid == user_uuid).first()
# #             if db_report:
# #                 certificates=[]
# #                 for certificate in db_report.certificate_report:
# #                     certificates.append(certificate)
# #                 for certifcate in add.certificate_report:
# #                     certificates.append(certifcate)
# #                     db_report.certificate_report = certificates
# #                 db.commit()
# #                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
# #                 return { 'detail' : 'Reported' }
# #             else:
# #                 db_add_report = models.Report(user_uuid=user_uuid, **add.dict())
# #                 db.add(db_add_report)
# #                 db.commit()
# #                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
# #                 return { 'detail' : 'Reported' }
# #         else:
# #             raise HTTPException(status_code=400, detail='User not found')
# #     except JWTError:
# #         raise HTTPException(status_code=401, detail='Unauthorized')
    
# @router.post('/ebattle_report')
# def EBattleReport(request: Request, reason_type: reportSchema.ReportPostReasons, add: reportSchema.EBattleReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')  

# @router.post('/review_report')
# def ReviewReport(request: Request, reason_type: reportSchema.ReportPostReasons, add: reportSchema.ReviewReports, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_report = db.query(models.Reports).filter(models.Reports.user_uuid == user_uuid).first()
#             if db_report:
#                 db_add_report = models.Reports(user_uuid=user_uuid,report_reason=reason_type, **add.dict())
#                 db.add(db_add_report)
#                 db.commit()
#                 call_log(logger, description='Reported', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Reported' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized') 
    

# # @router.get('/get_my_reports')
# # def GetMyReports(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
# #     try:
# #         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
# #         uuid: str = payload.get("sub")
# #         user_uuid = uuid
# #         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
# #         if db_user:
# #             db_reports = db.query(models.Reports).filter(models.Reports.reported_uuid == user_uuid, models.Reports.post_uuid == db_posts.uuid, models.Reports.certificate_uuid == db_certificate.uuid ).all()
# #             if db_reports:
# #                 return { 'data' : db_reports }
# #             else:
# #                 raise HTTPException(status_code=400, detail='You dont have any reports till now')
# #         else:
# #             raise HTTPException(status_code=400, detail='User not found')
# #     except JWTError:
# #         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
# # @router.get('/get_my_report_by_id')
# # def GetMyReportbyID(report_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
# #     try:
# #         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
# #         uuid: str = payload.get("sub")
# #         user_uuid = uuid
# #         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
# #         if db_user:
# #             db_report = db.query(models.Report).filter(models.Report.reported_uuid == user_uuid, models.Report.uuid == report_uuid).first()
# #             if db_report:
# #                 return { 'data' : db_report }
# #             else:
# #                 raise HTTPException(status_code=400, detail='You can view only your reported content')
# #         else:
# #             raise HTTPException(status_code=400, detail='User not found')
# #     except JWTError:
# #         raise HTTPException(status_code=400, detail='Unauthorized')