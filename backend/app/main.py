import json
import logging
import socket
import urllib.request
from typing import Dict, Any, List

# Setup logging configuration first
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("uptime_monitor.main")
dns_logger = logging.getLogger("uptime_monitor.dns_patch")

# ==============================================================================
# Docker DNS-over-HTTPS (DoH) Monkeypatch for Resilient Name Resolution
# ==============================================================================
original_getaddrinfo = socket.getaddrinfo
dns_cache: Dict[str, str] = {}


def is_ip(host: str) -> bool:
    """
    Check if the hostname string is already a valid IPv4 or IPv6 address.
    """
    try:
        socket.inet_aton(host)
        return True
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except socket.error:
        pass
    return False


def custom_getaddrinfo(host: Any, port: Any, family: int = 0, type: int = 0, proto: int = 0, flags: int = 0) -> List[Any]:
    """
    Custom hostname resolver. Intercepts DNS queries for external domains and
    resolves them via Google's DNS-over-HTTPS JSON API. Ignores local and
    Docker-internal container addresses.
    """
    # Standardize host to string if passed as bytes
    if isinstance(host, bytes):
        host = host.decode("utf-8")

    # Bypass for IP addresses, local loopbacks, and internal Docker Compose service names
    if is_ip(host) or host in (
        "localhost",
        "127.0.0.1",
        "db",
        "uptime-db",
        "backend",
        "uptime-backend",
        "frontend",
        "uptime-frontend",
    ):
        return original_getaddrinfo(host, port, family, type, proto, flags)

    # Check resolution cache
    if host in dns_cache:
        return original_getaddrinfo(dns_cache[host], port, family, type, proto, flags)

    try:
        # Request A records over standard HTTPS port 443 via Google's raw IP API endpoint
        url = f"https://8.8.8.8/resolve?name={host}&type=A"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            if "Answer" in data:
                for answer in data["Answer"]:
                    if answer["type"] == 1:  # A Record
                        ip = answer["data"]
                        dns_cache[host] = ip
                        dns_logger.info(f"DoH successfully resolved {host} to {ip}")
                        return original_getaddrinfo(ip, port, family, type, proto, flags)
    except Exception as e:
        dns_logger.warning(
            f"DoH resolution failed for {host}: {e}. Falling back to default system resolver."
        )

    # Fall back to default system resolver if DoH query fails
    return original_getaddrinfo(host, port, family, type, proto, flags)


# Apply the monkeypatch to override socket DNS lookup operations globally
socket.getaddrinfo = custom_getaddrinfo
# ==============================================================================

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import Base, engine
from app.router import router
from app.services.monitor import run_monitoring_job

# Instantiate APScheduler AsyncIOScheduler
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup and shutdown lifecycles.
    - Creates database tables on startup.
    - Configures and runs the background scheduler.
    - Cleanly shuts down the scheduler on application exit.
    """
    logger.info("FastAPI lifecycle starting: Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Scheduling background monitoring job (interval = 60s)...")
    scheduler.add_job(
        run_monitoring_job,
        trigger="interval",
        seconds=60,
        id="url_monitor_job",
        replace_existing=True,
    )
    
    logger.info("Starting background scheduler...")
    scheduler.start()

    # Trigger a monitoring task run immediately in the background 
    # to avoid waiting 60s during development testing.
    asyncio.create_task(run_monitoring_job())

    yield

    logger.info("FastAPI lifecycle stopping: Shutting down background scheduler...")
    scheduler.shutdown()
    
    logger.info("Closing database engine connections...")
    await engine.dispose()


app = FastAPI(
    title="Uptime Monitor MVP Backend",
    description="Backend API for monitoring website availability and latency.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(router)


@app.get("/", summary="Root Health Check Endpoint", tags=["System"])
async def root() -> Dict[str, str]:
    """
    Root status endpoint returning basic API info.
    """
    return {
        "status": "healthy",
        "service": "Uptime Monitor API",
    }


@app.get("/health", summary="Perform a System Health Check", tags=["System"])
async def health() -> Dict[str, str]:
    """
    Liveness probe endpoint. Returns a 200 OK status to check if container is running.
    """
    return {
        "status": "ok"
    }
