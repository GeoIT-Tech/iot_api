# from configs.base_config import BaseConfig
# from dotenv import load_dotenv
# import os

# load_dotenv('.env')

# class Configuration(BaseConfig):
#     DEBUG = True

#     POSTGRES = {
#         'user': os.environ.get('C_DB_USER'),
#         'pw': os.environ.get('C_DB_PASSWORD'),
#         'db': os.environ.get('C_DB_NAME'),
#         'host': os.environ.get('C_DB_HOST'),
#         'port': os.environ.get('C_DB_PORT'),
#         'port': int(os.environ.get('C_DB_PORT'))
#         }


#     # DB_URI_1= 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)d/%(db)s?ssl_key=%(ssl)s' % POSTGRES
    
#     # Redirect_URL = ' '                      # mention the url to redirect from user_mail after verification
    


# def postgres_test():

#     try:
#         conn = psycopg2.connect("dbname='mydb' user='myuser' host='my_ip' password='mypassword' connect_timeout=1 ")
#         conn.close()
#         return True
#     except:
#         return False