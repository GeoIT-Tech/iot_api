from configs.base_config import BaseConfig
from dotenv import load_dotenv
import os

load_dotenv('.env')

class Configuration(BaseConfig):
    DEBUG = True

    POSTGRES = {
        'user': os.environ.get('DB_USER'),
        'pw': os.environ.get('DB_PASSWORD'),
        'db': os.environ.get('DB_NAME'),
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'port': int(os.environ.get('DB_PORT')),
        'ssl': ''
        }


    DB_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)d/%(db)s?ssl_key=%(ssl)s' % POSTGRES
    
    Redirect_URL = ' '                      # mention the url to redirect from user_mail after verification
    