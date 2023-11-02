from sqlalchemy import Column, Integer, String, DateTime,TEXT
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class AccountVerifyWebhook(Base):
    __tablename__ = "account_verify_webhook"
    id = Column(Integer, primary_key=True)
    request = Column(TEXT)
    response=Column(TEXT)
    created_at = Column(DateTime)
    status = Column(TINYINT, comment="0->Inactive, 1->Active,-1-delete")



    # CREATE TABLE `rawcaster`.`account_verify_webhook` ( `id` INT NOT NULL AUTO_INCREMENT , `request` TEXT NULL , `response` TEXT NULL , `created_at` DATETIME NULL , `status` TINYINT NULL COMMENT '0->Inactive, 1->Active,-1-delete' , PRIMARY KEY (`id`)) ENGINE = InnoDB; 
