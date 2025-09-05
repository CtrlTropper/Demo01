from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from database import Base

class DS_Nguoi_dung(Base):
	__tablename__ = "DS_Nguoi_dung"

	UID = Column(Integer, primary_key=True, index=True)
	Username = Column(String(128), unique=True, nullable=False, index=True)
	passwork = Column(String(255), nullable=False)
	isAdmin = Column(Boolean, default=False, nullable=False, index=True)

	files = relationship("DS_File", back_populates="creator", cascade="all, delete-orphan")
	sessions = relationship("SessionToken", back_populates="user", cascade="all, delete-orphan")

class DS_File(Base):
	__tablename__ = "DS_File"

	UID = Column(Integer, primary_key=True, index=True)
	Ten_file = Column(String(255), nullable=False)
	CreateBy = Column(Integer, ForeignKey("DS_Nguoi_dung.UID"), nullable=False, index=True)
	CreateAt = Column(DateTime, default=datetime.utcnow, nullable=False)
	isEmbeding = Column(Boolean, default=False, nullable=False, index=True)

	creator = relationship("DS_Nguoi_dung", back_populates="files")

class SessionToken(Base):
	__tablename__ = "SessionToken"

	id = Column(Integer, primary_key=True, index=True)
	token = Column(String(256), unique=True, nullable=False, index=True)
	user_id = Column(Integer, ForeignKey("DS_Nguoi_dung.UID"), nullable=False, index=True)
	created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
	expires_at = Column(DateTime, nullable=False)

	user = relationship("DS_Nguoi_dung", back_populates="sessions")
