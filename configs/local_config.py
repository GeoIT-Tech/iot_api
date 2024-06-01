from configs.base_config import BaseConfig
from dotenv import load_dotenv
import os

load_dotenv('.env')

class Configuration(BaseConfig):
    DEBUG = True

    POSTGRES = {
        'user': os.environ.get('LOCAL_DB_USER'),
        'pw': os.environ.get('LOCAL_DB_PASSWORD'),
        'db': os.environ.get('LOCAL_DB_NAME'),
        'host': os.environ.get('LOCAL_DB_HOST'),
        'port': int(os.environ.get('LOCAL_DB_PORT')),
        'ssl': ''
        }


    DB_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)d/%(db)s?ssl_key=%(ssl)s' % POSTGRES
    
    Redirect_URL = ' '                      # mention the url to redirect from user_mail after verification
    

    AWS_ACCESS_KEY_ID = 'AKIAUEKOECNOSQGFIF2D'
    AWS_SECRET_ACCESS_KEY = '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'
    AWS_REGION = 'ap-south-1'
    AWS_VERIFICATION_BUCKET_NAME = 'menem-verification-documents'
    AWS_PROFILE_BUCKET_NAME = 'menem.profile'
    AWS_NEWSFEED_BUCKET_NAME = 'menem.newsfeed'
