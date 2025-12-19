from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm
import jwt

from app.config import SECRET_KEY, ALGORITHM
from app.models.users import User as UserModel
from app.schemas import UserCreate, User as UserSchema, RefreshTokenRequest
from app.db_depends import get_async_db
from app.auth import hash_password, verify_password, create_access_token, create_refresh_token


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Регистрирует нового пользователя с ролью 'buyer' или 'seller' или 'admin'.
    """
    stmt = select(UserModel).where(UserModel.email == user.email)
    result = await db.scalars(stmt)
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    db_user = UserModel(
        email=user.email, hashed_password=hash_password(user.password.get_secret_value()), role=user.role
    )

    db.add(db_user)
    await db.commit()
    return db_user


@router.post("/token")  # New
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    """
    Аутентифицирует пользователя и возвращает access_token и refresh_token.
    """
    result = await db.scalars(
        select(UserModel).where(UserModel.email == form_data.username, UserModel.is_active == True)
    )
    user = result.first()
    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def _get_user_from_refresh_token(refresh_token: str, db: AsyncSession) -> UserModel:
    """
    Проверяет refresh-токен и возвращает пользователя.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("token_type")

        if email is None or token_type != "refresh":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.scalars(select(UserModel).where(UserModel.email == email, UserModel.is_active == True))
    user = result.first()
    if user is None:
        raise credentials_exception

    return user


@router.post("/refresh-token")
async def update_refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Обновляет refresh-токен, принимая старый refresh-токен в теле запроса.
    """
    user = await _get_user_from_refresh_token(body.refresh_token, db)
    new_refresh_token = create_refresh_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/access-token")
async def update_access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Обновляет access-токен, принимая старый refresh-токен в теле запроса.
    """
    user = await _get_user_from_refresh_token(body.refresh_token, db)
    new_access_token = create_access_token(data={"sub": user.email, "role": user.role, "id": user.id})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }
