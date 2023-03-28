from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class Country(Base):
    id=Column(Integer,primary_key=True)
    country_code=Column(String(10),comment=" phone code ")
    mobile_no_length=Column(String(50))
    name=Column(String(100))
    iso=Column(String(2))
    img=Column(String(255),comment=" flag images or any icon images ")
    sms_enabled=Column(TINYINT,default=0)
    status=Column(TINYINT,nullable=False,default=1,comment="0->Inactive, 1->Active")
    
    nugget_hash_tags=relationship("NuggetHashTags",back_populates="country")
    user=relationship("User",back_populates="country")
    