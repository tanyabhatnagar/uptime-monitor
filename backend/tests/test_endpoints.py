import pytest
from httpx import AsyncClient
from fastapi import status

# Standard pytest marker for all tests in this file
pytestmark = pytest.mark.asyncio

async def test_health_endpoint(client: AsyncClient):
    """
    Verify the GET /health endpoint returns status ok.
    """
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

async def test_add_url_success(client: AsyncClient):
    """
    Verify adding a valid URL succeeds.
    """
    response = await client.post(
        "/urls",
        json={"url": "https://example.com", "name": "Example Test"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["url"] == "https://example.com"
    assert data["name"] == "Example Test"
    assert "id" in data

async def test_add_url_invalid(client: AsyncClient):
    """
    Verify adding invalid URLs fails with a 422 error.
    """
    # Invalid protocol
    response = await client.post(
        "/urls",
        json={"url": "ftp://example.com", "name": "FTP Test"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Missing domain dot
    response2 = await client.post(
        "/urls",
        json={"url": "https://invalidlocalhostname", "name": "Bad Host"}
    )
    assert response2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_add_duplicate_url(client: AsyncClient):
    """
    Verify adding duplicate URLs triggers a 400 error.
    """
    payload = {"url": "https://duplicate.com", "name": "Dupe Site"}
    
    # First time succeeds
    resp1 = await client.post("/urls", json=payload)
    assert resp1.status_code == status.HTTP_201_CREATED
    
    # Second time fails
    resp2 = await client.post("/urls", json=payload)
    assert resp2.status_code == status.HTTP_400_BAD_REQUEST
    assert resp2.json()["detail"] == "URL is already registered."

async def test_get_urls_list(client: AsyncClient):
    """
    Verify list query endpoint retrieves registered items.
    """
    # Check current list is empty or contains the duplicate test item
    response = await client.get("/urls")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

async def test_manual_health_check_endpoint(client: AsyncClient):
    """
    Verify triggering manual health check works.
    """
    # First add a test URL
    add_resp = await client.post(
        "/urls",
        json={"url": "https://test-check.org", "name": "Check Site"}
    )
    assert add_resp.status_code == status.HTTP_201_CREATED
    url_id = add_resp.json()["id"]
    
    # Trigger manual health check
    check_resp = await client.post(f"/urls/{url_id}/check")
    assert check_resp.status_code == status.HTTP_200_OK
    check_data = check_resp.json()
    assert check_data["url_id"] == url_id
    assert "is_up" in check_data
    assert "response_time_ms" in check_data

async def test_manual_health_check_not_found(client: AsyncClient):
    """
    Verify manual check on non-existent ID returns 404.
    """
    response = await client.post("/urls/99999/check")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "URL monitor not found."

async def test_delete_url_success(client: AsyncClient):
    """
    Verify deleting a URL succeeds and cascading works.
    """
    # Register a URL first
    add_resp = await client.post(
        "/urls",
        json={"url": "https://delete-me.org", "name": "Delete Site"}
    )
    assert add_resp.status_code == status.HTTP_201_CREATED
    url_id = add_resp.json()["id"]
    
    # Delete URL
    del_resp = await client.delete(f"/urls/{url_id}")
    assert del_resp.status_code == status.HTTP_200_OK
    assert del_resp.json() == {"message": "URL deleted successfully."}
    
    # Verify it is deleted from list
    get_resp = await client.get("/urls")
    urls = get_resp.json()
    assert not any(u["id"] == url_id for u in urls)

async def test_delete_url_not_found(client: AsyncClient):
    """
    Verify deleting a non-existent URL returns 404.
    """
    response = await client.delete("/urls/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "URL monitor not found."
