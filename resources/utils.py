from datetime import datetime, timedelta
from models import SessionLocal, models
import logging as custom_logging
from dotenv import load_dotenv
from configs import BaseConfig
import re, os, math, random
from typing import Optional
from jose import jwt
import smtplib
import os

load_dotenv('.env')

class LogDBHandler(custom_logging.Handler):
    '''
    Customized logging handler that puts logs to the database.
    '''
    def __init__(self):
        custom_logging.Handler.__init__(self)
        self.db_tbl_log = 'lms_log'

    def emit(self, record):
        if record.name == 'uvicorn.error':
            return None

        log_list = record.msg.split(',')
        log_instance = models.MeNeMLog()
        for key_value in log_list:
            key, value = key_value.split(':', 1)
            if not value:
                value = None
            setattr(log_instance, key, value)
        log_instance.module = record.name        
        db = SessionLocal()
        db.add(log_instance)
        db.commit()
        db.close()

def call_log(logger, description='', ip='', user_uuid='', status_code=200, api=''):
    logger.info('description:{description},ip:{ip},user_uuid:{user_uuid},status_code:{status_code},api:{api}'.format(
        description = description,
        ip = ip,
        user_uuid = user_uuid,
        status_code = status_code,
        api = api
    ))

def get_logger(module_name):
    handler_instance = LogDBHandler()
    custom_logging.getLogger('').addHandler(handler_instance)
    custom_logging.basicConfig(filename='log.txt')
    logger = custom_logging.getLogger(module_name)
    logger.setLevel('DEBUG')
    return logger

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire })
    encoded_jwt = jwt.encode(to_encode, BaseConfig.SECRET_KEY, algorithm=BaseConfig.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({'exp': expire })
    encoded_jwt = jwt.encode(to_encode, BaseConfig.SECRET_KEY, algorithm=BaseConfig.ALGORITHM)
    return encoded_jwt

def email_validator(email):                                 #to_validate_user-email
    regex = r'^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if(re.search(regex,email)):   
        return True  
    else:   
        False

def otp_code():
    digits="0123456789"
    OTP=""
    for i in range(6):
        OTP+=digits[math.floor(random.random()*10)]
    otp = OTP
    print(otp)
    return otp


def send_verification_email(username, to, subject, otp):
    try:
        text = 'Hi {},\nThank you for being associated with our MeNeM Social Networking Service. Use the following OTP to complete your account procedures.\n{}\nOTP is valid for 10 minutes, Our executives never ask you about one time password. In case you have not logged in to your account. please contact our customer service . You can also write an email at support@menem.in\nRegards,\nMeNeM'.format(username, otp)
        server = smtplib.SMTP(os.environ.get('SMTP_SERVER'), os.environ.get('SMTP_SERVER_NUM'))
        server.connect(os.environ.get('SMTP_SERVER'), os.environ.get('SMTP_SERVER_NUM'))
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(os.environ.get('SMTP_FROM'), os.environ.get('SMTP_APP_PASSWORD'))
        msg = 'Subject: {}\n\n{}'.format(subject, text)
        server.sendmail(os.environ.get('SMTP_FROM'), to, msg)
        server.quit()
        return { 'status': True }
    except Exception as e:
            print(str(e))
            return { 'status': False, 'error': {'message': 'Sending Mail Failed'}}


def send_forgetpassword_email(username, to, subject, otp):
    try:
        text = 'Hi {},\nThank you for being associated with our MeNeM Social Networking Service. Use the following OTP to reset your password.\n{}\nOTP is valid for 10 minutes, Our executives never ask you about one time password. In case you have not logged in to your account. please contact our customer service . You can also write an email at support@menem.in\nRegards,\nMeNeM'.format(username, otp)
        server = smtplib.SMTP(os.environ.get('SMTP_SERVER'), os.environ.get('SMTP_SERVER_NUM'))
        server.connect(os.environ.get('SMTP_SERVER'), os.environ.get('SMTP_SERVER_NUM'))
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(os.environ.get('SMTP_FROM'), os.environ.get('SMTP_APP_PASSWORD'))
        msg = 'Subject: {}\n\n{}'.format(subject, text)
        server.sendmail(os.environ.get('SMTP_FROM'), to, msg)
        server.quit()
        return { 'status': True }
    except Exception as e:
            print(str(e))
            return { 'status': False, 'error': {'message': 'Sending Mail Failed'}}


def common_elements(list1, list2):
    result = []
    for element in list1:
        if element in list2:
            result.append(element)
    return result

def mutual_list(db, request_uuid, user_uuid):
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
    return len(Mutuals)
