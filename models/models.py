from sqlalchemy import ARRAY, Boolean, Column, Date, ForeignKey, String, DateTime, LargeBinary, JSON, Text, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import datetime
from models import engine
import bcrypt
import uuid
from sqlalchemy.orm import sessionmaker, relationship
Base = declarative_base(bind=engine)


class User(Base):

    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    name = Column(String)
    signup_type = Column(String)
    email = Column(String, unique=True)
    dial_code = Column(String)
    mobile = Column(String, unique=True)
    hashed_password = Column(LargeBinary)
    verification_code = Column(JSON)
    house_name = Column(String)
    mac_address = Column(String)
    ip_address = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    delete_reason = Column(String)
    profile_photo = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    deleted_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    def hash_password(self, password):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
        print(self.hashed_password)

    def verify_password(self, password):
        if bcrypt.checkpw(password.encode('utf8'), self.hashed_password):
            return True
        else:
            return False

class ResetPasswordCode(Base):
    
    __tablename__ = 'reset_password_code'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    verification_code = Column(JSON)
    consumed = Column(Boolean, default=False)
    expired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class ViLog(Base):
    
    __tablename__ = 'vi_logs'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid') )
    ip = Column(Text)
    module = Column(String)
    status_code = Column(Integer, default=200)
    description = Column(Text)
    api = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  
        
# Base.metadata.create_all(bind=engine)