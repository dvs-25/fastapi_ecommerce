from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categories import Category as CategoryModel
from app.models.users import User as UserModel
from app.schemas import Category as CategorySchema, CategoryCreate
from app.db_depends import get_async_db
from app.auth import get_current_admin

router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


async def get_category_or_404(db: AsyncSession, category_id: int) -> CategoryModel:
    """Получает активную категорию по ID или вызывает 404 исключение."""
    stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active.is_(True))
    result = await db.scalars(stmt)
    category = result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


async def validate_parent_category(db: AsyncSession, parent_id: int) -> CategoryModel:
    """Проверяет существование родительской категории."""
    stmt = select(CategoryModel).where(CategoryModel.id == parent_id, CategoryModel.is_active.is_(True))
    result = await db.scalars(stmt)
    parent = result.first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent category not found")
    return parent


async def check_circular_reference(db: AsyncSession, category_id: int, parent_id: int) -> None:
    """Проверяет, что нет циклической ссылки (категория не является родителем своей родительской категории)."""
    if category_id == parent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category cannot be a parent of itself")

    current_parent_id = parent_id
    while current_parent_id is not None:
        if current_parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Circular reference detected: category cannot be a descendant of itself",
            )
        parent_stmt = select(CategoryModel).where(
            CategoryModel.id == current_parent_id, CategoryModel.is_active.is_(True)
        )
        result = await db.scalars(parent_stmt)
        parent = result.first()
        current_parent_id = parent.parent_id if parent else None


@router.get("/", response_model=list[CategorySchema])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных категорий.
    """
    stmt = select(CategoryModel).where(CategoryModel.is_active.is_(True))
    result = await db.scalars(stmt)
    categories = result.all()
    return categories


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_admin),
):
    """
    Создаёт новую категорию.
    """
    if category.parent_id is not None:
        await validate_parent_category(db, category.parent_id)

    db_category = CategoryModel(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_admin),
):
    """
    Обновляет категорию по её ID.
    """
    db_category = await get_category_or_404(db, category_id)

    if category.parent_id is not None:
        await validate_parent_category(db, category.parent_id)

        await check_circular_reference(db, category_id, category.parent_id)

    await db.execute(update(CategoryModel).where(CategoryModel.id == category_id).values(**category.model_dump()))
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", response_model=CategorySchema)
async def delete_category(
    category_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_admin)
):
    """
    Логически удаляет категорию по её ID, устанавливая is_active=False.
    """
    category = await get_category_or_404(db, category_id)
    category.is_active = False
    await db.commit()
    return category
