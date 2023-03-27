from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class UserStatusMaster(Base):
    __tablename__="user_status_master"
    #__table_args__ = {'extend_existing': True}
    id=Column(Integer,primary_key=True)
    name=Column(String(100))
    description=Column(String(255))
    referral_needed=Column(Integer,default=0,comment=" Referral need to upgrade user account (per month) ")
    max_event_duration=Column(Integer,default=1,comment=" Max Event Duration(hours) ")
    max_event_participants_count=Column(Integer,default=2,comment=" Max Participants allowed ")
    created_at=Column(DateTime)
    status=Column(TINYINT,default=1)