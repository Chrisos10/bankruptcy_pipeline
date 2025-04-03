from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from urllib.parse import quote_plus

# Encode password properly
password = "0vwxZ46X2GqzRNAkIdty5J4qa07s1Sa2"
encoded_password = quote_plus(password)

DATABASE_URL = f"postgresql://bankruptcy_iucf_user:{encoded_password}@dpg-cvm3v5re5dus73aevum0-a.oregon-postgres.render.com/bankruptcy_iucf?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables on startup: {e}")