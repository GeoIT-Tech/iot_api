import os

class BaseConfig(object):
    

    SECRET_KEY = '469c2c6bad1e9e0fb2b4aba3e445567733cec9185dd0df274471683ede3702c0'
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 526000
    REFRESH_TOKEN_EXPIRE_MINUTES = 526000
    EMAIL_TOKEN_EXPIRE_MINUTES = 1440
    
    EmailOTP = 'EmailOTP'  # mention email_template to be sent by from_email to user for verification
    ResetPassword = 'ForgetPasswordOTP'

    From_Email = 'geoit.techy@gmail.com'