import os
from dotenv import load_dotenv

#'OAuth2PasswordBearer' defines where FastAPI should look for the token in incoming requests
from fastapi.security import OAuth2PasswordBearer

from fastapi import HTTPException

#It is passlib's tool for hashing and verifying passwords
from passlib.context import CryptContext

#Used to encode (create) and decode (verify) JWTs
import jwt

#Used to set token expiration
from datetime import datetime, timedelta, timezone

from typing import Optional
from schemas import TokenData

#Loads variables from the .env file so os.getenv() can access them
load_dotenv()

#Key used to sign the JWT, so that the server (us) can later verify the token was not tampered with
SECRET_KEY = os.getenv("SECRET_KEY")

#The signing algorithm. HS256 is a standard, symmetric choice for this kind of setup
ALGORITHM = os.getenv("ALGORITHM")

#Defines how many minutes the token stays valid before the user has to log in again
TOKEN_EXPIRES = int(os.getenv("TOKEN_EXPIRES"))

#'pwd_context' is a reusable object for hashing and verifying passwords
#'schemes=["bcrypt"]' tells the object to use bcrypt. It is a password hashing algorithm, a way to turn a plain-text password into an irreversible scrambled string
#'depricated="auto"' auto-flags old hashes for rehashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#Tells FastAPI where the clients get a token, so it knows how to extract and validate it from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#Checks whether a login attempt is correct
def verify_pwd(plain_pwd: str, hashed_pwd: str)-> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)

#Returns the hashed password
def get_pwd_hash(password: str)-> str:
    return pwd_context.hash(password)

#Builds and signs the actual JWT with the SECRET_KEY
def create_access_token(data: dict, expires_delta: Optional[timedelta]=None):

    #Makes a copy of the data to put inside the token
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(TOKEN_EXPIRES)      #Falls back to the configured 'TOKEN_EXPIRES' instead of a hardcoded value


    #Adds the expiry timestamp into the token's payload.
    #'exp' is a standard JWT field that libraries know to check automatically
    to_encode.update({"exp": expire})

    #Takes the payload, signs it with the SECRET_KEY using the specified algorithm, and produces the final token string
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

#Validates an incoming token and extracts the user's identity from it
def verify_token(token:str) -> TokenData:

    #Decodes and verifies the token
    #jwt.PyJWTError is intentionally not caught here. It bubbles up to get_current_user in dependencies.py which converts it into a 401
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    #Extracts the email from the payload
    #'sub' is the standard JWT field for identifying who the token belongs to
    email: str = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    #Wraps the email in a Pydantic schema and returns it
    return TokenData(email=email)