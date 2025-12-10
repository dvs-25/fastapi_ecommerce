from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_db


router = APIRouter(
    prefix="/products",
    tags=["products"],
)


def get_product_or_404(db: Session, product_id: int) -> ProductModel:
    """Получает активный товар по ID или вызывает 404 исключение."""
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active.is_(True))
    product = db.scalars(stmt).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


def validate_category(db: Session, category_id: int) -> CategoryModel:
    """Проверяет существование активной категории."""
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active.is_(True))
    category = db.scalars(stmt).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found")
    return category


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).where(ProductModel.is_active.is_(True))
    products = db.scalars(stmt).all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    validate_category(db, product.category_id)

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema])
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    validate_category(db, category_id)

    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active.is_(True))
    products = db.scalars(stmt).all()
    return products


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = get_product_or_404(db, product_id)
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    db_product = get_product_or_404(db, product_id)
    validate_category(db, product.category_id)

    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Удаляет товар по его ID.
    """
    product = get_product_or_404(db, product_id)
    product.is_active = False
    db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
