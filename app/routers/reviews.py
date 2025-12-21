from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.models.reviews import Review as ReviewModel
from app.models.products import Product as ProductModel
from app.models.users import User as UserModel
from app.auth import get_current_buyer
from app.auth import get_current_admin
from app.schemas import Review as ReviewSchema, ReviewCreate
from app.db_depends import get_async_db


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


async def get_review_or_404(db: AsyncSession, review_id: int) -> ReviewModel:
    """Получает активный отзыв по ID или вызывает 404 исключение."""
    stmt = select(ReviewModel).where(ReviewModel.id == review_id, ReviewModel.is_active.is_(True))
    result = await db.scalars(stmt)
    review = result.first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    return review

async def get_product_or_404(db: AsyncSession, product_id: int) -> ProductModel:
    """Получает активный товар по ID или вызывает 404 исключение."""
    stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active.is_(True))
    result = await db.scalars(stmt)
    product = result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product

async def update_product_rating(db: AsyncSession, product_id: int):
    """
    Пересчитывает и обновляет среднюю оценку продукта.
    """
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(ReviewModel.product_id == product_id, ReviewModel.is_active == True)
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.get("/", response_model=list[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех отзывов.
    """
    stmt = select(ReviewModel).where(ReviewModel.is_active.is_(True))
    result = await db.scalars(stmt)
    reviews = result.all()
    return reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer),
):
    """
    Создаёт новый отзыв.
    """
    await get_product_or_404(db, review.product_id)

    existing_review_stmt = select(ReviewModel).where(
        ReviewModel.user_id == current_user.id,
        ReviewModel.product_id == review.product_id,
        ReviewModel.is_active.is_(True),
    )
    existing_review_result = await db.scalars(existing_review_stmt)
    existing_review = existing_review_result.first()

    if existing_review:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already reviewed this product")

    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    await update_product_rating(db, db_review.product_id)
    return db_review


@router.put("/{review_id}", response_model=ReviewSchema)
async def update_review(
    review_id: int,
    review_update: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer),
):
    """
    Обновляет отзыв. Только владелец отзыва может его изменить.
    """
    review = await get_review_or_404(db, review_id)

    if review.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own reviews")

    if review_update.product_id != review.product_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change the product associated with this review"
        )

    review.comment = review_update.comment
    review.grade = review_update.grade

    await db.commit()
    await db.refresh(review)
    await update_product_rating(db, review.product_id)
    return review


@router.delete("/{review_id}")
async def delete_review(
    review_id: int, db: AsyncSession = Depends(get_async_db), current_user: UserModel = Depends(get_current_admin)
):
    """
    Удаляет отзыв по его ID.
    """
    review = await get_review_or_404(db, review_id)

    review.is_active = False
    await db.commit()
    await db.refresh(review)
    await update_product_rating(db, review.product_id)
    return review
