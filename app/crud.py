import uuid # Added for screen_id type hint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, update # update re-added
from .models import FutureViewing, ProcessingStatus, ScreenViewings, Screens # Added ScreenViewings and Screens
from datetime import datetime, timedelta, timezone


async def create_future_viewing(db: AsyncSession, name: str, age: int, content: str) -> FutureViewing:
    """
    Creates a new FutureViewing record in the database.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        name (str): The name for the FutureViewing.
        age (int): The age for the FutureViewing.
        content (str): The content/prompt for the FutureViewing.

    Returns:
        FutureViewing: The newly created and refreshed FutureViewing object.
    """
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
    """
    Retrieves a FutureViewing record by its ID.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        fv_id (str): The UUID (as a string) of the FutureViewing to retrieve.

    Returns:
        FutureViewing | None: The found FutureViewing object, or None if not found.
    """
    result = await db.execute(select(FutureViewing).filter(FutureViewing.id == fv_id))
    return result.scalars().first()


async def update_future_viewing_image(db: AsyncSession, fv_id: str, image_url: str,
                                      status: ProcessingStatus) -> FutureViewing | None:
    """
    Updates the image URL and status of a specific FutureViewing record.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        fv_id (str): The UUID (as a string) of the FutureViewing to update.
        image_url (str): The new image URL to set.
        status (ProcessingStatus): The new processing status to set.

    Returns:
        FutureViewing | None: The updated and refreshed FutureViewing object, or None if not found.
    """
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
    """
    Updates the processing status of a specific FutureViewing record.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        fv_id (str): The UUID (as a string) of the FutureViewing to update.
        status (ProcessingStatus): The new processing status to set.

    Returns:
        FutureViewing | None: The updated and refreshed FutureViewing object, or None if not found.
    """
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
    Registers a new screen in the database.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        screen_name (str | None, optional): An optional friendly name for the screen.
                                           Defaults to None, in which case the screen's
                                           name attribute will be None.

    Returns:
        Screens: The newly created and refreshed Screens object.
    """
    new_screen = Screens(name=screen_name)
    db.add(new_screen)
    await db.commit()
    await db.refresh(new_screen)
    return new_screen


async def get_future_viewings_paginated(db: AsyncSession, page: int = 1, page_size: int = 20) -> list[FutureViewing]:
    """
    Retrieves FutureViewing records in a paginated manner, ordered by creation date descending.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        page (int, optional): The page number to retrieve (1-indexed). Defaults to 1.
        page_size (int, optional): The number of items per page. Defaults to 20.

    Returns:
        list[FutureViewing]: A list of FutureViewing objects for the requested page.
                             Returns an empty list if the page is out of bounds or no items exist.
    """
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


async def get_recent_future_viewings_and_mark_viewed(
    db: AsyncSession, screen_id: uuid.UUID, page: int = 1, page_size: int = 20
) -> list[FutureViewing]:
    """
    Retrieves recent, completed FutureViewings that have not yet been shown on a specific screen,
    then marks them as viewed on that screen by creating ScreenViewings entries.

    The selection criteria for FutureViewings are:
    - Status is COMPLETED.
    - Created within the last 24 hours.
    - No corresponding entry in ScreenViewings linking it to the provided `screen_id`.

    Args:
        db (AsyncSession): The SQLAlchemy asynchronous session.
        screen_id (uuid.UUID): The ID of the screen for which to fetch and mark viewings.
                               This is used to ensure a viewing isn't shown multiple times
                               on the same screen if already logged in ScreenViewings.
        page (int, optional): The page number for pagination of results. Defaults to 1.
        page_size (int, optional): The number of items per page. Defaults to 20.

    Returns:
        list[FutureViewing]: A list of FutureViewing objects to be displayed.
                             These objects are refreshed after the ScreenViewings entries are created.
                             The list is reversed from the database order to show newest last (if desired).
    """
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

    # Refrescar las entidades. While `has_been_viewed` is gone from FutureViewing,
    # refreshing ensures the FutureViewing objects are in their most current state
    # from the DB, which can be useful if other processes might modify them,
    # or if they had relationships that were affected by the commit.
    refreshed_images = []
    for img in images_to_show:
        await db.refresh(img)
        refreshed_images.append(img)

    return refreshed_images