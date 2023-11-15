from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date,TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT, LONGTEXT
from app.db.base_class import Base


class VerifyAccounts(Base):
    __tablename__ = "verify_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), comment=" user table ref id")
    first_name = Column(String(100))
    last_name = Column(String(100))
    telephone = Column(String(20))
    email_id = Column(String(50))
    dob = Column(Date)
    location = Column(String(100))
    verify_date = Column(DateTime)
    verification_token=Column(String(255),comment="authtoken for Account verify")
    verification_response=Column(TEXT)
    verify_status = Column(TINYINT, default=0, comment="0-pending,1- verified,-1- delete")
    created_at = Column(DateTime)
    status = Column(TINYINT, comment="1-Active,0-Inactive,-1-delete")

    user = relationship("User", back_populates="verify_accounts")


    # ALTER TABLE `verify_accounts` ADD `verification_token` VARCHAR(255) NULL COMMENT 'authtoken for Account verify' AFTER `verify_status`, ADD `verification_response` TEXT NULL AFTER `verification_token`; 
    # ALTER TABLE `user` DROP `verification_token`;