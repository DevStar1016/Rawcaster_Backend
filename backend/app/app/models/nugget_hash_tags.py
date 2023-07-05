from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class NuggetHashTags(Base):
    __tablename__ = "nugget_hash_tags"
    id = Column(Integer, primary_key=True)
    nugget_master_id = Column(Integer, ForeignKey("nuggets_master.id"))
    nugget_id = Column(Integer, ForeignKey("nuggets.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    country_id = Column(Integer, ForeignKey("country.id"))
    hash_tag = Column(String(100))
    created_date = Column(DateTime)
    status = Column(TINYINT, default=1)

    nuggets_master = relationship("NuggetsMaster", back_populates="nugget_hash_tags")
    nuggets = relationship("Nuggets", back_populates="nugget_hash_tags")
    user = relationship("User", back_populates="nugget_hash_tags")
    country = relationship("Country", back_populates="nugget_hash_tags")
