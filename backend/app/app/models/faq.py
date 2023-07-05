from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class Faq(Base):
    id = Column(Integer, primary_key=True)
    question = Column(String(1250))
    answer = Column(Text)
    created_at = Column(DateTime)
    status = Column(TINYINT(1), comment=" -1-deleted,0-inactive,1-active ")
