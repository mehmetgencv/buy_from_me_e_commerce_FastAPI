import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext
from dotenv import dotenv_values

from app.models import User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
config_credentials = dotenv_values(".env")


def get_hashed_password(password):
    return password_context.hash(password)


async def verify_token(token: str):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"], algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


async def verify_password(plain_password: str, hashed_password: str):
    return password_context.verify(plain_password, hashed_password)


async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)

    if user and verify_password(password, user.password):
        return user
    return False


async def token_generator(username: str, password: str):
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"})

    token_data = {
        "id": user.id,
        "username": user.username,
    }

    token = jwt.encode(token_data, config_credentials["SECRET"], algorithm="HS256")
    return token
