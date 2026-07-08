from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UrlBase(BaseModel):
    url: str = Field(..., description="The URL to monitor (must start with http:// or https://)")
    name: Optional[str] = Field(None, max_length=255, description="A friendly name for this monitor")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v_stripped = v.strip()
        if not (v_stripped.startswith("http://") or v_stripped.startswith("https://")):
            raise ValueError("URL must start with 'http://' or 'https://'")
        # Ensure it has a length of at least 8 (e.g. http://a) and doesn't exceed database limit
        if len(v_stripped) < 8 or len(v_stripped) > 2048:
            raise ValueError("URL must be between 8 and 2048 characters long")
        return v_stripped


class UrlCreate(UrlBase):
    pass


class UrlResponse(UrlBase):
    id: int
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UrlListResponse(UrlResponse):
    """
    Response schema that includes the latest health check state for dashboard visualization.
    """
    latest_is_up: Optional[bool] = None
    latest_response_time_ms: Optional[float] = None
    latest_status_code: Optional[int] = None
    latest_checked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    id: int
    url_id: int
    checked_at: datetime
    is_up: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
