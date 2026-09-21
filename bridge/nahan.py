import os
import httpx


class NahanAPI:

    def __init__(self):
        self.base_url = os.getenv("NAHAN_URL", "").rstrip("/")
        self.api_key = os.getenv("NAHAN_API_KEY", "")
        self.api_route = os.getenv(
            "NAHAN_API_ROUTE",
            "sync",
        ).strip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def request(self, method, path, **kwargs):
        if not self.base_url:
            raise RuntimeError(
                "NAHAN_URL is not configured"
            )

        url = (
            f"{self.base_url}/"
            f"{self.api_route}{path}"
        )

        async with httpx.AsyncClient(
            timeout=15
        ) as client:

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

    async def get_user(self, user_id):
    return await self.request(
        "GET",
        f"/api/users?id={user_id}",
    )

    async def stats(self):
        return await self.request(
            "GET",
            "/api/stats",
        )

    async def create_user(
        self,
        name,
        traffic_limit=None,
        daily_limit=None,
        expiry_days=None,
        notes="",
        max_configs=None,
    ):
        data = {
            "name": name,
            "notes": notes,
        }

        if traffic_limit is not None:
            data["trafficLimit"] = traffic_limit

        if daily_limit is not None:
            data["dailyLimit"] = daily_limit

        if expiry_days is not None:
            data["expiryDays"] = expiry_days

        if max_configs is not None:
            data["maxConfigs"] = max_configs

        return await self.request(
            "POST",
            "/api/users",
            json=data,
        )

    async def update_user(
        self,
        user_id,
        **fields,
    ):
        return await self.request(
            "PUT",
            f"/api/users?id={user_id}",
            json=fields,
        )

    async def delete_user(self, user_id):
        return await self.request(
            "DELETE",
            f"/api/users?id={user_id}",
        )

    async def toggle_user(self, user_id):
        return await self.request(
            "POST",
            f"/api/users?id={user_id}&action=toggle",
        )

    async def reset_traffic(self, user_id):
        return await self.request(
            "POST",
            f"/api/users?id={user_id}&action=reset",
        )
