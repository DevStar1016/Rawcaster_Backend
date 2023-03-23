from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL,BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetPollVoted(Base):
    __tablename__="nugget_poll_voted"
    id=Column(BigInteger,primary_key=True)
    nugget_master_id=Column(Integer,ForeignKey("nuggets_master.id")) 
    nugget_id=Column(Integer,ForeignKey("nuggets.id"))
    user_id=Column(Integer,ForeignKey("user.id"))
    poll_option_id=Column(BigInteger,ForeignKey("nugget_poll_option.id"))
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    nuggets=relationship("Nuggets",back_populates="nugget_poll_voted")
    user=relationship("User",back_populates="nugget_poll_voted")
    nugget_poll_option=relationship("NuggetPollOption",back_populates="nugget_poll_voted")
    nuggets_master=relationship("NuggetsMaster",back_populates="nugget_poll_voted")
    
    