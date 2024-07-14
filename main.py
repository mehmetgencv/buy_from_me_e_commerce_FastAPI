from urllib.request import Request

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from app.models import *
from app.authentication import *

app = FastAPI()


@app.get("/")
async def index():
    return {"message": "Hello World"}

@app.post("/registration")
async def user_registrations(user: user_pydanticIn):
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = get_hashed_password(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return {
        "status": "success",
        "data": f"Hello {new_user.username}, thanks for registering. "
                f"Please check your email to verify your email.",
    }

register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,

)
