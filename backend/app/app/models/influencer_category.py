
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class InfluencerCategory(Base):
    __tablename__="influencer_category"
    id=Column(Integer,primary_key=True)
    name=Column(String(50))
    created_date=Column(DateTime)
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")    
    