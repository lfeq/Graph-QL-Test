from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, update, and_
from .models import FutureViewing, ProcessingStatus
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


async def get_recent_future_viewings_and_mark_viewed(db: AsyncSession, page: int = 1, page_size: int = 20):
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
                FutureViewing.has_been_viewed == False
            )
        )
        .order_by(desc(FutureViewing.created_at))  # Obtener en orden descendente
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    images_to_show = result.scalars().all()

    if not images_to_show:
        return []

    # 2. Marcar como vistas
    image_ids_to_update = [img.id for img in images_to_show]
    update_stmt = (
        update(FutureViewing)
        .where(FutureViewing.id.in_(image_ids_to_update))
        .values(has_been_viewed=True)
    )
    await db.execute(update_stmt)
    await db.commit()

    # 3. Revertir el orden para la presentación (como en el C# original)
    images_to_show.reverse()

    # Refrescar las entidades para obtener el estado `has_been_viewed` actualizado
    # Esto no es estrictamente necesario si solo devuelves los datos ya obtenidos,
    # pero es bueno si quieres los objetos completos y actualizados.
    refreshed_images = []
    for img in images_to_show:
        await db.refresh(img)
        refreshed_images.append(img)

    return refreshed_images