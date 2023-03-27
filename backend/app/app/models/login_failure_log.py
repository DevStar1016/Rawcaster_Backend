
from sqlalchemy import Column, Integer, String,DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class LoginFailureLog(Base):
    #__table_args__ = {'extend_existing': True}
    __tablename__="login_failure_log"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" ref user table ")
    ip=Column(String(15),comment=" ip address ")
    created_at=Column(DateTime)
    status=Column(TINYINT)
    
    user=relationship("User",back_populates="login_failure_log")