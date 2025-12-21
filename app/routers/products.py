from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.models.users import User as UserModel
from app.models.reviews import Review as ReviewModel
from app.auth import get_current_seller
from app.schemas import Product as ProductSchema, ProductCreate, Review as ReviewSchema
from app.db_depends import get_async_db


router = APIRouter(
    prefix="/products",
    tags=["products"],
)


async def get_product_or_404(db: AsyncSession, product_id: int) -> ProductModel:
    """Получает активный товар по ID или вызывает 404 исключение."""
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active.is_(True))
    result = await db.scalars(stmt)
    product = result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def validate_category(db: AsyncSession, category_id: int) -> CategoryModel:
    """Проверяет существование активной категории."""
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active.is_(True))
    result = await db.scalars(stmt)
    category = result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
    return category


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).where(ProductModel.is_active.is_(True))
    result = await db.scalars(stmt)
    products = result.all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    """
    Создаёт новый товар.
    """
    await validate_category(db, product.category_id)

    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    await validate_category(db, category_id)

    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active.is_(True))
    result = await db.scalars(stmt)
    products = result.all()
    return products


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = await get_product_or_404(db, product_id)
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller),
):
    """
    Обновляет товар по его ID.
    """
    db_product = await get_product_or_404(db, product_id)
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    await validate_category(db, product.category_id)

    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_seller)
):
    """
    Удаляет товар по его ID.
    """
    product = await get_product_or_404(db, product_id)
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    product.is_active = False
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/{product_id}/reviews/", response_model=list[ReviewSchema])
async def get_reviews_by_product_id(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список отзывов по ID товара.
    """
    product = await get_product_or_404(db, product_id)

    stmt = select(ReviewModel).where(ReviewModel.product_id == product_id, ReviewModel.is_active.is_(True))
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews
