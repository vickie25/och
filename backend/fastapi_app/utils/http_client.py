"""
HTTP client utilities for communicating with Django API.
"""
from typing import Any

import httpx
from config import settings


class DjangoAPIClient:
    """
    Client for making requests to Django API.
    """

    def __init__(self):
        self.base_url = settings.DJANGO_API_URL
        self.timeout = settings.DJANGO_API_TIMEOUT

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make GET request to Django API.
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Make POST request to Django API.
        """
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()


