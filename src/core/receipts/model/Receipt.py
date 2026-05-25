from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from utilities.dbconfig import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(String(20), primary_key=True)
    transaction_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(20), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
