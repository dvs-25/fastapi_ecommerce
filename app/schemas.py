from pydantic import BaseModel, Field, ConfigDict, EmailStr, SecretStr
from decimal import Decimal


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Название категории (3-50 символов)",
    )
    parent_id: int | None = Field(None, description="ID родительской категории, если есть")


class Category(CategoryCreate):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """

    id: int = Field(..., description="Уникальный идентификатор категории")
    is_active: bool = Field(..., description="Активность категории")

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Название товара (3-100 символов)",
    )
    description: str | None = Field(None, max_length=500, description="Описание товара (до 500 символов)")
    price: Decimal = Field(..., gt=0, description="Цена товара (больше 0)", decimal_places=2)
    image_url: str | None = Field(None, max_length=200, description="URL изображения товара")
    stock: int = Field(..., ge=0, description="Количество товара на складе (0 или больше)")
    category_id: int = Field(..., description="ID категории, к которой относится товар")


class Product(ProductCreate):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """

    id: int = Field(..., description="Уникальный идентификатор товара")
    is_active: bool = Field(..., description="Активность товара")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    Модель для создания пользователя.
    Используется в POST запросах.
    """

    email: EmailStr = Field(..., description="Email пользователя")
    password: SecretStr = Field(..., min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(
        default="buyer", pattern="^(buyer|seller|admin)$", description="Роль: 'buyer' или 'seller' или 'admin'"
    )


class User(BaseModel):
    """
    Модель для ответа с данными пользователя.
    Используется в GET запросах.
    """

    id: int = Field(..., description="Уникальный идентификатор пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    is_active: bool = Field(..., description="Статус активности пользователя")
    role: str = Field(..., description="Роль пользователя")

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenRequest(BaseModel):
    """
    Модель для запроса обновления токенов.
    Используется для передачи refresh-токена в эндпоинты обновления токенов.
    """

    refresh_token: str = Field(..., description="Refresh-токен для обновления токена")
