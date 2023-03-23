from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class PaymentGateways(Base):
    __tablename__="payment_gateways"
    id=Column(Integer,primary_key=True)
    title=Column(String(255)) 
    logo=Column(String(255)) 
    status=Column(TINYINT,default=1,comment=" 0->Inactive, 1->Active ")
    
    online_payment_details=relationship("OnlinePaymentDetails",back_populates="payment_gateways")
    