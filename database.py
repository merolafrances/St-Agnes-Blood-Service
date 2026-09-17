from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# إعدادات قاعدة البيانات (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./blood_service.db"

# إنشاء المحرك (Engine) 
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# إنشاء الجلسة (Session)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# الأساس اللي بتبني عليه الجداول
Base = declarative_base()


# ==========================================
# --- الجداول (Models) ---
# ==========================================

from sqlalchemy import Column, Integer, String, Float

class Donor(Base):
    __tablename__ = "donors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    blood_type = Column(String, index=True)
    address = Column(String)
    notes = Column(String)
    current_age = Column(Integer)
    birth_year = Column(Integer)
    weight = Column(Float)       # ضفنا الوزن اهو
    height = Column(Float)       # وادي الطول
    status = Column(String)      # وادي الحالة
    last_contact = Column(String, nullable=True) # عشان الإحصائيات
    contact_result = Column(String, nullable=True)
    last_donation = Column(String, nullable=True)
    last_called_by = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class BloodRequest(Base):
    __tablename__ = "blood_requests"
    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String)
    hospital = Column(String)
    companion_phone = Column(String)
    patient_age = Column(Integer)
    blood_type = Column(String)
    notes = Column(Text, nullable=True)
    status = Column(String, default="قيد الانتظار")
    handled_by = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    login_time = Column(DateTime, default=datetime.utcnow)