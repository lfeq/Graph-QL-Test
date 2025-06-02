import uuid # Added for screen_id type hint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, update # update re-added
from .models import FutureViewing, ProcessingStatus, ScreenViewings, Screens # Added ScreenViewings and Screens
from datetime import datetime, timedelta, timezone


async def create_future_viewing(db: AsyncSession, name: str, age: int, content: str) -> FutureViewing:
    db_fv = FutureViewing(
        name=name,
        age=age,
        content=content,
        status=ProcessingStatus.PENDING
    )
    db.add(db_fv)
    await db.commit()
    await db.refresh(db_fv)
    return db_fv


async def get_future_viewing_by_id(db: AsyncSession, fv_id: str) -> FutureViewing | None:
    result = await db.execute(select(FutureViewing).filter(FutureViewing.id == fv_id))
    return result.scalars().first()


async def update_future_viewing_image(db: AsyncSession, fv_id: str, image_url: str,
                                      status: ProcessingStatus) -> FutureViewing | None:
    stmt = (
        update(FutureViewing)
        .where(FutureViewing.id == fv_id)
        .values(image_url=image_url, status=status)
        .returning(FutureViewing)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_fv = result.scalars().first()
    if updated_fv:
        await db.refresh(updated_fv)  # Asegura que la instancia esté actualizada
    return updated_fv


async def update_future_viewing_status(db: AsyncSession, fv_id: str, status: ProcessingStatus) -> FutureViewing | None:
    stmt = (
        update(FutureViewing)
        .where(FutureViewing.id == fv_id)
        .values(status=status)
        .returning(FutureViewing)
    )
    result = await db.execute(stmt)
    await db.commit()
    updated_fv = result.scalars().first()
    if updated_fv:
        await db.refresh(updated_fv)
    return updated_fv


async def register_screen(db: AsyncSession, screen_name: str | None = None) -> Screens:
    """
    Registers a new screen. If screen_name is provided, it's used for the name.
    Otherwise, the name field will be None.
    """
    new_screen = Screens(name=screen_name)
    db.add(new_screen)
    await db.commit()
    await db.refresh(new_screen)
    return new_screen


async def get_future_viewings_paginated(db: AsyncSession, page: int = 1, page_size: int = 20):
    if page <= 0: page = 1
    if page_size <= 0: page_size = 20
    offset = (page - 1) * page_size
    result = await db.execute(
        select(FutureViewing)
        .order_by(desc(FutureViewing.created_at))
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


async def get_recent_future_viewings_and_mark_viewed(db: AsyncSession, screen_id: uuid.UUID, page: int = 1, page_size: int = 20):
    if page <= 0: page = 1
    if page_size <= 0: page_size = 20
    offset = (page - 1) * page_size

    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)

    # 1. Obtener las imágenes
    stmt = (
        select(FutureViewing)
        .where(
            and_(
                FutureViewing.status == ProcessingStatus.COMPLETED,
                FutureViewing.created_at >= twenty_four_hours_ago,
                ~select(ScreenViewings.id) # Subquery for NOT EXISTS
                .where(
                    ScreenViewings.future_viewing_id == FutureViewing.id,
                    ScreenViewings.screen_id == screen_id
                ).exists()
            )
        )
        .order_by(desc(FutureViewing.created_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    images_to_show = result.scalars().all()

    if not images_to_show:
        return []

    # 2. Create ScreenViewings entries
    new_screen_viewings = [
        ScreenViewings(future_viewing_id=img.id, screen_id=screen_id)
        for img in images_to_show
    ]
    db.add_all(new_screen_viewings)
    await db.commit()

    # 3. Revertir el orden para la presentación
    images_to_show.reverse()

    # Refrescar las entidades para obtener el estado `has_been_viewed` actualizado
    # Esto no es estrictamente necesario si solo devuelves los datos ya obtenidos
    # (since has_been_viewed is gone from FutureViewing),
    # pero es bueno si quieres los objetos completos y actualizados por otras razones
    # o si relationships were involved that needed refreshing.
    refreshed_images = []
    for img in images_to_show:
        await db.refresh(img)
        refreshed_images.append(img)

    return refreshed_images