import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app import crud, schemas
from app.db import get_db
from app.services.monitor import ping_url
from app.models import HealthCheck

logger = logging.getLogger("uptime_monitor.router")
router = APIRouter()


@router.post(
    "/urls",
    response_model=schemas.UrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new URL for monitoring",
    tags=["Monitors"],
    response_description="The registered URL monitor configuration."
)
async def register_url(url_in: schemas.UrlCreate, db: AsyncSession = Depends(get_db)):
    """
    Registers a new website URL to be monitored.
    Validates that the URL protocol is correct, resolves the structure, and checks for existing duplicates in the database.
    """
    logger.info(f"Received request to register URL: {url_in.url}")
    existing_url = await crud.get_url_by_url(db, url=url_in.url)
    if existing_url:
        logger.warning(f"Registration rejected. URL already exists: {url_in.url}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is already registered.",
        )
    try:
        new_url = await crud.create_url(db, url_in=url_in)
        return new_url
    except Exception as e:
        logger.error(f"Error registering URL monitor: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create URL monitor database entry.",
        )


@router.get(
    "/urls",
    response_model=List[schemas.UrlListResponse],
    summary="List all monitored URLs with latest health metrics and history",
    tags=["Monitors"],
    response_description="A list of all monitored URLs and their aggregated metrics."
)
async def list_urls(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all registered website monitors, annotated with their current health check status 
    and the list of their 10 most recent response times.
    """
    logger.debug("Listing all monitored URLs")
    try:
        return await crud.get_urls_with_latest_checks(db)
    except Exception as e:
        logger.error(f"Error listing URL monitors: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve monitored URLs.",
        )


@router.delete(
    "/urls/{id}",
    summary="Remove a URL from the monitoring list",
    tags=["Monitors"],
    response_description="Simple status message confirming deletion."
)
async def delete_url(id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a monitored URL from the system. Cascades to remove all historical 
    health check logs associated with it.
    """
    logger.info(f"Received request to delete URL ID: {id}")
    success = await crud.delete_url(db, url_id=id)
    if not success:
        logger.warning(f"URL ID {id} not found for deletion.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL monitor not found.",
        )
    return {"message": "URL deleted successfully."}


@router.get(
    "/history/{id}",
    response_model=List[schemas.HealthCheckResponse],
    summary="Get health check history for a specific URL",
    tags=["History"],
    response_description="A chronological list of recent health checks (newest first)."
)
async def get_url_history(id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves up to 100 historical health check logs for a specific URL, ordered newest first.
    Useful for detailed audit trails and charts.
    """
    logger.debug(f"Fetching history logs for URL ID: {id}")
    url = await crud.get_url_by_id(db, url_id=id)
    if not url:
        logger.warning(f"History request failed: URL ID {id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL monitor not found.",
        )
    try:
        return await crud.get_url_history(db, url_id=id)
    except Exception as e:
        logger.error(f"Error fetching URL history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health check logs.",
        )


@router.post(
    "/urls/{id}/check",
    response_model=schemas.HealthCheckResponse,
    summary="Trigger an immediate manual health check",
    tags=["Monitors"],
    response_description="The result of the triggered health check."
)
async def check_url_now(id: int, db: AsyncSession = Depends(get_db)):
    """
    Triggers an immediate, out-of-band health check for a registered URL monitor.
    Saves the result to the database logs and updates status indicators immediately.
    """
    logger.info(f"Received request to manually check URL ID: {id}")
    url = await crud.get_url_by_id(db, url_id=id)
    if not url:
        logger.warning(f"Manual check request failed: URL ID {id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="URL monitor not found.",
        )
    
    try:
        async with httpx.AsyncClient() as client:
            res = await ping_url(client, url.id, url.url)
            
        health_check = HealthCheck(
            url_id=res["url_id"],
            is_up=res["is_up"],
            status_code=res["status_code"],
            response_time_ms=res["response_time_ms"],
            error_message=res["error_message"],
        )
        
        db.add(health_check)
        await db.commit()
        await db.refresh(health_check)
        logger.info(f"Manual check for URL ID {id} completed: is_up={res['is_up']}")
        return health_check
    except Exception as e:
        logger.error(f"Error executing manual health check for URL ID {id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual health check execution failed: {str(e)}",
        )
