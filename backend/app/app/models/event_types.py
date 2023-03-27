from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class EventTypes(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="event_types"
    id=Column(Integer,primary_key=True)
    title=Column(String(255))
    payment_type=Column(TINYINT,nullable=False,default=1,comment=" 1->Free, 2->Paid ")
    created_at=Column(DateTime)
    created_by=Column(Integer,ForeignKey("user.id"))
    last_updated_at=Column(DateTime)
    last_updated_by=Column(Integer,ForeignKey("user.id"))
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    user1=relationship("User",foreign_keys=[created_by])
    user2=relationship("User",foreign_keys=[last_updated_by])
    events=relationship("Events",back_populates="event_types")
    
    