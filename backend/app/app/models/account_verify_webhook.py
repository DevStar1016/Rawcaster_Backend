from sqlalchemy import Column, Integer, String, DateTime,TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class AccountVerifyWebhook(Base):
    __tablename__ = "account_verify_webhook"
    id = Column(Integer, primary_key=True)
    scan_ref=Column(String(255))
    client_id=Column(String(255))
    verify_status=Column(String(100))
    request = Column(TEXT)
    response=Column(TEXT)
    created_at = Column(DateTime)
    status = Column(TINYINT, comment="0->Inactive, 1->Active,-1-delete")



