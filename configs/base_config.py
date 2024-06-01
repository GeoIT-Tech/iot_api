import os

class BaseConfig(object):
    

    SECRET_KEY = 'ebb165ac9608f658c2082a2c70932d2c4257088a12d9e2cb7c3334f17d6fafbe'
    ALGORITHM = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES = 526000
    REFRESH_TOKEN_EXPIRE_MINUTES = 526000
    EMAIL_TOKEN_EXPIRE_MINUTES = 1440
    
    EmailOTP = 'EmailOTP'  # mention email_template to be sent by from_email to user for verification
    ResetPassword = 'ForgetPasswordOTP'

    From_Email = 'support@menem.in'