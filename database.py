from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./data/cloud_costs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, unique=True, index=True)
    resource_type = Column(String)  # disk, vm, snapshot, ip, lb
    resource_name = Column(String)
    cloud_provider = Column(String)  # AWS, Azure
    region = Column(String)
    monthly_cost = Column(Float)
    status = Column(String)  # orphaned, idle, active
    last_used = Column(String)
    tags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class RemediationCommand(Base):
    __tablename__ = "remediation_commands"
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String, index=True)
    command_type = Column(String)  # CLI, API
    command = Column(Text)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH
    executed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanReport(Base):
    __tablename__ = "scan_reports"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    cloud_provider = Column(String)
    total_resources = Column(Integer)
    orphaned_count = Column(Integer)
    total_waste_monthly = Column(Float)
    total_waste_annual = Column(Float)
    scanned_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
