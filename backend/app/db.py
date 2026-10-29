from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import DATABASE_URL

# SQLAlchemy only understands "postgresql://", some providers hand out "postgres://"
engine = create_engine(DATABASE_URL.replace("postgres://", "postgresql://", 1), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
