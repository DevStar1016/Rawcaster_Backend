from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class UserTypeMaster(Base):
    __tablename__ = "user_type_master"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(255))
    created_at = Column(DateTime)
    status = Column(TINYINT, default=1)

    user = relationship("User", back_populates="user_type_master")
