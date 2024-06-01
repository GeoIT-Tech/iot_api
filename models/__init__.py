from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from configs import Configuration


SQLALCHEMY_DATABASE_URL = Configuration.DB_URI

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, pool_size=100, max_overflow=0
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()