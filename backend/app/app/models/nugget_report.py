from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class NuggetReport(Base):
    __tablename__ = "nugget_report"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    nugget_id = Column(Integer, ForeignKey("nuggets.id"))
    message = Column(String(500))
    reported_date = Column(DateTime)
    report_status = Column(TINYINT, default=0)
    status = Column(TINYINT, default=1)

    nuggets = relationship("Nuggets", back_populates="nugget_report")
    user = relationship("User", back_populates="nugget_report")
