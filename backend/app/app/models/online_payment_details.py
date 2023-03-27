from sqlalchemy import Column, Integer, String,DateTime,ForeignKey,Text,BLOB
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base

class OnlinePaymentDetails(Base):
    __tablename__="online_payment_details"
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("user.id"),comment=" user table ref id ")
    paid_for=Column(TINYINT,default=1,comment=" 1->Event, 2->Wallet ")
    event_id=Column(Integer,ForeignKey("events.id"),comment=" event table ref id ")
    date_time=Column(DateTime)
    payment_gateway_id=Column(Integer,ForeignKey("payment_gateways.id"),comment=" payment_gateway table ref id ")
    payment_gateway_request=Column(Text,comment=" raw request sent to payment gateway with params ")
    payment_gateway_response=Column(Text,comment=" raw response received from payment gateway ")
    payment_status=Column(TINYINT,default=0,comment=" 0->Pending, 1->Success, 2->Failed ")
    our_ref_code=Column(String(100),comment=" for our local app purpose ")
    payment_gateway_ref_code=Column(String(100),comment=" for payment gateway ")
    request_time=Column(DateTime)
    response_time=Column(DateTime)
    event_update_log_ref_id=Column(Integer)
    
    user=relationship("User",back_populates="online_payment_details")
    events=relationship("Events",back_populates="online_payment_details")
    payment_gateways=relationship("PaymentGateways",back_populates="online_payment_details")
    


    