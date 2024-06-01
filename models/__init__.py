from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs import Configuration


SQLALCHEMY_DATABASE_URL = Configuration.DB_URI

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=100, max_overflow=0
)

# engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, pool_size=100, max_overflow=0,
#                        pool_recycle=3600, pool_timeout=30, connect_args={'connect_timeout': 60},
#                        encoding='utf-8', isolation_level='READ UNCOMMITTED')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()