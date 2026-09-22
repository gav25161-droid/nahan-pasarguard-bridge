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

            inbounds = list(
                getattr(
                    user,
                    "inbounds",
                    [],
                )
            )

            proxy_types = []

            try:
                if user.proxies.HasField(
                    "vless"
                ):
                    proxy_types.append(
                        "vless"
                    )

                    flow = getattr(
                        user.proxies.vless,
                        "flow",
                        "",
                    )

                    print(
                        f"[SYNC] {source} "
                        f"email={email} "
                        f"proxy=vless "
                        f"flow={'yes' if flow else 'no'} "
                        f"inbounds={len(inbounds)}"
                    )

            except Exception:
                pass

            try:
                if user.proxies.HasField(
                    "vmess"
                ):
                    proxy_types.append(
                        "vmess"
                    )
            except Exception:
                pass

            try:
                if user.proxies.HasField(
                    "trojan"
                ):
                    proxy_types.append(
                        "trojan"
                    )
            except Exception:
                pass

            try:
                if user.proxies.HasField(
                    "shadowsocks"
                ):
                    proxy_types.append(
                        "shadowsocks"
                    )
            except Exception:
                pass

            try:
                if user.proxies.HasField(
                    "wireguard"
                ):
                    proxy_types.append(
                        "wireguard"
                    )
            except Exception:
                pass

            try:
                if user.proxies.HasField(
                    "hysteria"
                ):
                    proxy_types.append(
                        "hysteria"
                    )
            except Exception:
                pass

            if "vless" not in proxy_types:

                print(
                    f"[SYNC] {source} "
                    f"email={email} "
                    f"proxy={','.join(proxy_types) if proxy_types else 'none'} "
                    f"inbounds={len(inbounds)}"
                )

        except Exception as e:

            print(
                f"[SYNC] Failed to inspect user: "
                f"{type(e).__name__}: {e}"
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
        # Debug information.
        # This does not change the returned statistics.
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
                "[STATS REQUEST] "
                f"name={request_name} "
                f"type={request_type} "
                f"reset={request_reset}"
            )

        except Exception as e:

            print(
                "[STATS REQUEST] "
                f"Failed to inspect request: "
                f"{type(e).__name__}: {e}"
            )

        try:
            data = await self.nahan.stats()

            print(
                "[STATS RESPONSE] "
                f"python_type={type(data).__name__}"
            )

            response = service_pb2.StatResponse()

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
                    f"totalRequests={total_requests}"
                )

                response.stats.add(
                    name="nahan",
                    type="Outbounds",
                    value=int(
                        total_requests or 0
                    ),
                )

            else:

                print(
                    "[STATS] "
                    "Nahan response is not a dict"
                )

            return response

        except Exception as e:

            print(
                f"[STATS] Failed: "
                f"{type(e).__name__}: {e}"
            )

            return service_pb2.StatResponse()

    async def GetUserOnlineStats(
        self,
        request,
        context,
    ):
        try:
            print(
                "[ONLINE] requested for "
                f"email={request.name}"
            )

        except Exception as e:

            print(
                "[ONLINE] request inspection failed: "
                f"{type(e).__name__}: {e}"
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
        try:
            print(
                "[ONLINE-IP] requested for "
                f"email={request.name}"
            )

        except Exception as e:

            print(
                "[ONLINE-IP] request inspection failed: "
                f"{type(e).__name__}: {e}"
            )

        return service_pb2.StatsOnlineIpListResponse(
            name=request.name,
        )

    async def SyncUser(
        self,
        request_iterator,
        context,
    ):
        count = 0

        print(
            "[SYNC] SyncUser stream started"
        )

        async for user in request_iterator:

            count += 1

            self._describe_user(
                user,
                "SyncUser",
            )

        print(
            "[SYNC] SyncUser stream finished, "
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
            "[SYNC] SyncUsers received, "
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
            "[SYNC] SyncUsersChunked "
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
            "[SYNC] SyncUsersChunked finished, "
            f"chunks={chunks}, users={total}"
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

        certificate = cert_file.read()

    with open(
        KEY_FILE,
        "rb",
    ) as key_file:

        private_key = key_file.read()

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
