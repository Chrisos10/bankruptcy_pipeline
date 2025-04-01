from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base

DATABASE_URL = "postgresql://bankruptcy_user:aLTYjEv0OikgFNRkpWo0npeAoxvMMloN@dpg-cvl9h6ffte5s739tr0f0-a.oregon-postgres.render.com/bankruptcy"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Dependency function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
