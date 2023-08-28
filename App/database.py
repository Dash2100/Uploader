from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
import os

Base = declarative_base()

class Files(Base):
    __tablename__ = 'Files'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    date = Column(String)
    size = Column(String)
    share = Column(Integer)
    sharedate = Column(String)
    downloads = Column(Integer)

class ShortUrls(Base):
    __tablename__ = 'ShortUrls'

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True)
    file = Column(String)

class Sessions(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True)
    session = Column(String, unique=True, nullable=False)
    uuid = Column(String)
    username = Column(String)
    expiration_date = Column(DateTime, nullable=False)

class Users(Base):
    __tablename__ = 'Users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

def create_tables():
    engine = create_engine('sqlite:///database.db', echo=True)
    Base.metadata.create_all(engine)

def sqlinit():
    #if files not exist create them
    if not os.path.isfile('database.db'):
        create_tables()

if __name__ == "__main__":
    sqlinit()