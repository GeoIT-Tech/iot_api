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
    category = Column(String)
    fullname = Column(String)
    MID = Column(String, unique=True)
    signup_type = Column(String)
    email = Column(String, unique=True)
    dial_code = Column(String)
    mobile = Column(String, unique=True)
    hashed_password = Column(LargeBinary)
    verification_code = Column(JSON)
    tagline = Column(String)
    about = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_protected = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    delete_reason = Column(String)
    delete_comment = Column(String)
    detail = Column(JSON)
    profile_photo = Column(String)
    cover_image = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    def hash_password(self, password):
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
        print(self.hashed_password)

    def verify_password(self, password):
        if bcrypt.checkpw(password.encode('utf8'), self.hashed_password):
            return True
        else:
            return False
    
class Personal(Base):
    
    __tablename__ = 'personals'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    location = Column(String)
    title = Column(String)
    DOB = Column(Date)
    pronounce = Column(String)
    skills = Column(ARRAY(String))
    contact_us = Column(JSON)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class PAEducationInfo(Base):

    __tablename__ = 'pa_education_info'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    institute_name = Column(String)
    degree = Column(String)
    specialization = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    description = Column(String)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class PAWorkInfo(Base):

    __tablename__ = 'pa_work_info'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    designation = Column(String)
    company_name = Column(String)
    industry = Column(String)
    location = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    roles_responsibilities = Column(String)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class PAProject(Base):

    __tablename__ = 'pa_projects'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    name = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    url = Column(String)
    description = Column(String)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class SocialLink(Base):

    __tablename__ = 'social_links'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    facebook = Column(String)
    instagram = Column(String)
    youtube = Column(String)
    twitter = Column(String)
    linkedin = Column(String)
    threads = Column(String)
    discord = Column(String)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class Organization(Base):
    
    __tablename__ = 'organizations'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    organization_type = Column(String)
    location = Column(String)
    industry = Column(String)
    website = Column(String)
    contact_us = Column(JSON)
    company_size = Column(String)
    head_quaters = Column(String)
    established_year = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class EduInstitute(Base):
    
    __tablename__ = 'eduinstitutes'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    institute_type = Column(String)
    location = Column(String)
    website = Column(String)
    contact_us = Column(JSON)
    established_year = Column(Integer)
    ranking = Column(String)
    recognised_by = Column(String)
    strength = Column(Integer)
    academic_facilities = Column(String)
    course_url = Column(String)
    admission_url = Column(String)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
      
    
class EIAdmissionDetail(Base):
    
    __tablename__ = 'ei_admission_details'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    edu_institute_uuid = Column(UUID(as_uuid=True), ForeignKey('eduinstitutes.uuid'))
    detail = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    course_title = Column(String)
    academic_year = Column(String)
    admission_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class EIProgramOffer(Base):
    
    __tablename__ = 'ei_program_offers'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    edu_institute_uuid = Column(UUID(as_uuid=True), ForeignKey('eduinstitutes.uuid'))
    detail = Column(String)
    no_of_seat = Column(Integer)
    course_year = Column(String)
    course_mode = Column(String)
    document_link = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)


class EIPlacementPartner(Base):
    
    __tablename__ = 'ei_placement_partner'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    placement_partner_description = Column(String)
    placement_partner_id = Column(ARRAY(UUID(as_uuid=True)))
    edu_institute_uuid = Column(UUID(as_uuid=True), ForeignKey('eduinstitutes.uuid'))
       
    
class Verification(Base):
    
    __tablename__ = 'verifications'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    full_name = Column(String)
    country = Column(String)
    category = Column(String)
    document_type = Column(String)
    document_url = Column(String)
    status = Column(String)
    status_note = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class Report(Base):
    
    __tablename__ = 'reports'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    MID = Column(String, ForeignKey('users.MID'))
    media_type = Column(String)
    media_uuid = Column(UUID(as_uuid=True))
    reported_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    reported_count = Column(Integer)
    report_reason = Column(String)
    report_status = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime)
      
class Setting(Base):
    
    __tablename__ = 'settings'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    private_setting = Column(String)
    blocked_account = Column(ARRAY(UUID(as_uuid=True)))
    logout_activity = Column(ARRAY(UUID(as_uuid=True)))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
     

class Post(Base):
    
    __tablename__ = 'posts'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    caption = Column(String)
    media_link = Column(String)
    media_type = Column(String)
    share_count = Column(Integer)
    send_count = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    tags = Column(ARRAY(String))
    hashtags = Column(ARRAY(String))
    like_count = Column(Integer)
    details = Column(JSON)
    comments_count = Column(Integer)
    not_interested = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class Certificate(Base):
    
    __tablename__ = 'certificates'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    name = Column(String)
    link = Column(String)
    is_paid_course = Column(Boolean)
    course_amount = Column(String)
    is_online_course = Column(Boolean)
    location = Column(String)
    from_date = Column(Date)
    to_date = Column(Date)
    description = Column(String)
    tags = Column(ARRAY(String))
    hashtags = Column(ARRAY(String))
    is_deleted = Column(Boolean, default=False)
    like_count =Column(Integer)
    comments_count = Column(Integer)
    cover_image_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class EBattle(Base):
    
    __tablename__ = 'e_battles'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    category = Column(String)
    title = Column(String)
    timezone = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    start_time = Column(String)
    end_time = Column(String)
    is_online_battle = Column(Boolean)
    activity_url = Column(String)
    location = Column(String)
    description = Column(String)
    tags = Column(ARRAY(String))
    hashtags = Column(ARRAY(String))
    cover_image_url = Column(String)
    guests = Column(ARRAY(UUID(as_uuid=True)))
    collab_acc = Column(ARRAY(UUID(as_uuid=True)))
    is_deleted = Column(Boolean, default=False)
    like_count =Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class JoinEBattle(Base):
    
    __tablename__ = 'join_e_battles'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    e_battle_uuid = Column(UUID(as_uuid=True), ForeignKey('e_battles.uuid'))
    email = Column(String)
    mobile = Column(String)
    caption = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class Comment(Base):
    
    __tablename__ = 'comments'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    post_uuid = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
    certificate_uuid = Column(UUID(as_uuid=True), ForeignKey('certificates.uuid'))
    comment_details = Column(String)
    hashtags = Column(ARRAY(String))
    tags = Column(ARRAY(String))
    like_count = Column(Integer)
    is_deleted =Column(Boolean, default=False)
    is_reported = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
    
class Like(Base):
    
    __tablename__ = 'likes'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    post_uuid = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
    certificate_uuid = Column(UUID(as_uuid=True), ForeignKey('certificates.uuid'))
    ebattle_uuid = Column(UUID(as_uuid=True), ForeignKey('e_battles.uuid'))
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    is_liked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    

class CommentLikes(Base):
    
    __tablename__ = 'comment_likes'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    comment_uuid = Column(UUID(as_uuid=True), ForeignKey('comments.uuid'))
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    is_liked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class Hashtag(Base):
    
    __tablename__ = 'hashtags'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    hashtags = Column(String)
    hashtags_count = Column(Integer)
    trending_hastag = Column(Boolean, default=False)
    easter_eggs = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

# class HashtagMapping(Base):
    
#     __tablename__ = 'hashtags_mapping'
    
#     uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
#     hashtag_uuid = Column(UUID(as_uuid=True), ForeignKey('hashtags.uuid'))
#     post_uuid = Column(UUID(as_uuid=True), ForeignKey('posts.uuid'))
#     certificate_uuid = Column(UUID(as_uuid=True), ForeignKey('certificates.uuid'))
#     e_battle_uuid = Column(UUID(as_uuid=True), ForeignKey('e_battles.uuid'))
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)
#     updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
  
class DontRecomment(Base):
    
    __tablename__ = 'dont_recommends'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    post_uuid = Column(ARRAY(UUID(as_uuid=True)))
    certificate_uuid = Column(ARRAY(UUID(as_uuid=True)))
    ebattle_uuid = Column(ARRAY(UUID(as_uuid=True)))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class Boosts(Base):
    
    __tablename__ = 'boost_table'  
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    sender_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), primary_key=True)
    receiver_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), primary_key=True)
    status = Column(String, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)      
        
class Review(Base):
    
    __tablename__ = 'reviews'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    reviewer_uuid = Column(UUID(as_uuid=True))
    review = Column(String)
    rating = Column(Float)
    reply = Column(String)
    hashtags = Column(ARRAY(String))
    tags = Column(ARRAY(String))
    replied_at = Column(DateTime)
    is_reported = Column(Boolean, default=False)
    reported_at = Column(DateTime)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
            

class MeNeMLog(Base):
    
    __tablename__ = 'menem_logs'
    
    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    user_uuid = Column(UUID(as_uuid=True))
    ip = Column(Text)
    module = Column(String)
    status_code = Column(Integer, default=200)
    description = Column(Text)
    api = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)  
    
class ResetPasswordCode(Base):
    
    __tablename__ = 'reset_password_code'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey('users.uuid'))
    verification_code = Column(JSON)
    consumed = Column(Boolean, default=False)
    expired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PartnerAndServices(Base):

    __tablename__ = "partner_and_services"

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True, default=uuid.uuid4)
    organization_name = Column(String)
    location = Column(String)
    website = Column(String)
    services = Column(String)
    email = Column(String)
    mobile = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class job_title(Base):

    __tablename__ = 'job_title'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)
    
class edu_specialization(Base):

    __tablename__ = 'edu_specialization'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    specialization = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class edu_degree(Base):

    __tablename__ = 'edu_degree'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    degree = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class industry(Base):

    __tablename__ = 'industry'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    industry = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class explore_category(Base):

    __tablename__ = 'explore_category'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    explore_category = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class location(Base):

    __tablename__ = 'location'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    location = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

class app_data(Base):

    __tablename__ = 'app_data'

    uuid = Column(UUID(as_uuid=True), primary_key=True, unique=True)
    app_name = Column(String)
    app_logo = Column(String)
    mobile_app_version = Column(String)
    is_maintenance = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.datetime.utcnow)

# Base.metadata.create_all(bind=engine)