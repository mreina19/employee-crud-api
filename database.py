#Provides access to operating system functions, used here to read environment variables
import os

#Reads a .env file and loads its key-value pairs into environment variables
from dotenv import load_dotenv

#Creates the database engine, the core connection to the database
from sqlalchemy import create_engine

#Provides the base class that all ORM models (tables) will inherit from.
from sqlalchemy.orm import DeclarativeBase

#Factory that creates database session objects used to run queries
from sqlalchemy.orm import sessionmaker

#Loads variables from the .env file so os.getenv() can access them
load_dotenv()

#Reads the database connection string from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

#Creates the SQLAlchemy engine that manages the actual connection to the database
engine = create_engine(DATABASE_URL)

#Creates a session factory. Each call to SessionLocal() returns a new database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Base class that all SQLAlchemy models (tables) will inherit from
#SQLAlchemy uses this to track which classes represent database tables
class Base(DeclarativeBase):
    pass

#Opens a db session before the request is handled, provides it to the route, and closes it when the request is done regardless of success or failure.
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()