#'Base Model' is Pydantic's base class for data validation and serialization
#'ConfigDict' is the Pydantic v2 way to configure model settings
#'Field' is used to add extra validation rules (like max_length) on top of the type itself
#'EmailStr' validates that a string is actually shaped like a valid email, not just any string
from pydantic import BaseModel, ConfigDict, Field, EmailStr

from typing import Optional

#Built-in Python module for working with dates and times
from datetime import datetime

#'Enum' is Python's built-in tool for defining a fixed set of named, valid values
from enum import Enum

#Enum that contains all the possible roles that a user can have
#Using an Enum instead of a plain string rejects invalid roles automatically and shows a dropdown of valid options in the docs, instead of accepting any free text
class UserRoles(str, Enum):
    admin = "admin"
    manager = "manager"
    developer = "developer"
    designer = "designer"
    analyst = "analyst"
    hr = "hr"

#Schema used when CREATING a user. No "id" here because the DB assigns it automatically
class UserAdd(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=70)

    #UserRoles instead of str. The role can only be one of the predefined values
    role: UserRoles

    #Gets hashed before being stored, it is never saved as it is.
    #By capping 'max_length', the schema reject overly long passwords before they ever reach bcrypt (which has a 72 bytes max)
    password: str = Field(min_length=8, max_length=72)

    is_active: bool = True

#Schema used when UPDATING a user. No "id" here because the DB assigns it automatically.
#Although identical to UserAdd, both are kept separate as they represent different intentions and may diverge in the future.
class UserUpdate(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr = Field(max_length=70)

    # UserRoles instead of str. The role can only be one of the predefined values
    role: UserRoles

    # Gets hashed before being stored, it is never saved as it is.
    # By capping 'max_length', the schema reject overly long passwords before they ever reach bcrypt (which has a 72 bytes max)
    password: str = Field(min_length=8, max_length=72)

    is_active: bool = True

#Schema used when RETURNING a user. Includes "id" because the DB has already assigned it at this point
#There are no Fields() here, because this data is already validated and stored
class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRoles
    is_active: bool
    created_at: datetime

    #'model_config' is the Pydantic v2 way to set configuration.
    #'from_attributes=True' lets Pydantic read SQLAlchemy model objects directly, not just dictionaries
    model_config = ConfigDict(from_attributes=True)

#Schema used for the LOGIN RESPONSE
#Returned to the client after a successful login, containing the JWT itself and its type
class Token(BaseModel):
    access_token: str
    token_type: str

#Represents the data extracted from inside a decoded JWT, not something sent by the client
#Used internally to identify which user a token belongs to. Optional because decoding could fail to find the expected field
class TokenData(BaseModel):
    email: Optional[str] = None