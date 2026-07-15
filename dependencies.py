from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import inspect
import jwt

from database import get_db
from auth import oauth2_scheme, verify_token
from models import User
from schemas import UserRoles

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(name)s: %(message)s"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)
logger.propagate = False

#Returns the user that is making the current request, based on the JWT token they sent
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        method = inspect.currentframe().f_code.co_name

        #Validates the token and extracts the email from it
        token_data = verify_token(token)

        #Searches the database for a user whose email matches the one extracted from the JWT token
        user = db.query(User).filter(func.lower(User.email) == token_data.email.lower()).first()

        if user is None:
            logger.warning(f"{method}: User '{token_data.email}' not found")

            raise HTTPException(
                status_code=401,
                detail=f"User '{token_data.email}' does not exist.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user

    except HTTPException:
        raise

    #Catches expired tokens and returns a clear 401 response
    except jwt.ExpiredSignatureError:
        logger.warning(f"{method}: Token has expired.")         #No need to log as an error. Expected situation

        raise HTTPException(
            status_code=401,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    #Catches any other JWT-related error such as invalid or tampered tokens and converts it into a 401 response
    except jwt.PyJWTError:
        logger.error(f"{method}: Could not validate credentials.")

        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    except Exception as e:
        logger.error(f"{method}: {e}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

#Returns the current user only if their account is active
#Used as a dependency on protected routes instead of get_current_user directly, adding a second layer of protection
def get_current_active_user(current_user: User = Depends(get_current_user)):
    method = inspect.currentframe().f_code.co_name

    if not current_user.is_active:
        logger.warning(f"{method}: User '{current_user.email}' is inactive.")
        
        raise HTTPException(
            status_code=403,
            detail=f"User '{current_user.email}' is inactive."
        )

    return current_user

#Returns the current user only if they have the admin role
#Used as a dependency on admin-only routes, adding a third layer of protection on top of get_current_active_user
def require_admin(current_user: User = Depends(get_current_active_user)):
    method = inspect.currentframe().f_code.co_name

    if current_user.role != UserRoles.admin:
        logger.warning(f"{method}: User with email '{current_user.email}' does not have admin privileges.")

        raise HTTPException(
            status_code=403,
            detail=f"User with email '{current_user.email}' does not have admin privileges."
        )

    return current_user