from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from resources.utils import call_log, get_logger, common_elements, mutual_list
from fastapi_pagination import paginate, Params
from models.schemas import boostSchema
from sqlalchemy.orm import Session
from models import models, get_db
from configs import BaseConfig
from jose import jwt, JWTError
from sqlalchemy import delete, or_, and_
from uuid import UUID

router = APIRouter()

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post('/send_request')
def SendRequest(request: Request, send: boostSchema.SendRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            if str(user_uuid)==str(send.receiver_uuid):
                raise HTTPException(status_code=400, detail='You cannot send request to your own Account')
            db_receiver = db.query(models.User).filter(models.User.uuid == send.receiver_uuid, models.User.is_deleted == False).first()
            if not db_receiver:
                raise HTTPException(status_code=400, detail='Receiver not available')
            db_sender = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == send.receiver_uuid, models.Boosts.sender_uuid==user_uuid).first()
            db_request = db.query(models.Boosts).filter(models.Boosts.sender_uuid == send.receiver_uuid,models.Boosts.receiver_uuid==user_uuid ).first()
            if db_sender:
                if db_sender.status=="Pending":                
                    raise HTTPException(status_code=400, detail='You have already sent request to this user')
                if db_sender.status=="Accepted":                
                    raise HTTPException(status_code=400, detail='You are already boosting this user')
                if db_sender.status=="Rejected":
                    db.execute(delete(models.Boosts).where(models.Boosts.receiver_uuid == send.receiver_uuid, models.Boosts.sender_uuid==user_uuid))
                    # db_update = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == send.receiver_uuid, models.Boosts.sender_uuid==user_uuid).first()
                    # db_update.status="Pending"
                    # db_update.receiver_uuid=user_uuid
                    # db_update.sender_uuid=send.receiver_uuid
                    db.commit()
                    db_send_request = models.Boosts(sender_uuid = user_uuid, receiver_uuid = send.receiver_uuid, status="Pending")
                    db.add(db_send_request)
                    db.commit()
            elif db_request:
                if db_request.status=="Pending":                
                    raise HTTPException(status_code=400, detail='They  already sent request to you')
                if db_request.status=="Accepted":                
                    raise HTTPException(status_code=400, detail='You are already boosting this user')
                if db_request.status=="Rejected":
                    db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == send.receiver_uuid,models.Boosts.receiver_uuid==user_uuid))
                    # db_update = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == send.receiver_uuid, models.Boosts.sender_uuid==user_uuid).first()
                    # db_update.status="Pending"
                    # db_update.receiver_uuid=user_uuid
                    # db_update.sender_uuid=send.receiver_uuid
                    db.commit()
                    db_send_request = models.Boosts(sender_uuid = user_uuid, receiver_uuid = send.receiver_uuid, status="Pending")
                    db.add(db_send_request)
                    db.commit()
            # elif db_send_request:
            #         db_send_request = models.Boosts(sender_uuid = send.receiver_uuid, status="Pending")
            #         raise HTTPException(status_code=400, detail='You cannot boost or unboost yourself')
            else:
                db_send_request = models.Boosts(sender_uuid = user_uuid, receiver_uuid = send.receiver_uuid, status="Pending")
                db.add(db_send_request)
                db.commit()
            call_log(logger, description='Boosting request sent', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
            return { 'detail' : 'Boosting request sent' } 
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get('/get_all_requests')
def GetAllRequests(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
        if db_user:
            db_requests = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid, models.Boosts.status=="Pending").order_by(models.Boosts.created_at.desc()).all()
            for sender in db_requests:
                db_sender = db.query(models.User).filter(models.User.uuid == sender.sender_uuid,models.User.is_deleted == False, models.User.is_active == True).first()
                del(db_sender.hashed_password)
                del(db_sender.verification_code)
                sender.sender_details = db_sender
            return { 'data' : db_requests }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_my_send_requests')
def GetMySentRequests(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_requests = db.query(models.Boosts).filter(models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Pending").order_by(models.Boosts.created_at.desc()).all()
            for receive in db_requests:
                db_receive = db.query(models.User).filter(models.User.uuid == receive.receiver_uuid,models.User.is_deleted == False, models.User.is_active == True).first()
                # del(db_sender.hashed_password)
                # del(db_sender.verification_code)
                receive.receiver_details = db_receive
            return { 'data' : db_requests }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post('/respond_request')
def RespondRequest(request: Request, sender_uuid: UUID,request_status:boostSchema.BoostStatus, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_request = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.sender_uuid==sender_uuid).first()
            if db_request:
                if db_request.status=="Accepted":                
                    raise HTTPException(status_code=400, detail='You are already boosting this user')
                if db_request.status=="Pending": 
                    db_request.status=request_status   
                    db.commit()
                    call_log(logger, description='Boosting Now', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
                    return { 'status' : request_status + " Now" }
            else:
                 raise HTTPException(status_code=400, detail='Request is not available')       
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.get("/get_boosting_list")
def GetBoostingList(request:Request, request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == request_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == request_uuid , models.Boosts.status=="Accepted").all()
            Boosting=[]
            boosting_uuids=[]
            if db_sender:
                for sender in db_sender:
                    db_boosting = db.query(models.User).filter(models.User.uuid == sender.receiver_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    if db_boosting:
                        boosting_uuids.append(sender.receiver_uuid)
                        Boosting.append(db_boosting)
            if db_receive:
                for receive in db_receive:
                    db_boosting = db.query(models.User).filter(models.User.uuid == receive.sender_uuid, models.User.is_deleted == False, models.User.is_active == True).first()
                    if db_boosting:
                        boosting_uuids.append(receive.sender_uuid)
                        Boosting.append(db_boosting)
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            boosting_my_list=[]
            for sender_id in db_sender:
                boosting_my_list.append(sender_id.receiver_uuid)
            for receive_id in db_receive:
                boosting_my_list.append(receive_id.sender_uuid)
            db_request = db.query(models.Boosts).filter( or_(models.Boosts.sender_uuid == user_uuid, models.Boosts.receiver_uuid == user_uuid), models.Boosts.status=="Pending").all()
            boosting_my_request_list=[]
            for request in db_request:
                boosting_my_request_list.append(request.sender_uuid)
                boosting_my_request_list.append(request.receiver_uuid)
            if Boosting:
                db_list=Boosting
                for boost in db_list:
                    if boost.uuid in boosting_my_list:
                        boost.boostingstatus = "Boosting"
                    elif boosting_my_request_list:
                        if boost.uuid in boosting_my_request_list:
                            boost.boostingstatus = "Pending"
                        else:
                            boost.boostingstatus = "Boost"
                    else:
                        boost.boostingstatus = "Boost"
                # db_list=Boosting
                # print(boosting_uuids)
                # print(db_user.uuid)
                # for boost in db_list:
                #     if boost.uuid in boosting_uuids:
                #        print("true")
                #     else:
                #        print("false")

                return { 'data' : db_list }
            else:
                raise HTTPException(status_code=400, detail="No boosting list found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.post("/remove_boosting")
def RemoveBoosting(request:Request, profile_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_sender = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == profile_uuid, models.Boosts.sender_uuid==user_uuid).first()
            db_receive = db.query(models.Boosts).filter(models.Boosts.sender_uuid == profile_uuid,models.Boosts.receiver_uuid==user_uuid ).first()
            if db_sender:
                 db.execute(delete(models.Boosts).where(models.Boosts.receiver_uuid == profile_uuid, models.Boosts.sender_uuid==user_uuid))
                 db.commit()
                 return { 'detail' : 'Boosting Removed' }
            elif db_receive:
                 db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == profile_uuid,models.Boosts.receiver_uuid==user_uuid))
                 db.commit()
                 return { 'detail' : 'Boosting Removed' }
            
            else:
                raise HTTPException(status_code=400, detail="No boosting found")
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')
    

@router.delete('/delete_boost_request')
def DeleteBoostRequest(request:Request, reciever_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_sender = db.query(models.User).filter(models.User.uuid == reciever_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
            if not db_sender:
                raise HTTPException(status_code=400, detail='Sender not available')
            else:
                db.execute(delete(models.Boosts).where(models.Boosts.sender_uuid == user_uuid, models.Boosts.receiver_uuid == reciever_uuid))
                db.commit()
            return { 'detail' : 'Boosting Removed' }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/mutual_boost_list')
def MutualBoostList(request:Request, request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_senders = db.query(models.Boosts).filter( models.Boosts.sender_uuid == request_uuid, models.Boosts.status=="Accepted").all()
            db_receives = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == request_uuid , models.Boosts.status=="Accepted").all()
            boosting_lists=[]
            for sender_ids in db_senders:
                boosting_lists.append(sender_ids.receiver_uuid)
            for receive_ids in db_receives:
                boosting_lists.append(receive_ids.sender_uuid)
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            boosting_list=[]
            for sender_id in db_sender:
                boosting_list.append(sender_id.receiver_uuid)
            for receive_id in db_receive:
                boosting_list.append(receive_id.sender_uuid)
            mutual_list = common_elements(boosting_list, boosting_lists)
            Mutuals = []
            for mutual in mutual_list:
                db_mutual = db.query(models.User).filter(models.User.uuid == mutual, models.User.is_deleted == False).first()
                ml = { 'user_uuid' : mutual, 'MID' : db_mutual.MID, 'Proile_Image' : db_mutual.profile_photo, 'Full_name' : db_mutual.fullname, 'Tagline' : db_mutual.tagline }
                Mutuals.append(ml)
            return { 'data' : Mutuals }
            # def common_elements(boosting_list, boosting_lists):
            #     print(1)
            #     return [element for element in boosting_list if element in boosting_lists]
            # return {'data1' : boosting_list , 'data2':  boosting_lists}
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/suggested_profiles')
def SuggestedProfiles(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid== user_uuid, models.User.is_deleted == False,  models.User.is_active == True).all()
        if db_user:
            db_block=[]
            db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
            if db_my_settings:
                if db_my_settings.blocked_account:
                    db_block=db_my_settings.blocked_account
            user=[]
            sender_uuid=[]
            reciever_uuid=[]
            db_profile = db.query(models.Boosts).filter(or_(models.Boosts.sender_uuid == user_uuid , models.Boosts.receiver_uuid == user_uuid), or_(models.Boosts.status == "Accepted",models.Boosts.status == "Pending")).all()
            for profile in db_profile:
               sender_uuid.append(profile.sender_uuid)
               reciever_uuid.append(profile.receiver_uuid)
            db_suggested_list= db.query(models.User).filter(models.User.uuid != user_uuid, ~models.User.uuid.in_(sender_uuid),~models.User.uuid.in_(db_block),~models.User.uuid.in_(reciever_uuid), models.User.is_deleted == False,  models.User.is_active == True).all()
            return { 'data' : db_suggested_list}
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get('/get_profile_details')
def GetProfileDetails(request:Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            del(db_user.hashed_password)
            del(db_user.verification_code)
            db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == user_uuid, models.Boosts.status=="Accepted").all()
            db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == user_uuid , models.Boosts.status=="Accepted").all()
            if db_sender:
                db_user.boosting_count = len(db_sender)
            elif db_receive:
                db_user.boosting_count = len(db_receive)       
            else:
                db_user.boosting_count = 0
            db_reviews = db.query(models.Review).filter(models.Review.user_uuid == user_uuid).all()
            if db_reviews:
                db_user.reviews = len(db_reviews)
                ratings=[]
                for reviews in db_reviews:
                    ratings.append(reviews.rating)
                db_user.ratings = (sum(ratings))/len(db_reviews)
            else:
                db_user.reviews = 0
                db_user.ratings = 0
            db_personals = db.query(models.Personal).filter(models.Personal.user_uuid == db_user.uuid, models.Personal.is_deleted == False).first()
            db_organizations = db.query(models.Organization).filter(models.Organization.user_uuid == db_user.uuid, models.Organization.is_deleted == False).first()
            db_institutes = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == db_user.uuid, models.EduInstitute.is_deleted == False).first()
            if db_personals:
                db_edu = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.user_uuid == user_uuid, models.PAEducationInfo.is_deleted == False).all()
                db_work = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.user_uuid == user_uuid, models.PAWorkInfo.is_deleted == False).all()
                db_project = db.query(models.PAProject).filter(models.PAProject.user_uuid == user_uuid, models.PAProject .is_deleted == False).all()
                db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == user_uuid, models.SocialLink.is_deleted == False).first()
                total_profile = len(vars(db_personals))
                not_completed = []
                if None in vars(db_personals).values():
                    not_completed.append(vars(db_personals).values())
                completed = (len(not_completed) - total_profile) * -1
                db_user.profile = db_personals
                db_user.edu_info = db_edu
                db_user.work_info = db_work
                db_user.project = db_project
                db_user.social_link = db_social_link
                db_user.percentage = round((completed/total_profile)*100, 2)
            elif db_organizations:
                db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == user_uuid, models.SocialLink.is_deleted == False).first()
                total_profile = len(vars(db_organizations))
                not_completed = []
                if None in vars(db_organizations).values():
                    not_completed.append(vars(db_organizations).values())
                completed = (len(not_completed) - total_profile) * -1
                db_user.profile = db_organizations
                db_user.social_link = db_social_link
                db_user.percentage = round((completed/total_profile)*100, 2)
            elif db_institutes:
                db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == user_uuid, models.SocialLink.is_deleted == False).first()
                total_profile = len(vars(db_institutes))
                not_completed = []
                if None in vars(db_institutes).values():
                    not_completed.append(vars(db_institutes).values())
                completed = (len(not_completed) - total_profile) * -1
                db_user.profile = db_institutes
                db_user.social_link = db_social_link
                db_user.percentage = round((completed/total_profile)*100, 2)
            return { 'data' : db_user }
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


@router.get("/get_user_profile")
def GetUserProfile(request:Request, request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
        uuid: str = payload.get("sub")
        user_uuid = uuid
        db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
        if db_user:
            db_profile = db.query(models.User).filter(models.User.uuid == request_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
            if db_profile:
                db_settings = db.query(models.Setting).filter(models.Setting.user_uuid == request_uuid).first()
                del(db_profile.hashed_password)
                del(db_profile.verification_code)
                db_sender = db.query(models.Boosts).filter( models.Boosts.sender_uuid == request_uuid, models.Boosts.status=="Accepted").all()
                db_receive = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == request_uuid , models.Boosts.status=="Accepted").all()
                boosting_list=[]
                for sender_id in db_sender:
                    boosting_list.append(sender_id.receiver_uuid)
                for receive_id in db_receive:
                    boosting_list.append(receive_id.sender_uuid)
                if db_user.uuid in boosting_list:
                    db_profile.boostingstatus = True
                else:
                    db_profile.boostingstatus = False
                if boosting_list:
                    db_profile.boosting_count=len(boosting_list)
                else:
                     db_profile.boosting_count=0
                if db_profile.boostingstatus==False:
                    db_profile.is_protected=db_profile.is_protected
                    # this is for if login user recevice request from requested uuid
                    db_sender_request = db.query(models.Boosts).filter(models.Boosts.sender_uuid == request_uuid,models.Boosts.receiver_uuid==user_uuid, models.Boosts.status=="Pending").first()
                    # this is for if login user send request to requested uuid
                    db_receive_request = db.query(models.Boosts).filter(models.Boosts.receiver_uuid == request_uuid ,models.Boosts.sender_uuid==user_uuid, models.Boosts.status=="Pending").first()
                    if db_sender_request:
                        db_profile.boosting_request = "Requested" #show Accept or reject button
                    elif db_receive_request:
                        db_profile.boosting_request = "Pending" # show Pending button 
                    else:
                        db_profile.boosting_request = "Boost" # not connected
                else:
                        db_profile.is_protected=False
                        db_profile.boosting_request = "Boosting" # Already connected
                db_reviews = db.query(models.Review).filter(models.Review.reviewer_uuid == request_uuid).all()
                if db_reviews:
                    db_profile.reviews = len(db_reviews)
                    ratings=[]
                    for reviews in db_reviews:
                        ratings.append(reviews.rating)
                    average = (sum(ratings))/len(db_reviews)
                    
                    db_profile.ratings = round(average, 1)
                else:
                    db_profile.reviews = 0
                    db_profile.ratings = 0
                db_personals = db.query(models.Personal).filter(models.Personal.user_uuid == db_profile.uuid, models.Personal.is_deleted == False).first()
                db_organizations = db.query(models.Organization).filter(models.Organization.user_uuid == db_profile.uuid, models.Organization.is_deleted == False).first()
                db_institutes = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == db_profile.uuid, models.EduInstitute.is_deleted == False).first()
                if db_personals:
                    db_profile.location=db_personals.location
                    db_edu = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.user_uuid == request_uuid, models.PAEducationInfo.is_deleted == False).all()
                    db_work = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.user_uuid == request_uuid, models.PAWorkInfo.is_deleted == False).all()
                    db_project = db.query(models.PAProject).filter(models.PAProject.user_uuid == request_uuid, models.PAProject .is_deleted == False).all()
                    db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
                    db_profile.profile = db_personals
                    db_profile.edu_info = db_edu
                    db_profile.work_info = db_work
                    db_profile.project = db_project
                    db_profile.social_link = db_social_link
                elif db_organizations:
                    db_profile.location=db_organizations.location
                    db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
                    db_profile.profile = db_organizations
                    db_profile.social_link = db_social_link
                elif db_institutes:
                    db_profile.location=db_institutes.location
                    db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
                    db_profile.profile = db_institutes
                    db_profile.social_link = db_social_link
                #need to remove here - protected issues
                # if db_settings and db_settings.protect_account:
                #     db_profile.protected = True
                # else:
                #     db_profile.protected = False
                db_my_settings = db.query(models.Setting).filter(models.Setting.user_uuid == user_uuid).first()
                if db_my_settings:
                   if db_my_settings.blocked_account:
                       if str(request_uuid) in db_my_settings.blocked_account:
                          db_profile.boosting_request = "Blocked"
                          db_profile.blocked = True
                       else:
                          db_profile.blocked = False                     
                else:
                    db_profile.blocked = False
                db_requestor_settings = db.query(models.Setting).filter(models.Setting.user_uuid == request_uuid).first()
                if db_requestor_settings:
                   if db_requestor_settings.blocked_account:
                       if str(user_uuid) in db_requestor_settings.blocked_account:
                          db_profile.boosting_request = "Blocked"
                          db_profile.blocked = True
                       else:
                          db_profile.blocked = False                     
                else:
                    db_profile.blocked = False
                db_posts = db.query(models.Post).filter(models.Post.is_deleted == False, models.Post.user_uuid == request_uuid).all()
                if db_posts:
                    db_profile.posts_count = len(db_posts)
                else:
                    db_profile.posts_count = 0
                if mutual_list:
                    db_profile.mutual_count = mutual_list(db, request_uuid, user_uuid)
                else:
                    db_profile.mutual_count = 0
                return { 'data' : db_profile }
            else:
                raise HTTPException(status_code=400, detail='Profile not found')
        else:
            raise HTTPException(status_code=400, detail='User not found')
    except JWTError:
        raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get('/get_profile_by_id')
# def GetProfilebyID(request:Request, request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
#         if db_user:
#             db_profile = db.query(models.User).filter(models.User.uuid == request_uuid, models.User.is_deleted == False,  models.User.is_active == True).first()
#             db_personals = db.query(models.Personal).filter(models.Personal.user_uuid == db_profile.uuid, models.Personal.is_deleted == False).first()
#             db_organizations = db.query(models.Organization).filter(models.Organization.user_uuid == db_profile.uuid, models.Organization.is_deleted == False).first()
#             db_institutes = db.query(models.EduInstitute).filter(models.EduInstitute.user_uuid == db_profile.uuid, models.EduInstitute.is_deleted == False).first()
#             if db_personals:
#                 db_edu = db.query(models.PAEducationInfo).filter(models.PAEducationInfo.user_uuid == request_uuid, models.PAEducationInfo.is_deleted == False).all()
#                 db_work = db.query(models.PAWorkInfo).filter(models.PAWorkInfo.user_uuid == request_uuid, models.PAWorkInfo.is_deleted == False).all()
#                 db_project = db.query(models.PAProject).filter(models.PAProject.user_uuid == request_uuid, models.PAProject .is_deleted == False).all()
#                 db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
#                 db_profile.profile = db_personals
#                 db_profile.edu_info = db_edu
#                 db_profile.work_info = db_work
#                 db_profile.project = db_project
#                 db_profile.social_link = db_social_link
#             elif db_organizations:
#                 db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
#                 db_profile.profile = db_organizations
#                 db_profile.social_link = db_social_link
#             elif db_institutes:
#                 db_social_link = db.query(models.SocialLink).filter(models.SocialLink.user_uuid == request_uuid, models.SocialLink.is_deleted == False).first()
#                 db_profile.profile = db_institutes
#                 db_profile.social_link = db_social_link
#             db_settings = db.query(models.Setting).filter(models.Setting.user_uuid == request_uuid).first()
#             del(db_profile.hashed_password)
#             del(db_profile.verification_code)
#             if db_settings and db_settings.protect_account:
#                 db_profile.protected = True
#             else:
#                 db_profile.protected = False
#             db_suggested_list= db.query(models.User).filter(models.User.uuid == request_uuid, models.User.is_deleted == False,  models.User.is_active == True).all() 
#             return { 'data' : db_suggested_list}    
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=400, detail='Unauthorized')


# @router.post('/send_request')
# def SendRequest(request: Request, send: boostSchema.SendRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_receiver = db.query(models.User).filter(models.User.uuid == send.receiver_uuid, models.User.is_deleted == False).first()
#             if not db_receiver:
#                 raise HTTPException(status_code=400, detail='Receiver not available')
#             db_request = db.query(models.BoostRequest).filter(models.BoostRequest.receiver_uuid == send.receiver_uuid).first()
#             if db_request:                
#                 raise HTTPException(status_code=400, detail='You have already sent request to this user')
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid).first()
#             if db_boost:
#                 if db_boost.boosting_uuid:
#                     if str(send.receiver_uuid) in db_boost.boosting_uuid:
#                         raise HTTPException(status_code=400, detail='You are already boosting this user')
#             db_protected = db.query(models.Setting).filter(models.Setting.user_uuid == send.receiver_uuid).first()
#             if db_protected and db_protected.protect_account == True:
#                     db_send_request = models.BoostRequest(sender_uuid = user_uuid, receiver_uuid = send.receiver_uuid)
#                     db.add(db_send_request)
#                     db.commit()
#                     call_log(logger, description='Boosting request sent', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                     return { 'detail' : 'Boosting request sent' } 
#             else:
#                 db_r_boost = db.query(models.Boost).filter(models.Boost.user_uuid == send.receiver_uuid).first()
#                 db_s_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid).first()
#                 r_boosts=[]
#                 s_boosts=[]
#                 if db_s_boost and db_s_boost.boosting_uuid:
#                     for boost in db_s_boost.boosting_uuid:
#                         s_boosts.append(boost)
#                     s_boosts.append(send.receiver_uuid)
#                     db_s_boost.boosting_uuid = s_boosts
#                     db_s_boost.boosting_count = len(s_boosts)
#                     db.commit()
#                 else:
#                     db_add_boost = models.Boost(user_uuid=user_uuid)
#                     db.add(db_add_boost)
#                     db.commit()
#                     db.refresh(db_add_boost)
#                     s_boosts.append(send.receiver_uuid)
#                     db_add_boost.boosting_uuid = s_boosts
#                     db_add_boost.boosting_count = len(s_boosts)
#                     db.commit()
#                 if db_r_boost and db_r_boost.booster_uuid:
#                     for boost in db_r_boost.booster_uuid:
#                         r_boosts.append(boost)
#                     r_boosts.append(user_uuid)
#                     db_r_boost.booster_uuid = r_boosts
#                     db_r_boost.booster_count = len(r_boosts)
#                     db.commit()
#                 else:
#                     db_add_boost = models.Boost(user_uuid=send.receiver_uuid)
#                     db.add(db_add_boost)
#                     db.commit()
#                     db.refresh(db_add_boost)
#                     r_boosts.append(user_uuid)
#                     db_add_boost.booster_uuid = r_boosts
#                     db_add_boost.booster_count = len(r_boosts)
#                     db.commit()
#                 call_log(logger, description='Boosting Now', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#                 return { 'detail' : 'Boosting Now' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.get('/get_all_requests')
# def GetAllRequests(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_requests = db.query(models.BoostRequest).filter(models.BoostRequest.receiver_uuid == user_uuid).order_by(models.BoostRequest.created_at.desc()).all()
#             for sender in db_requests:
#                 db_sender = db.query(models.User).filter(models.User.uuid == sender.sender_uuid,models.User.is_deleted == False).first()
#                 del(db_sender.hashed_password)
#                 del(db_sender.verification_code)
#                 sender.sender_details = db_sender
#             return { 'data' : db_requests }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    

# @router.post('/accept_request')
# def AcceptRequest(request: Request, sender_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_receiver = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#             db_sender = db.query(models.User).filter(models.User.uuid == sender_uuid, models.User.is_deleted == False).first()
#             if not db_sender:
#                 raise HTTPException(status_code=400, detail='Sender not available')
#             db_r_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid).first()
#             db_s_boost = db.query(models.Boost).filter(models.Boost.user_uuid == sender_uuid).first()
#             r_boosts=[]
#             s_boosts=[]
#             if db_s_boost and db_s_boost.boosting_uuid:
#                 for boost in db_s_boost.boosting_uuid:
#                     s_boosts.append(boost)
#                 s_boosts.append(user_uuid)
#                 db_s_boost.boosting_uuid = s_boosts
#                 db_s_boost.boosting_count = len(s_boosts)
#                 db.commit()
#             else:
#                 db_add_boost = models.Boost(user_uuid=sender_uuid)
#                 db.add(db_add_boost)
#                 db.commit()
#                 db.refresh(db_add_boost)
#                 s_boosts.append(user_uuid)
#                 db_add_boost.boosting_uuid = s_boosts
#                 db_add_boost.boosting_count = len(s_boosts)
#                 db.commit()
#             if db_r_boost and db_r_boost.booster_uuid:
#                 for boost in db_r_boost.booster_uuid:
#                     r_boosts.append(boost)
#                 r_boosts.append(sender_uuid)
#                 db_r_boost.booster_uuid = r_boosts
#                 db_r_boost.booster_count = len(r_boosts)
#                 db.commit()
#             else:
#                 db_add_boost = models.Boost(user_uuid=user_uuid )
#                 db.add(db_add_boost)
#                 db.commit()
#                 db.refresh(db_add_boost)
#                 r_boosts.append(sender_uuid)
#                 db_add_boost.booster_uuid = r_boosts
#                 db_add_boost.booster_count = len(r_boosts)
#                 db.commit()
#             db.execute(delete(models.BoostRequest).where(models.BoostRequest.sender_uuid == sender_uuid, models.BoostRequest.receiver_uuid == user_uuid))
#             db.commit()
#             call_log(logger, description='Boosting Now', user_uuid=user_uuid, status_code=200, api=request.url.path, ip=request.client.host)
#             return { 'detail' : 'Boosting Now' }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')
    
    
# @router.get('/suggested_profiles')
# def SuggestedProfiles(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme), params: Params = Depends()):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).all()
#         if db_user:
#             boosts = []
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid).first()
#             if db_boost and db_boost.boosting_uuid:
#                 for boost in db_boost.boosting_uuid:
#             # if db_boost and db_boost.boosting_uuid and boost.booster_uuid and mutual_account:
#             #     for boost in db_boost.boosting_uuid:
#             #     for boost in db_boost.booster_uuid:
#             #     for boost in db_boost.mutual_account:
#                     db_suggested_profile = db.query(models.Boost).filter(models.Boost.user_uuid == boost).first()
#                     boosts.append(db_suggested_profile)
#             return { 'data' : paginate(boosts, params) }
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')

    
# @router.delete('/delete_boost_request')
# def DeleteBoostRequest(sender_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_sender = db.query(models.User).filter(models.User.uuid == sender_uuid, models.User.is_deleted == False).first()
#             if not db_sender:
#                 raise HTTPException(status_code=400, detail='Sender not available')
#             db.execute(delete(models.BoostRequest).where(models.BoostRequest.sender_uuid == sender_uuid, models.BoostRequest.receiver_uuid == user_uuid))
#             db.commit()
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_boosting_list")
# def GetBoostingList(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.boosting_uuid != None).first()
#             Boosting=[]
#             if db_boost and db_boost.boosting_uuid:
#                 for boosting_uuid in db_boost.boosting_uuid:
#                     db_boosting = db.query(models.User).filter(models.User.uuid == boosting_uuid, models.User.is_deleted == False).first()
#                     if db_boosting:
#                         del(db_boosting.hashed_password)
#                         del(db_boosting.verification_code)
#                     Boosting.append(db_boosting)
#                 return { 'data' : Boosting }
#             else:
#                 raise HTTPException(status_code=400, detail="No boosting list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_other_boosting_list")
# def GetOtherBoostingList(request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == request_uuid, models.Boost.boosting_uuid != None).first()
#             Boosting=[]
#             if db_boost and db_boost.boosting_uuid:
#                 for boosting_uuid in db_boost.boosting_uuid:
#                     db_boosting = db.query(models.User).filter(models.User.uuid == boosting_uuid, models.User.is_deleted == False).first()
#                     if db_boosting:
#                         del(db_boosting.hashed_password)
#                         del(db_boosting.verification_code)
#                     Boosting.append(db_boosting)
#                 return { 'data' : Boosting }
#             else:
#                 raise HTTPException(status_code=400, detail="No boosting list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_booster_list")
# def GetBoosterList(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.booster_uuid != None).first()
#             Booster=[]
#             if db_boost and db_boost.booster_uuid:
#                 for booster_uuid in db_boost.booster_uuid:
#                     db_booster = db.query(models.User).filter(models.User.uuid == booster_uuid, models.User.is_deleted == False).first()
#                     if db_booster:
#                         del(db_booster.hashed_password)
#                         del(db_booster.verification_code)
#                     Booster.append(db_booster)
#                 return { 'data' : Booster }
#             else:
#                 raise HTTPException(status_code=400, detail="No booster list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.get("/get_other_booster_list")
# def GetOtherBoosterList(request_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.booster_uuid != None).first()
#             Booster=[]
#             if db_boost and db_boost.booster_uuid:
#                 for booster_uuid in db_boost.booster_uuid:
#                     db_booster = db.query(models.User).filter(models.User.uuid == booster_uuid, models.User.is_deleted == False).first()
#                     if db_booster:
#                         del(db_booster.hashed_password)
#                         del(db_booster.verification_code)
#                     Booster.append(db_booster)
#                 return { 'data' : Booster }
#             else:
#                 raise HTTPException(status_code=400, detail="No booster list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')


# @router.post("/remove_booster")
# def RemoveBooster(booster_uuid: UUID, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, BaseConfig.SECRET_KEY, algorithms=[BaseConfig.ALGORITHM])
#         uuid: str = payload.get("sub")
#         user_uuid = uuid
#         db_user = db.query(models.User).filter(models.User.uuid == user_uuid, models.User.is_deleted == False).first()
#         if db_user:
#             db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.booster_uuid != None).first()
#             if db_boost and db_boost.booster_uuid:
#                 Booster=db_boost.booster_uuid
#                 if str(booster_uuid) in Booster:
#                     Booster.remove(str(booster_uuid))
#                     db_boost.booster_uuid = Booster
#                     db.commit()
#                     db_boost.booster_uuid = Booster
#                     db.commit()
#                     if len(db_boost.booster_uuid) == 0:
#                         db_boost = db.query(models.Boost).filter(models.Boost.user_uuid == user_uuid, models.Boost.boosting_uuid == None).delete()
#                         db.commit()
#                     return { 'detail' : 'Booster Removed' }
#                 else:
#                     raise HTTPException(status_code=400, detail="User not a booster")
#             else:
#                 raise HTTPException(status_code=400, detail="No booster list found")
#         else:
#             raise HTTPException(status_code=400, detail='User not found')
#     except JWTError:
#         raise HTTPException(status_code=401, detail='Unauthorized')