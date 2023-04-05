from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetPollOption(Base):
    __tablename__="nugget_poll_option"
    id=Column(Integer,primary_key=True)
    nuggets_master_id=Column(Integer,ForeignKey("nuggets_master.id")) 
    option_name=Column(String(255))
    votes=Column(Integer,default=0)
    poll_vote_percentage=Column(DECIMAL(10,2),default=0.00)
    created_date=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    nuggets_master=relationship("NuggetsMaster",back_populates="nugget_poll_option")
    
    nugget_poll_voted=relationship("NuggetPollVoted",back_populates="nugget_poll_option")
    