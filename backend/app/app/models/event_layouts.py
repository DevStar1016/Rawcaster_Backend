from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class EventLayouts(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="event_layouts"
    id=Column(Integer,primary_key=True)
    title=Column(String(255))
    created_at=Column(DateTime)
    created_by=Column(Integer)
    last_updated_at=Column(DateTime)
    last_updated_by=Column(Integer)
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    events=relationship("Events",back_populates="event_layouts")
    
    