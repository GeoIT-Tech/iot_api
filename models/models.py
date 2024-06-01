from sqlalchemy import ARRAY, Boolean, Column, Date, ForeignKey, String, DateTime, LargeBinary, JSON, Text, Integer, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import datetime
from models import engine
import bcrypt
import uuid
from sqlalchemy.orm import sessionmaker, relationship

# Base = declarative_base(bind=engine)

class User(Base):

    __tablename__ = 'users'

    id =  Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    email = Column(String, unique=True)
    mobile = Column(String)
    is_active = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)