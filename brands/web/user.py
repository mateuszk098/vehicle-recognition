from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, status

from ..errors.user import IncorrectPasswordError, MissingUserError, UserAlreadyExistsError
from ..schemas.user import TaskCreate, TaskSchema, Token, UserCreate, UserSchema
from ..services import user as service
from .dependencies import DBDep, LoginDep, TokenDep

ACCESS_TOKEN_EXPIRES_HOURS = 1

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/token", status_code=status.HTTP_202_ACCEPTED, include_in_schema=False)
async def create_access_token(form_data: LoginDep, db: DBDep) -> Token:
    try:
        user = service.auth_user(form_data.username, form_data.password, db)
    except MissingUserError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"User {e} not found")
    except IncorrectPasswordError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    else:
        expires = timedelta(hours=ACCESS_TOKEN_EXPIRES_HOURS)
        access_token = service.create_access_token(user.username, user.id, user.role, expires)
        return Token(access_token=access_token, token_type="bearer")


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserSchema)
async def register(user: Annotated[UserCreate, Form()], db: DBDep) -> UserSchema:
    try:
        return service.create_user(user, db)
    except UserAlreadyExistsError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"User {e} already exists")


@router.post("/predict", status_code=status.HTTP_201_CREATED, response_model=TaskSchema)
async def predict(task: Annotated[TaskCreate, Form()], db: DBDep, token: TokenDep) -> TaskSchema:
    return service.create_task(task, token.user_id, db)


@router.get("/tasks/", status_code=status.HTTP_200_OK, response_model=list[TaskSchema])
async def get_tasks(db: DBDep, token: TokenDep) -> list[TaskSchema]:
    return service.get_tasks(token.user_id, db)
