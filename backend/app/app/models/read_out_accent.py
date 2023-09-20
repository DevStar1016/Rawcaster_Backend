from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class ReadOutAccent(Base):
    __tablename__ = "read_out_accent"
    id = Column(Integer, primary_key=True)
    read_out_language_id = Column(Integer,ForeignKey("read_out_language.id"))
    accent = Column(String(50))
    accent_code=Column(String(10))
    created_at = Column(DateTime)
    status = Column(TINYINT, default=1, comment="0->Inactive, 1->Active")

    user_settings = relationship("UserSettings", back_populates="read_out_accent")
    read_out_language = relationship("ReadOutLanguage", back_populates="read_out_accent")
    
