from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class EventDefaultAv(Base):
    __tablename__="event_default_av"
    id=Column(Integer,primary_key=True)
    event_id=Column(Integer,ForeignKey("events.id"))
    default_host_audio=Column(TINYINT,default=1,comment="0-No,1-Yes")
    default_host_video=Column(TINYINT,default=1,comment="0-No,1-Yes")
    default_guest_audio=Column(TINYINT,comment="0-No,1-Yes")
    default_guest_video=Column(TINYINT,comment="0-No,1-Yes")

    
    events=relationship("Events",back_populates="event_default_av")
    
    