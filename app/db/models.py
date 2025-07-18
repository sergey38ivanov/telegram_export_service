from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ExportRecord(Base):
    __tablename__ = 'export_records'

    id = Column(Integer, primary_key=True)
    phone = Column(String, nullable=False)
    name = Column(String, nullable=True)
    export_date = Column(Date, nullable=False)
    directory_name = Column(String, nullable=False)
