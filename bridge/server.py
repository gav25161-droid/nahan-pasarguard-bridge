import os
import grpc

from bridge import service_pb2
from bridge import service_pb2_grpc

from bridge.state import BridgeState
from bridge.nahan import NahanAPI


CERT_FILE = os.getenv(
    "SSL_CERT_FILE",
    "/app/certs/server.crt",
)

KEY_FILE = os.getenv(
    "SSL_KEY_FILE",
    "/app/certs/server.key",
)

API_KEY = os.getenv(
    "API_KEY",
    "",
).strip()


class AuthInterceptor(grpc.aio.ServerInterceptor):

    async def intercept_service(
        self,
        continuation,
        handler_call_details,
    ):
        metadata = dict(
            handler_call_details.invocation_metadata
        )

        authorization = metadata.get(
            "authorization",
            "",
        ).strip()

        api_key = metadata.get(
            "api-key",
            "",
        ).strip()

        x_api_key = metadata.get(
            "x-api-key",
            "",
        ).strip()

        expected = API_KEY

        valid = (
            authorization
            == f"Bearer {expected}"
            or authorization
            == expected
            or api_key
            == expected
            or x_api_key
            == expected
        )

        if not API_KEY or not valid:

            async def abort_handler(
                request,
                context,
            ):
                await context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Invalid or missing API key",
                )

            return grpc.unary_unary_rpc_method_handler(
                abort_handler
            )

        return await continuation(
            handler_call_details
        )


class NodeService(
    service_pb2_grpc.NodeServiceServicer
):

    def __init__(self):

        self.state = BridgeState()

        self.nahan = NahanAPI()

    # -----------------------------------------
    # Helper
    # -----------------------------------------

    def _describe_user(
        self,
        user,
        source,
    ):
        try:

            email = getattr(
                user,
                "email",
                "",
            )

            proxy = getattr(
                user,
                "proxies",
                None,
            )

            inbounds = getattr(
                user,
                "inbounds",
                [],
            )

            print(
                f"[USER] "
                f"source={source} "
                f"email={email} "
                f"inbounds={len(inbounds)}"
            )

            if proxy is not None:

                try:

                    vless = getattr(
                        proxy,
                        "vless",
                        None,
                    )

                    if vless is not None:

                        print(
                            f"[USER] "
                            f"VLESS flow="
                            f"{getattr(vless, 'flow', '')}"
                        )

                except Exception:
                    pass

        except Exception as e:

            print(
                f"[USER] "
                f"describe failed: "
                f"{type(e).__name__}: {e}"
            )

    # -----------------------------------------
    # Base Info
    # -----------------------------------------

    async def GetBaseInfo(
        self,
        request,
        context,
    ):

        return service_pb2.BaseInfoResponse(
            started=True,
            core_version="nahan",
            node_version="bridge-1.0",
        )

    # -----------------------------------------
    # System Stats
    # -----------------------------------------

    async def GetSystemStats(
        self,
        request,
        context,
    ):

        return service_pb2.SystemStatsResponse(
            cpu_cores=1,
            cpu_usage=0,
            uptime=0,
        )

    # -----------------------------------------
    # Backend Stats
    # -----------------------------------------

    async def GetBackendStats(
        self,
        request,
        context,
    ):

        return service_pb2.BackendStatsResponse(
            uptime=0,
        )

    # -----------------------------------------
    # Stats
    # -----------------------------------------

    async def GetStats(
        self,
        request,
        context,
    ):

        try:

            request_name = getattr(
                request,
                "name",
                "",
            )

            request_reset = getattr(
                request,
                "reset",
                False,
            )

            request_type = getattr(
                request,
                "type",
                0,
            )

            print(
                f"[STATS REQUEST] "
                f"name={request_name} "
                f"type={request_type} "
                f"reset={request_reset}"
            )

        except Exception as e:

            print(
                f"[STATS REQUEST] "
                f"LOG ERROR: "
                f"{type(e).__name__}: {e}"
            )

            request_name = ""
            request_type = 0

        try:

            response = service_pb2.StatResponse()

            # =================================
            # type=4 = UsersStat
            # =================================

            if request_type == 4:

                print(
                    "[USERS STAT] "
                    "Fetching Nahan users..."
                )

                users_data = await self.nahan.users()

                print(
                    "[USERS STAT] "
                    f"python_type="
                    f"{type(users_data).__name__}"
                )

                print(
                    "[USERS STAT DATA] "
                    f"{users_data}"
                )

                if isinstance(
                    users_data,
                    dict,
                ):

                    users = users_data.get(
                        "users",
                        [],
                    )

                    print(
                        "[USERS STAT] "
                        f"users_count="
                        f"{len(users)}"
                    )

                    for user in users:

                        if not isinstance(
                            user,
                            dict,
                        ):
                            continue

                        user_name = str(
                            user.get(
                                "name",
                                "",
                            )
                        ).strip()

                        usage = user.get(
                            "usage",
                            {},
                        )

                        if not isinstance(
                            usage,
                            dict,
                        ):
                            usage = {}

                        total_usage = usage.get(
                            "total",
                            0,
                        )

                        try:

                            total_usage = int(
                                total_usage or 0
                            )

                        except Exception:

                            total_usage = 0

                        print(
                            "[USERS STAT] "
                            f"name={user_name} "
                            f"total={total_usage}"
                        )

                        if not user_name:
                            continue

                        response.stats.add(
                            name=user_name,
                            type="UserStat",
                            value=total_usage,
                        )

                return response

            # =================================
            # type=0 = Outbounds
            # =================================

            data = await self.nahan.stats()

            print(
                "[STATS RESPONSE] "
                f"python_type="
                f"{type(data).__name__}"
            )

            print(
                "[STATS DATA] "
                f"{data}"
            )

            if isinstance(
                data,
                dict,
            ):

                stats = data.get(
                    "stats",
                    {},
                )

                traffic = stats.get(
                    "traffic",
                    {},
                )

                total_requests = traffic.get(
                    "totalRequests",
                    0,
                )

                print(
                    "[STATS] "
                    f"totalRequests="
                    f"{total_requests}"
                )

                response.stats.add(
                    name="nahan",
                    type="Outbounds",
                    value=int(
                        total_requests or 0
                    ),
                )

            return response

        except Exception as e:

            print(
                "[STATS] Failed: "
                f"{type(e).__name__}: {e}"
            )

            return service_pb2.StatResponse()

    # -----------------------------------------
    # User Online Stats
    # -----------------------------------------

    async def GetUserOnlineStats(
        self,
        request,
        context,
    ):

        print(
            "[ONLINE REQUEST] "
            f"name={getattr(request, 'name', '')}"
        )

        return service_pb2.OnlineStatResponse(
            name=getattr(
                request,
                "name",
                "",
            ),
            value=0,
        )

    # -----------------------------------------
    # User Online IP List
    # -----------------------------------------

    async def GetUserOnlineIpListStats(
        self,
        request,
        context,
    ):

        print(
            "[ONLINE IP REQUEST] "
            f"name={getattr(request, 'name', '')}"
        )

        return service_pb2.StatsOnlineIpListResponse(
            name=getattr(
                request,
                "name",
                "",
            ),
            ips={},
        )

    # -----------------------------------------
    # Sync User
    # -----------------------------------------

    async def SyncUser(
        self,
        request_iterator,
        context,
    ):

        print(
            "[SYNC USER] "
            "request received"
        )

        try:

            async for user in request_iterator:

                self._describe_user(
                    user,
                    "SyncUser",
                )

        except Exception as e:

            print(
                "[SYNC USER] "
                f"Failed: "
                f"{type(e).__name__}: {e}"
            )

        return service_pb2.Empty()

    # -----------------------------------------
    # Sync Users
    # -----------------------------------------

    async def SyncUsers(
        self,
        request,
        context,
    ):

        print(
            "[SYNC USERS] "
            "request received"
        )

        try:

            users = getattr(
                request,
                "users",
                [],
            )

            print(
                "[SYNC USERS] "
                f"count={len(users)}"
            )

            for user in users:

                self._describe_user(
                    user,
                    "SyncUsers",
                )

        except Exception as e:

            print(
                "[SYNC USERS] "
                f"Failed: "
                f"{type(e).__name__}: {e}"
            )

        return service_pb2.Empty()

    # -----------------------------------------
    # Sync Users Chunked
    # -----------------------------------------

    async def SyncUsersChunked(
        self,
        request_iterator,
        context,
    ):

        print(
            "[SYNC USERS CHUNKED] "
            "request received"
        )

        try:

            async for chunk in request_iterator:

                users = getattr(
                    chunk,
                    "users",
                    [],
                )

                index = getattr(
                    chunk,
                    "index",
                    0,
                )

                last = getattr(
                    chunk,
                    "last",
                    False,
                )

                print(
                    "[SYNC USERS CHUNKED] "
                    f"index={index} "
                    f"count={len(users)} "
                    f"last={last}"
                )

                for user in users:

                    self._describe_user(
                        user,
                        "SyncUsersChunked",
                    )

        except Exception as e:

            print(
                "[SYNC USERS CHUNKED] "
                f"Failed: "
                f"{type(e).__name__}: {e}"
            )

        return service_pb2.Empty()

    # -----------------------------------------
    # Start
    # -----------------------------------------

    async def Start(
        self,
        request,
        context,
    ):

        print(
            "[NODE] "
            "Start requested"
        )

        # فقط برای بررسی اتصال Nahan
        # و مشاهده کاربران موجود.
        try:

            users_data = await self.nahan.users()

            print(
                "[NAHAN USERS] "
                f"python_type="
                f"{type(users_data).__name__}"
            )

            print(
                "[NAHAN USERS DATA] "
                f"{users_data}"
            )

        except Exception as e:

            print(
                "[NAHAN USERS] Failed: "
                f"{type(e).__name__}: {e}"
            )

        return service_pb2.BaseInfoResponse(
            started=True,
            core_version="nahan",
            node_version="bridge-1.0",
        )

    # -----------------------------------------
    # Stop
    # -----------------------------------------

    async def Stop(
        self,
        request,
        context,
    ):

        print(
            "[NODE] "
            "Stop requested"
        )

        return service_pb2.Empty()


# =============================================
# Create gRPC Server
# =============================================

async def create_server():

    if not os.path.exists(
        CERT_FILE
    ):

        raise RuntimeError(
            f"Certificate file not found: "
            f"{CERT_FILE}"
        )

    if not os.path.exists(
        KEY_FILE
    ):

        raise RuntimeError(
            f"Private key file not found: "
            f"{KEY_FILE}"
        )

    if not API_KEY:

        raise RuntimeError(
            "API_KEY is not configured"
        )

    with open(
        KEY_FILE,
        "rb",
    ) as f:

        private_key = f.read()

    with open(
        CERT_FILE,
        "rb",
    ) as f:

        certificate = f.read()

    credentials = (
        grpc.ssl_server_credentials(
            (
                (
                    private_key,
                    certificate,
                ),
            )
        )
    )

    server = grpc.aio.server(
        interceptors=[
            AuthInterceptor()
        ]
    )

    service_pb2_grpc.add_NodeServiceServicer_to_server(
        NodeService(),
        server,
    )

    return server, credentials

بعد از جایگزینی، Deploy مجدد Bridge را بزن.

وقتی بالا آمد، در PasarGuard یک بار صفحه را Refresh کن. مهم‌ترین چیزی که باید در لاگ ببینیم این است:

[STATS REQUEST] name= type=4 reset=True
[USERS STAT] Fetching Nahan users...
[USERS STAT] users_count=3
[USERS STAT] name=... total=...

اگر این‌ها ظاهر شدند، کد واقعاً دارد مصرف کاربران Nahan را دریافت می‌کند و آن‌وقت نتیجه‌ای که PasarGuard نمایش می‌دهد را بررسی می‌کنیم.
