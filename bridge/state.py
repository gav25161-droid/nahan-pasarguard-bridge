import asyncio


class BridgeState:
    def __init__(self):
        self.lock = asyncio.Lock()

        # آخرین مقدار مصرف دریافت‌شده از Nahan
        self.last_usage = {}

        # مقدار تجمعی مصرف هر کاربر
        self.total_usage = {}

        # تعداد کاربران آنلاین
        self.online_users = {}

        # IPهای آنلاین هر کاربر
        self.online_ips = {}

    async def get_last_usage(self, email):
        async with self.lock:
            return self.last_usage.get(email, 0)

    async def set_last_usage(self, email, value):
        async with self.lock:
            self.last_usage[email] = value

    async def get_total_usage(self, email):
        async with self.lock:
            return self.total_usage.get(email, 0)

    async def set_total_usage(self, email, value):
        async with self.lock:
            self.total_usage[email] = value

    async def set_online(self, email, value):
        async with self.lock:
            self.online_users[email] = value

    async def get_online(self, email):
        async with self.lock:
            return self.online_users.get(email, 0)

    async def set_online_ips(self, email, ips):
        async with self.lock:
            self.online_ips[email] = ips

    async def get_online_ips(self, email):
        async with self.lock:
            return self.online_ips.get(email, {})
