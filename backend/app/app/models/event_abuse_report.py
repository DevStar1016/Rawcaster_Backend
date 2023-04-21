from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class EventAbsueReport(Base):
    __tablename__="event_abuse_report"
    id=Column(Integer,primary_key=True)
    event_id=Column(Integer,ForeignKey("events.id"))
    user_id=Column(Integer,ForeignKey('user.id'))
    message=Column(Text)
    created_at=Column(DateTime)
    attachment=Column(String(500))
    status=Column(TINYINT,comment="1-Active,0-Inactive")
    
    
    events=relationship("Events",back_populates="event_abuse_report")
    user=relationship("User",back_populates="event_abuse_report")
    
    
    