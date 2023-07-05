from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import TINYINT
from app.db.base_class import Base


class KurentoServers(Base):
    __tablename__ = "kurento_servers"
    id = Column(Integer, primary_key=True)
    server_id = Column(String(10))
    name = Column(String(25))
    url = Column(String(100))
    status = Column(TINYINT, default=1)
