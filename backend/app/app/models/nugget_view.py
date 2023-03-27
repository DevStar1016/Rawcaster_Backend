from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetView(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="nugget_view"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"))
    nugget_id=Column(Integer,ForeignKey("nuggets.id"))
    ip_address=Column(String(20))
    created_date=Column(DateTime)
    
    user=relationship("User",back_populates="nugget_view")
    nuggets=relationship("Nuggets",back_populates="nugget_view")

    