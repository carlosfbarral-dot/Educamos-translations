# core/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Language(Base):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)

    terms = relationship("Term", back_populates="language")


class Term(Base):
    __tablename__ = 'terms'

    id = Column(Integer, primary_key=True)
    term = Column(String, nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)

    language = relationship("Language", back_populates="terms")
    translations = relationship("Translation", back_populates="term")


class Translation(Base):
    __tablename__ = 'translations'

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey('terms.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=False)
    translation = Column(String, nullable=False)

    term = relationship("Term", back_populates="translations")
    language = relationship("Language")


class Export(Base):
    __tablename__ = 'exports'

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey('terms.id'), nullable=False)
    exported_at = Column(DateTime, default=datetime.utcnow)

    term = relationship("Term")