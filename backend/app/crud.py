from typing import List, Optional
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas


async def get_url_by_url(db: AsyncSession, url: str) -> Optional[models.Url]:
    """
    Retrieve a URL record matching the given address.
    """
    result = await db.execute(select(models.Url).where(models.Url.url == url))
    return result.scalars().first()


async def get_url_by_id(db: AsyncSession, url_id: int) -> Optional[models.Url]:
    """
    Retrieve a URL record by its primary key.
    """
    result = await db.execute(select(models.Url).where(models.Url.id == url_id))
    return result.scalars().first()


async def create_url(db: AsyncSession, url_in: schemas.UrlCreate) -> models.Url:
    """
    Register a new URL for monitoring.
    """
    db_url = models.Url(url=url_in.url, name=url_in.name)
    db.add(db_url)
    await db.commit()
    await db.refresh(db_url)
    return db_url


async def delete_url(db: AsyncSession, url_id: int) -> bool:
    """
    Delete a URL record and cascade delete all checks.
    Returns True if deletion was successful, False if the URL did not exist.
    """
    db_url = await get_url_by_id(db, url_id)
    if not db_url:
        return False
    await db.delete(db_url)
    await db.commit()
    return True


async def get_urls_with_latest_checks(db: AsyncSession) -> List[schemas.UrlListResponse]:
    """
    Retrieve all URLs annotated with their most recent health check metrics.
    Uses a subquery with ROW_NUMBER() to optimize search.
    """
    # Subquery to rank health checks for each url_id by checked_at descending
    subq = (
        select(
            models.HealthCheck.url_id,
            models.HealthCheck.is_up,
            models.HealthCheck.response_time_ms,
            models.HealthCheck.status_code,
            models.HealthCheck.checked_at,
            func.row_number().over(
                partition_by=models.HealthCheck.url_id,
                order_by=models.HealthCheck.checked_at.desc(),
            ).label("rn"),
        )
        .subquery()
    )

    # Join Urls with the subquery where rank is 1 (the latest check)
    stmt = (
        select(
            models.Url.id,
            models.Url.url,
            models.Url.name,
            models.Url.created_at,
            models.Url.is_active,
            subq.c.is_up.label("latest_is_up"),
            subq.c.response_time_ms.label("latest_response_time_ms"),
            subq.c.status_code.label("latest_status_code"),
            subq.c.checked_at.label("latest_checked_at"),
        )
        .outerjoin(subq, (models.Url.id == subq.c.url_id) & (subq.c.rn == 1))
        .order_by(models.Url.id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Map database row tuples into schemas.UrlListResponse instances
    return [
        schemas.UrlListResponse(
            id=row.id,
            url=row.url,
            name=row.name,
            created_at=row.created_at,
            is_active=row.is_active,
            latest_is_up=row.latest_is_up,
            latest_response_time_ms=row.latest_response_time_ms,
            latest_status_code=row.latest_status_code,
            latest_checked_at=row.latest_checked_at,
        )
        for row in rows
    ]


async def get_url_history(
    db: AsyncSession, url_id: int, limit: int = 100
) -> List[models.HealthCheck]:
    """
    Retrieve historical health check entries for a specific URL, ordered by newest first.
    """
    result = await db.execute(
        select(models.HealthCheck)
        .where(models.HealthCheck.url_id == url_id)
        .order_by(models.HealthCheck.checked_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
