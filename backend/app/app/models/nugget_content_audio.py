from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class NuggetContentAudio(Base):
    __tablename__="nugget_content_audio"
    id=Column(Integer,primary_key=True)
    nugget_master_id=Column(Integer,ForeignKey("nuggets_master.id"))
    path=Column(String(500))
    created_at=Column(DateTime)
    status=Column(TINYINT,default=1)
    
    nuggets_master=relationship("NuggetsMaster",back_populates="nugget_content_audio")
    
    