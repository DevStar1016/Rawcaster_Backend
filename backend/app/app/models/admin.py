from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True)
    admin_type = Column(TINYINT, comment="1->Super Admin, 2->Admin")
    username = Column(String(50))
    password = Column(String(255))
    first_name = Column(String(50))
    last_name = Column(String(50))
    contact_no = Column(String(20))
    otp = Column(Integer)
    otp_created = Column(DateTime)
    created_at = Column(DateTime)
    created_by = Column(Integer, comment="admin table ref id")
    last_updated_at = Column(DateTime)
    last_updated_by = Column(Integer, comment="admin table ref id")
    status = Column(TINYINT, comment="0->Inactive, 1->Active")
