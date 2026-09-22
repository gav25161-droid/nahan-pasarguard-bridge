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

API_KEY = os.getenv("API_KEY", "").strip()


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
            authorization == f"Bearer {expected}"
            or authorization == expected
            or api_key == expected
            or x_api_key == expected
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

    def _describe_user(self, user, source):

        try:
            email = getattr(
                user,
                "email",
                "",
            )

            inbounds = list(
                getattr(
                    user,
                    "inbounds",
                    [],
                )
            )

            print("")
            print("========== USER SYNC ==========")
            print(
                f"[SYNC] source={source}"
            )
            print(
                f"[SYNC] email={email}"
            )
            print(
                f"[SYNC] inbounds={inbounds}"
            )

            try:
                if user.proxies.HasField("vless"):

                    vless_id = getattr(
                        user.proxies.vless,
                        "id",
                        "",
                    )

                    flow = getattr(
                        user.proxies.vless,
                        "flow",
                        "",
                    )

                    print(
                        "[SYNC] proxy=vless"
                    )

                    print(
                        f"[SYNC] vless_id={vless_id}"
                    )

                    print(
                        f"[SYNC] flow={flow}"
                    )

            except Exception as e:

                print(
                    "[SYNC] VLESS inspect error:",
                    type(e).__name__,
                    str(e),
                )

            try:
                if user.proxies.HasField("vmess"):

                    vmess_id = getattr(
                        user.proxies.vmess,
                        "id",
                        "",
                    )

                    print(
                        "[SYNC] proxy=vmess"
                    )

                    print(
                        f"[SYNC] vmess_id={vmess_id}"
                    )

            except Exception:
                pass

            try:
                if user.proxies.HasField("trojan"):

                    password = getattr(
                        user.proxies.trojan,
                        "password",
                        "",
                    )

                    print(
                        "[SYNC] proxy=trojan"
                    )

                    print(
                        f"[SYNC] trojan_password_present="
                        f"{bool(password)}"
                    )

            except Exception:
                pass

            print(
                "========== END USER SYNC =========="
            )
            print("")

        except Exception as e:

            print(
                "[SYNC] Failed to inspect user:",
                type(e).__name__,
                str(e),
            )

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

    async def GetBackendStats(
        self,
        request,
        context,
    ):

        return service_pb2.BackendStatsResponse(
            uptime=0,
        )

    async def GetStats(
        self,
        request,
        context,
    ):

        try:

            request_type = int(
                request.type
            )

            print("")
            print(
                "================================"
            )

            print(
                f"[STATS REQUEST] "
                f"name={request.name} "
                f"type={request_type} "
                f"reset={request.reset}"
            )

            # --------------------------------
            # UsersStat = 4
            # --------------------------------

            if request_type == 4:

                print(
                    "[USERS STAT] "
                    "Fetching Nahan users..."
                )

                data = await self.nahan.users()

                print(
                    "[USERS STAT] "
                    f"python_type={type(data).__name__}"
                )

                print(
                    "[USERS STAT DATA]",
                    data,
                )

                response = (
                    service_pb2.StatResponse()
                )

                if not isinstance(
                    data,
                    dict,
                ):
                    print(
                        "[USERS STAT] "
                        "Invalid response type"
                    )

                    return response

                users = data.get(
                    "users",
                    [],
                )

                print(
                    f"[USERS STAT] "
                    f"users_count={len(users)}"
                )

                for user in users:

                    if not isinstance(
                        user,
                        dict,
                    ):
                        continue

                    user_id = user.get(
                        "id",
                        "",
                    )

                    user_name = user.get(
                        "name",
                        "",
                    )

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
                        f"[USERS STAT] "
                        f"name={user_name} "
                        f"id={user_id} "
                        f"total={total_usage}"
                    )

                    response.stats.add(
                        name=user_name,
                        type="UserStat",
                        link=user_id,
                        value=total_usage,
                    )

                print(
                    f"[USERS STAT] "
                    f"Returning "
                    f"{len(response.stats)} stats"
                )

                print(
                    "================================"
                )

                return response

            # --------------------------------
            # Other stat types
            # --------------------------------

            data = await self.nahan.stats()

            print(
                "[STATS RESPONSE] "
                f"python_type={type(data).__name__}"
            )

            print(
                "[STATS DATA]",
                data,
            )

            response = (
                service_pb2.StatResponse()
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

            print(
                "================================"
            )

            return response

        except Exception as e:

            print(
                "[STATS] Failed:",
                type(e).__name__,
                str(e),
            )

            return service_pb2.StatResponse()

    async def GetUserOnlineStats(
        self,
        request,
        context,
    ):

        print(
            f"[ONLINE] requested for "
            f"email={request.name}"
        )

        return service_pb2.OnlineStatResponse(
            name=request.name,
            value=0,
        )

    async def GetUserOnlineIpListStats(
        self,
        request,
        context,
    ):

        print(
            f"[ONLINE-IP] requested for "
            f"email={request.name}"
        )

        return (
            service_pb2.StatsOnlineIpListResponse(
                name=request.name,
            )
        )

    async def SyncUser(
        self,
        request_iterator,
        context,
    ):

        count = 0

        print(
            "[SYNC] "
            "SyncUser stream started"
        )

        async for user in request_iterator:

            count += 1

            self._describe_user(
                user,
                "SyncUser",
            )

        print(
            "[SYNC] "
            f"SyncUser stream finished, "
            f"users={count}"
        )

        return service_pb2.Empty()

    async def SyncUsers(
        self,
        request,
        context,
    ):

        users = request.users

        print(
            "[SYNC] "
            f"SyncUsers received, "
            f"users={len(users)}"
        )

        for user in users:

            self._describe_user(
                user,
                "SyncUsers",
            )

        return service_pb2.Empty()

    async def SyncUsersChunked(
        self,
        request_iterator,
        context,
    ):

        total = 0
        chunks = 0

        print(
            "[SYNC] "
            "SyncUsersChunked "
            "stream started"
        )

        async for chunk in request_iterator:

            chunks += 1

            print(
                f"[SYNC] Chunk #{chunks}: "
                f"users={len(chunk.users)} "
                f"index={chunk.index} "
                f"last={chunk.last}"
            )

            for user in chunk.users:

                total += 1

                self._describe_user(
                    user,
                    "SyncUsersChunked",
                )

        print(
            "[SYNC] "
            f"SyncUsersChunked finished, "
            f"chunks={chunks}, "
            f"users={total}"
        )

        return service_pb2.Empty()

    async def Start(
        self,
        request,
        context,
    ):

        print(
            "[NODE] Start requested"
        )

        return service_pb2.BaseInfoResponse(
            started=True,
            core_version="nahan",
            node_version="bridge-1.0",
        )

    async def Stop(
        self,
        request,
        context,
    ):

        print(
            "[NODE] Stop requested"
        )

        return service_pb2.Empty()


async def create_server():

    if not os.path.exists(
        CERT_FILE
    ):

        raise RuntimeError(
            f"TLS certificate not found: "
            f"{CERT_FILE}"
        )

    if not os.path.exists(
        KEY_FILE
    ):

        raise RuntimeError(
            f"TLS private key not found: "
            f"{KEY_FILE}"
        )

    if not API_KEY:

        raise RuntimeError(
            "API_KEY is not configured"
        )

    with open(
        CERT_FILE,
        "rb",
    ) as cert_file:

        certificate = (
            cert_file.read()
        )

    with open(
        KEY_FILE,
        "rb",
    ) as key_file:

        private_key = (
            key_file.read()
        )

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

    (
        service_pb2_grpc
        .add_NodeServiceServicer_to_server(
            NodeService(),
            server,
        )
    )

    return server, credentials
