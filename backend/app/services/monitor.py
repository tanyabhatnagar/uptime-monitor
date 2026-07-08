import asyncio
import logging
import time
from typing import Dict, Any, List
import httpx
from sqlalchemy import select

from app.db import async_session_maker
from app.models import HealthCheck, Url

# Configure service logger
logger = logging.getLogger("uptime_monitor.services.monitor")
logger.setLevel(logging.INFO)


async def ping_url(client: httpx.AsyncClient, url_id: int, url: str) -> Dict[str, Any]:
    """
    Asynchronously pings a URL with a GET request, measuring response time.
    Catches timeouts, DNS errors, connection errors, and records them as DOWN.
    
    Args:
        client: The HTTPX async client instance to perform the request.
        url_id: The primary key of the URL in the database.
        url: The web URL string.
        
    Returns:
        A dictionary containing the check statistics.
    """
    logger.debug(f"Pinging URL ID {url_id}: {url}")
    start_time = time.perf_counter()
    status_code = None
    is_up = False
    error_message = None

    try:
        # Request with a 10-second timeout
        response = await client.get(url, timeout=10.0, follow_redirects=True)
        # Any successful HTTP response (i.e. we got back a status code) is considered UP.
        is_up = True
        status_code = response.status_code
        logger.debug(f"Success for {url}: status={status_code}")
    except httpx.TimeoutException as e:
        error_message = f"Timeout: {type(e).__name__}"
        logger.warning(f"Timeout checking URL {url}: {e}")
    except httpx.NetworkError as e:
        error_message = f"Network failure: {type(e).__name__}"
        logger.warning(f"Network error checking URL {url}: {e}")
    except Exception as e:
        error_message = f"Unhandled error: {type(e).__name__} ({str(e)})"
        logger.error(f"Unexpected error checking URL {url}: {e}", exc_info=True)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return {
        "url_id": url_id,
        "is_up": is_up,
        "status_code": status_code,
        "response_time_ms": elapsed_ms,
        "error_message": error_message,
    }


async def run_monitoring_job() -> None:
    """
    Job target executing periodically.
    Fetches all active URLs, pings them concurrently, and records results to the database.
    """
    logger.info("Executing scheduled health check iteration...")
    
    async with async_session_maker() as session:
        # 1. Fetch all active monitored URLs
        result = await session.execute(select(Url).where(Url.is_active == True))
        active_urls = list(result.scalars().all())

        if not active_urls:
            logger.info("No active URLs to monitor this minute.")
            return

        logger.info(f"Pinging {len(active_urls)} active URLs concurrently...")

        # 2. Fire concurrent network checks using httpx
        async with httpx.AsyncClient() as client:
            tasks = [ping_url(client, url.id, url.url) for url in active_urls]
            check_results = await asyncio.gather(*tasks)

        # 3. Create and append HealthCheck model records
        for res in check_results:
            health_check = HealthCheck(
                url_id=res["url_id"],
                is_up=res["is_up"],
                status_code=res["status_code"],
                response_time_ms=res["response_time_ms"],
                error_message=res["error_message"],
            )
            session.add(health_check)

        # 4. Commit all records in a single database transaction
        try:
            await session.commit()
            logger.info(f"Health check iteration completed. Logged {len(check_results)} checks.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error writing health check results: {e}", exc_info=True)
