#Imports the building blocks for defining database table columns
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from database import Base
from sqlalchemy.sql import func

#Defines the "users" table as a Python class
#Inheriting from database.Base, tells SQLAlchemy this class represents a database table
class User(Base):
    __tablename__ = "users"  #The actual table name in the database

    #index=True speeds up lookups by ID
    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)

    #Email must be unique across all rows
    email = Column(String(70), nullable=False, unique=True)

    role = Column(String(50), nullable=False)

    #Stores the hashed version of the password. 255 is a common default length choice
    hashed_password = Column(String(255), nullable=False)

    #Flags whether the user is allowed to log in / is considered valid. Defaults to True on creation
    is_active = Column(Boolean, default=True, nullable=False)

    #Timestamp of when the row was created.
    #'server_default=func.now()' lets the DATABASE set the value, not Python, so it stays accurate even if a row is inserted outside the app
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)