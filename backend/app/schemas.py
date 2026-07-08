from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from urllib.parse import urlparse

class UrlBase(BaseModel):
    """
    Base validation schema for Monitored URLs.
    """
    url: str = Field(..., description="The URL to monitor (must start with http:// or https://)")
    name: Optional[str] = Field(None, max_length=255, description="A friendly name for this monitor")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Ensures the input URL is syntactically valid and has a valid protocol and domain.
        """
        v_stripped = v.strip()
        if not (v_stripped.startswith("http://") or v_stripped.startswith("https://")):
            raise ValueError("URL must start with 'http://' or 'https://'")
        
        # Ensure it has a length of at least 8 (e.g. http://a.c) and doesn't exceed database limit
        if len(v_stripped) < 8 or len(v_stripped) > 2048:
            raise ValueError("URL must be between 8 and 2048 characters long")
        
        # Parse URL components using standard urllib.parse
        try:
            parsed = urlparse(v_stripped)
            if not parsed.netloc:
                raise ValueError("URL must contain a valid domain or host name.")
            
            # Simple check for domain format (at least a dot in the hostname, or an IP address / localhost)
            hostname = parsed.hostname or ""
            if not hostname:
                raise ValueError("URL is missing a valid hostname.")
            
            is_localhost = hostname == "localhost"
            is_ip = all(c.isdigit() or c == "." or c == ":" for c in hostname) # simplified check for loopback/docker host ip
            if not is_localhost and not is_ip and "." not in hostname:
                raise ValueError("URL hostname must contain a dot (e.g. domain.com) or be a local service.")
        except Exception as e:
            if "URL" in str(e):
                raise
            raise ValueError(f"Invalid URL structure: {str(e)}")
            
        return v_stripped


class UrlCreate(UrlBase):
    """
    Schema for creating a new URL monitor.
    """
    pass


class UrlResponse(UrlBase):
    """
    Basic response schema for a registered URL monitor.
    """
    id: int
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class RecentCheckSchema(BaseModel):
    """
    Lightweight health check schema to feed sparkline components.
    """
    is_up: bool
    response_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UrlListResponse(UrlResponse):
    """
    Response schema that includes the latest health check state plus 
    recent historical check points for dashboard visualization.
    """
    latest_is_up: Optional[bool] = None
    latest_response_time_ms: Optional[float] = None
    latest_status_code: Optional[int] = None
    latest_checked_at: Optional[datetime] = None
    recent_checks: List[RecentCheckSchema] = Field(default_factory=list, description="List of the 10 most recent health checks")

    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    """
    Full response schema for a health check log.
    """
    id: int
    url_id: int
    checked_at: datetime
    is_up: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
