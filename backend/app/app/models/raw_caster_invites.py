from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class RawCasterInvites(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="raw_caster_invites"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ") 
    to_email_id=Column(String(50))
    ref_code=Column(String(50),comment=" ref code used for external link ")
    created_at=Column(DateTime)
    invite_status=Column(TINYINT,default=0,comment=" 0->sent, 1->joined ")
    status=Column(TINYINT,default=1,comment="  0->Inactive, 1->Active  ")
    
    user=relationship("User",back_populates="raw_caster_invites")
    