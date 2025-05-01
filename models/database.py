from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String)
    # Add more user fields as needed

class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)
    type = Column(String, nullable=False)  # rss, twitter, etc.
    added_by = Column(Integer, ForeignKey('users.id'))
    last_checked = Column(DateTime)
    
    user = relationship("User")

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    source_id = Column(Integer, ForeignKey('sources.id'))
    
    user = relationship("User")
    source = relationship("Source")

# Database engine and session
engine = create_engine(config.DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
