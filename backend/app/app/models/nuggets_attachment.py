from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetsAttachment(Base):
    __tablename__="nuggets_attachment"
    id=Column(BigInteger,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" User table id ")
    nugget_id=Column(Integer,ForeignKey("nuggets_master.id"),comment=" Nuggets master table id ")
    media_type=Column(String(10),comment=" Image or Video ")
    media_file_type=Column(String(10),comment=" Media Extension ")
    file_size=Column(Integer,default=0)
    path=Column(Text)
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    user=relationship("User",back_populates="nuggets_attachment")
    nuggets_master=relationship("NuggetsMaster",back_populates="nuggets_attachment")
    
   
    
    