from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class ReadOutLanguage(Base):
    __tablename__ = "read_out_language"
    id = Column(Integer, primary_key=True)
    language = Column(String(100))
    language_code = Column(String(10))
    language_with_country=Column(String(10))
    created_at = Column(DateTime)
    status = Column(TINYINT, default=1, comment="0->Inactive, 1->Active")

    user_settings = relationship("UserSettings", back_populates="read_out_language")
