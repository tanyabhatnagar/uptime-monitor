from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.db import get_db

router = APIRouter()


@router.post(
    "/urls",
    response_model=schemas.UrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new URL for monitoring",
)
async def register_url(url_in: schemas.UrlCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new URL to be monitored.
    Validates that the URL format is correct and checks for existing duplicates.
    """
    existing_url = await crud.get_url_by_url(db, url=url_in.url)
    if existing_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is already registered.",
        )
    return await crud.create_url(db, url_in=url_in)


@router.get(
    "/urls",
    response_model=List[schemas.UrlListResponse],
    summary="List all monitored URLs with latest health check status",
)
async def list_urls(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all registered URLs, annotated with the latest check state.
    """
    return await crud.get_urls_with_latest_checks(db)


@router.delete(
    "/urls/{id}",
    summary="Remove a URL from the monitoring list",
)
async def delete_url(id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes the URL and cascades to remove all associated health checks.
    """
    success = await crud.delete_url(db, url_id=id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found.",
        )
    return {"message": "URL deleted successfully."}


@router.get(
    "/history/{id}",
    response_model=List[schemas.HealthCheckResponse],
    summary="Get health check history for a specific URL",
)
async def get_url_history(id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves historical check results for a specific URL (ordered by newest first).
    """
    # Check if the URL actually exists first
    url = await crud.get_url_by_id(db, url_id=id)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL not found.",
        )
    return await crud.get_url_history(db, url_id=id)
