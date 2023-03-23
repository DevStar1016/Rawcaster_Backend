from sqlalchemy import Column, Integer, String,DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT,LONGTEXT
from app.db.base_class import Base

class ApiCallHistory(Base):
    __tablename__="api_call_history"
    id=Column(Integer,primary_key=True)
    api=Column(String(2500),comment="url")
    call_method=Column(String(25))
    params=Column(LONGTEXT)
    ip=Column(String(25),comment="api call from which ip")
    datetime=Column(DateTime)
    api_response=Column(LONGTEXT)
    status=Column(TINYINT,comment="-1->Deleted, 0->inactive, 1->active")