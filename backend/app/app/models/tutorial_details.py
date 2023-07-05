from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class TutorialDetails(Base):
    __tablename__ = "tutorial_details"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    description = Column(String(550))
    type = Column(TINYINT, comment=" 1-link, 2-videopath ")
    path = Column(String(550))
    status = Column(TINYINT)
