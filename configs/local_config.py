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
