#'FastAPI' is the main class that creates the application instance
#'HTTPException' raises proper HTTP errors that FastAPI automatically converts into a correct JSON error response with the right status code
#'Depends' is FastAPI's dependency injection system
#'Response' is a low-level way to build an HTTP response
from fastapi import FastAPI, HTTPException, Depends, Response

#FastAPI built-in that handles the login form data
from fastapi.security import OAuth2PasswordRequestForm

#Object that communicates to the database
from sqlalchemy.orm import Session

#Imports SQLAlchemy's func object, which gives access to SQL functions to use inside queries
from sqlalchemy import func

#Represents a duration of time
from datetime import timedelta

#Defines a List of items
from typing import List

#Enables logging
import logging

#Used to automatically retrieve the name of the current function, avoiding hardcoding it
import inspect

from dependencies import get_current_active_user, require_admin
from schemas import UserResponse, UserAdd, UserUpdate, UserPatch, Token
from models import User
from database import Base, engine, get_db
from auth import get_pwd_hash, verify_pwd, TOKEN_EXPIRES, create_access_token

#Creates a console handler that writes log messages to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

#Structures each log entry as LEVEL:file_name:message
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(name)s: %(message)s"))

#Creates a logger instance for this file, named after the module so it is identifiable in the log output
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#Attaches the console handler to the logger
logger.addHandler(console_handler)

#Prevents log messages from being passed to the root logger (uvicorn's logger), avoiding duplicates or suppression
logger.propagate = False

#Creates all tables defined in models that inherit from 'Base', if they do not already exist
Base.metadata.create_all(bind=engine)

#Creates the FastAPI application instance
app = FastAPI(title="Integration with PostGresSQL.")

#Registers a GET route at the root path "/"
@app.get("/")
def root():
    try:
        #Retrieves the name of the method
        method = inspect.currentframe().f_code.co_name

        logger.info(f"{method}: Root message successfully printed.")

        return {"message": "Intro to FastAPI with PostGreSQL."}

    #Unexpected error
    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a GET route at the path "/profile"
#Returns the user that is logged in
@app.get("/profile", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    try:
        method = inspect.currentframe().f_code.co_name
        logger.info(f"{method}: '{current_user.email}' is currently logged in.")

        return current_user

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a GET route at the path "/verify-token"
#Confirms that the token is still valid and returns basic information about the authenticated user
@app.get("/verify-token")
def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    try:
        method = inspect.currentframe().f_code.co_name

        logger.info(f"{method}: Token validated successfully for user '{current_user.email}'.")

        return {
            "valid": True,
            "user": {
                "id": current_user.id,
                "first_name": current_user.first_name,
                "last_name": current_user.last_name,
                "email": current_user.email,
                "role": current_user.role
            }
        }

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a GET ROUTE at the path "/user/"
#Returns all the information from the users table. Admin privileges
@app.get("/users/", response_model=List[UserResponse])
def get_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        logger.info(f"{method}: All users information retrieved successfully.")
        return db.query(User).all()

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a GET route at the path "/users/{user_id}"
#Gets the information of a user. Admin privileges
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id:int, current_user: User = Depends(require_admin), db:Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where id matches user_id and returns it
        db_user = db.query(User).filter(User.id == user_id).first()

        if not db_user:
            logger.warning(f"{method}: User '{user_id}' not found.")

            raise HTTPException(
                status_code=404,
                detail=f"User '{user_id}' not found."
            )

        logger.info(f"{method}: User '{user_id}' information retrieved successfully.")

        return db_user

    #Re-raises the 404 without catching it as a 500
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a POST route at the path "/register/"
#Creates a new user. Admin privileges
@app.post("/register/", response_model=UserResponse, status_code=201)
def register_user(user: UserAdd, current_user: User = Depends(require_admin), db:Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where email matches user_emails and returns it
        #Cannot call .lower() directly on a SQLAlchemy column
        if db.query(User).filter(func.lower(User.email) == user.email.lower()).first():
            logger.warning(f"{method}: Email '{user.email}' already exists.")

            raise HTTPException (
                status_code=409,
                detail=f"Email '{user.email}' already exists."
            )

        #Gets the user hashed password
        hashed_password = get_pwd_hash(user.password)

        new_user = User(
            first_name = user.first_name,
            last_name = user.last_name,
            email = user.email,
            role = user.role,
            hashed_password = hashed_password,
            is_active = user.is_active
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"{method}: User with email '{user.email}' created successfully.")

        return new_user

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a POST route at the path "/token/"
#Creates the JWT with the configured expiry and returns it
@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where email matches the given username and returns it
        user = db.query(User).filter(func.lower(User.email) == form_data.username.lower()).first()

        if not user or not verify_pwd(form_data.password, user.hashed_password):
            logger.warning(f"{method}: Incorrect username or password.")

            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password."
            )

        if not user.is_active:
            logger.warning(f"{method}: Email '{user.email}' is disabled.")

            raise HTTPException(
                status_code=401,
                detail=f"Email '{user.email}' is disabled."
            )

        #Duration object that represents how long the token will be valid
        access_token_expires = timedelta(minutes=TOKEN_EXPIRES)

        access_token = create_access_token(
            data= {"sub": user.email}, expires_delta=access_token_expires
        )

        logger.info(f"{method}: User with email '{user.email}' logged in successfully.")

        #'bearer' tells the client how to use the token. Bearer means the client should send it in every subsequent request
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


#Registers a PUT route at the path "/users/{user_id}"
#Updates the information of a user. Admin privileges
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, current_user: User = Depends(require_admin), db:Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where id matches user_id and returns it
        db_user = db.query(User).filter(User.id == user_id).first()

        if not db_user:
            logger.warning(f"{method}: User '{user_id}' not found.")

            raise HTTPException(
                status_code=404,
                detail=f"User '{user_id}' not found."
            )

        #Checks if the email is already in use by another user.
        if db.query(User).filter(func.lower(User.email) == user.email.lower(), User.id != user_id).first():
            logger.warning(f"{method}: Email '{user.email}' already exists.")

            raise HTTPException(
                status_code=409,
                detail=f"Email '{user.email}' already exists."
            )

        #Hashes the new password before updating
        hashed_password = get_pwd_hash(user.password)

        #Updates each field on the user object with the provided values
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.email = user.email
        db_user.role = user.role
        db_user.hashed_password = hashed_password
        db_user.is_active = user.is_active

        db.commit()
        db.refresh(db_user)

        logger.info(f"{method}: User '{user_id}' updated successfully.")

        return db_user

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Registers a PATCH route at the path "/users/{user_id}"
#Partially updates a user. Only fields included in the request body are changed. Admin privileges
@app.patch("/users/{user_id}", response_model=UserResponse)
def patch_user(user_id: int, user: UserPatch, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where id matches user_id and returns it
        db_user = db.query(User).filter(User.id == user_id).first()

        if not db_user:
            logger.warning(f"{method}: User '{user_id}' not found.")
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

        #'exclude_unset=True' keeps only the fields the client actually included in the request.
        update_data = user.model_dump(exclude_unset= True)

        #Checks if the email is already in use by another user, accounting for the email possibly not being part of this PATCH request at all.
        if "email" in update_data:
            if db.query(User).filter(func.lower(User.email) == update_data["email"].lower(), User.id != user_id).first():
                logger.warning(f"{method}: Email '{update_data['email']}' already exists.")
                raise HTTPException(status_code=409, detail=f"Email '{update_data['email']}' already exists.")

            db_user.email = update_data["email"]

        if "first_name" in update_data:
            db_user.first_name = update_data["first_name"]

        if "last_name" in update_data:
            db_user.last_name = update_data["last_name"]

        if "role" in update_data:
            db_user.role = update_data["role"]

        if "is_active" in update_data:
            db_user.is_active = update_data["is_active"]

        #Hashes the new password before updating.
        # Only re-hashed if the client actually included a new password in the request.
        if "password" in update_data:
            db_user.hashed_password = get_pwd_hash(update_data["password"])

        db.commit()
        db.refresh(db_user)

        logger.info(f"{method}: User '{user_id}' partially updated successfully.")
        return db_user

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


#Registers a DELETE route at the path "/users/{user_id}"
#Deletes a user from the table. Admin privileges
@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Searches the 'users' table for the first record where id matches user_id and returns it
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning(f"{method}: User '{user_id}' not found.")

            raise HTTPException(
                status_code=404,
                detail=f"User '{user_id}' not found."
            )

        if user.id == current_user.id:
            logger.warning(f"{method}: You cannot delete yourself.")

            raise HTTPException(
                status_code=403,
                detail="You cannot delete yourself."
            )

        db.delete(user)
        db.commit()

        logger.info(f"{method}: User '{user_id}' deleted successfully.")

        #No body, just confirmation it is gone
        return Response(status_code=204)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )