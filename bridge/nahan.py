import os
import httpx


class NahanAPI:

    def __init__(self):
        self.base_url = os.getenv("NAHAN_URL", "").rstrip("/")
        self.api_key = os.getenv("NAHAN_API_KEY", "")
        self.api_route = os.getenv("NAHAN_API_ROUTE", "sync").strip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def request(self, method, path, **kwargs):
        if not self.base_url:
            raise RuntimeError("NAHAN_URL is not configured")

        url = f"{self.base_url}/{self.api_route}{path}"

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                **kwargs,
            )

            response.raise_for_status()

            if not response.content:
                return {}

            return response.json()

    async def users(self):
        return await self.request(
            "GET",
            "/api/users",
        )

    async def stats(self):
        return await self.request(
            "GET",
            "/api/stats",
        )
