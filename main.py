from app.models import *
from app.email import *
from app.authentication import *

from fastapi import FastAPI, Request, HTTPException, status, Depends
from tortoise.contrib.fastapi import register_tortoise

# authentication
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# signals
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

# response classes
from fastapi.responses import HTMLResponse

# templates
from fastapi.templating import Jinja2Templates

# image upload
from fastapi import File, UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI()

templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# static file setup config
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return {"message": "Hello World"}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials["SECRET"], algorithms=["HS256"])
        user = await User.get(id=payload.get("id"))
        return await user

    except:
        HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"})


@app.post("/token")
async def generate_token(request_form: OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/user/me")
async def user_login(user: user_pydanticIn = Depends(get_current_user)):
    business = await Business.get(owner=user)
    logo = business.logo
    logo_path = "http://localhost:8000/static/images/" + logo
    return {
        "status": "success",
        "data": {
            "username": user.username,
            "email": user.email,
            "verified": user.is_verified,
            "join_date": user.join_date.strftime("%m/%d/%Y"),
            "logo": logo_path

        }
    }


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


@app.get("/verification", response_class=HTMLResponse)
async def email_verification(request: Request, token: str):
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponse("verification.html", {"request": request, "username": user.username})

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token",
                        headers={"WWW-Authenticate": "Bearer"})


@post_save(User)
async def create_business(
        sender: "Type[User]",
        instance: User,
        created: bool,
        using_db: "Optional[BaseDBAsyncClient]",
        update_fields: List[str],
) -> None:
    if created:
        business_obj = await Business.create(
            business_name=instance.username,
            owner=instance
        )
        await business_pydantic.from_tortoise_orm(business_obj)
        await send_email([instance.email], instance)


@app.post("/upload-file/profile")
async def create_upload_file(file: UploadFile = File(...),
                             user: user_pydantic = Depends(get_current_user)):
    FILEPATH = "./static/ímages/"
    file_name = file.filename
    extension = file_name.split(".")[-1]

    if extension not in ["png", "jpg", "jpeg"]:
        return {"status": "error", "detail": "File extension is not allowed."}

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()
    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)

    file.close()
    business = await Business.get(owner=user)
    owner = await business.owner

    if not owner == user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized to perform this action.",
                            headers={"WWW-Authenticate": "Bearer"})

    business.logo = token_name
    await business.save()

    file_url = "http://localhost:8000" + generated_name[1:]
    return {
        "status": "success",
        "filename": file_url
    }


@app.post("/upload-file/product/{id}")
async def create_update_file(id: int, file: UploadFile = File(...),
                             user: user_pydantic = Depends(get_current_user)):
    FILEPATH = "./static/ímages/"
    file_name = file.filename
    extension = file_name.split(".")[-1]

    if extension not in ["png", "jpg", "jpeg"]:
        return {"status": "error", "detail": "File extension is not allowed."}

    token_name = secrets.token_hex(10) + "." + extension
    generated_name = FILEPATH + token_name
    file_content = await file.read()
    with open(generated_name, "wb") as file:
        file.write(file_content)

    img = Image.open(generated_name)
    img = img.resize(size=(200, 200))
    img.save(generated_name)

    file.close()
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner

    if not owner == user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized to perform this action.",
                            headers={"WWW-Authenticate": "Bearer"})

    product.product_image = token_name
    await product.save()

    file_url = "http://localhost:8000" + generated_name[1:]
    return {
        "status": "success",
        "filename": file_url
    }


# CRUD

@app.post("/products")
async def add_new_product(product: product_pydanticIn,
                          user: user_pydantic = Depends(get_current_user)):
    product = product.dict(exclude_unset=True)

    if product["original_price"] > 0:
        product["percentage_discount"] = ((product["original_price"] - product["new_price"]) / product[
            "original_price"]) * 100

        product_obj = await Product.create(**product, business=user)
        product_obj = await product_pydantic.from_tortoise_orm(product_obj)
        return {
            "status": "success",
            "data": product_obj
        }


@app.get("/product")
async def get_product():
    response = await product_pydantic.from_queryset(Product.all())
    return {
        "status": "success",
        "data": response
    }


@app.get("/product/{id}")
async def get_product(id: int):
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner
    response = await product_pydantic.from_queryset_single(Product.get(id=id))

    return {
        "status": "success",
        "data": {
            "product_details": response,
            "business_details": {
                "business_name": business.business_name,
                "city": business.city,
                "region": business.region,
                "description": business.business_description,
                "logo": business.logo,
                "owner_id": owner.id,
                "owner_email": owner.email,
                "joined_date": owner.join_date.strftime("%m/%d/%Y"),
            }
        }
    }


@app.delete("/product/{id}")
async def delete_product(id: int, user: user_pydantic = Depends(get_current_user)):
    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner

    if not owner == user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized to perform this action.",
                            headers={"WWW-Authenticate": "Bearer"})

    await product.delete()

    return {
        "status": "success",
        "data": "Deleted"
    }

@app.put("/product/{id}")
async def update_product(id: int,
                         updated_product: product_pydanticIn,
                         user: user_pydantic = Depends(get_current_user)):

    product = await Product.get(id=id)
    business = await product.business
    owner = await business.owner

    update_info = updated_product.dict(exclude_unset=True)

    if not owner == user or update_info["original_price"] <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized to perform this action.",
                            headers={"WWW-Authenticate": "Bearer"})

    update_info["percentage_discount"] = ((update_info["original_price"] - update_info["new_price"]) /
                                          update_info["original_price"]) * 100
    update_info["date_published"] = datetime.utcnow()
    product = await product.update_from_dict(update_info)
    await product.save()
    response = await product_pydantic.from_tortoise_orm(product)
    return {
        "status": "success",
        "data": response
    }

@app.put("/business/{id}")
async def update_business(id: int,
                          updated_business: business_pydanticIn,
                          user: user_pydantic = Depends(get_current_user)):

    update_info = updated_business.dict()
    business = await Business.get(id=id)
    business_owner = await business.owner

    if not business_owner == user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authorized to perform this action.",
                            headers={"WWW-Authenticate": "Bearer"})

    await business.update_from_dict(update_info)
    await business.save()
    response = await business_pydantic.from_tortoise_orm(business)
    return {
        "status": "success",
        "data": response
    }


register_tortoise(
    app,
    db_url="sqlite://database.sqlite3",
    modules={"models": ["app.models"]},
    generate_schemas=True,
    add_exception_handlers=True,

)
