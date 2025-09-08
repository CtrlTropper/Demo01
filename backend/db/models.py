from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, func, UniqueConstraint


Base = declarative_base()


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(128), index=True, nullable=False)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    pdf_name = Column(String(255), nullable=False, unique=True, index=True)
    path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('pdf_name', name='uq_documents_pdf_name'),
    )


