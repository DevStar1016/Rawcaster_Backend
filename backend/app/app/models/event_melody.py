from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class EventMelody(Base):
    __tablename__="event_melody"
    #__table_args__ = {'extend_existing': True}
    id=Column(Integer,primary_key=True)
    title=Column(String(255))
    event_id=Column(Integer,ForeignKey("events.id"))
    is_default=Column(TINYINT(1),nullable=False,default=0)
    is_created_by_admin=Column(TINYINT(1),nullable=False,default=0)
    path=Column(Text)
    type=Column(TINYINT(4),comment=" 1-Image, 2-Video, 3-Audio, 4-PPT ")
    created_at=Column(DateTime)
    created_by=Column(Integer,ForeignKey("user.id"))
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")

    events=relationship("Events",back_populates="event_melody")
    user=relationship("User",back_populates="event_melody")
    
    