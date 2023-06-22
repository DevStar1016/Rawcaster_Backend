from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class QrTokens(Base):
    __tablename__="qr_tokens"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    token=Column(String(100))
    created_at=Column(DateTime)
    expired_at=Column(DateTime)
    status=Column(TINYINT,nullable=False,default=1,comment=" -1->Deleted, 0->inactive, 1->active ")
    
    user=relationship("User",back_populates="qr_tokens")