from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class NuggetsShareWith(Base):
    __tablename__ = "nuggets_share_with"
    id = Column(Integer, primary_key=True)
    nuggets_id = Column(Integer, ForeignKey("nuggets.id"), comment=" nuggets table id ")
    type = Column(TINYINT, comment=" 1-Group,2-User ")
    share_with = Column(Integer, comment=" Either Group id or User id ")

    nuggets = relationship("Nuggets", back_populates="nuggets_share_with")
