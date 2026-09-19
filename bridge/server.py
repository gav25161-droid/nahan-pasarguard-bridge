import grpc

from bridge import service_pb2
from bridge import service_pb2_grpc

from bridge.state import BridgeState
from bridge.nahan import NahanAPI


class NodeService(service_pb2_grpc.NodeServiceServicer):

    def __init__(self):
        self.state = BridgeState()
        self.nahan = NahanAPI()

    async def GetBaseInfo(self, request, context):
        return service_pb2.BaseInfoResponse(
            started=True,
            core_version="nahan",
            node_version="bridge-1.0",
        )

    async def GetSystemStats(self, request, context):
        return service_pb2.SystemStatsResponse(
            cpu_cores=1,
            cpu_usage=0,
            uptime=0,
        )

    async def GetBackendStats(self, request, context):
        return service_pb2.BackendStatsResponse(
            uptime=0,
        )

    async def GetStats(self, request, context):
        try:
            data = await self.nahan.stats()

            response = service_pb2.StatResponse()

            if isinstance(data, dict):
                stats = data.get("stats", {})

                traffic = stats.get("traffic", {})
                total_requests = traffic.get("totalRequests", 0)

                response.stats.add(
                    name="nahan",
                    type="Outbounds",
                    value=int(total_requests or 0),
                )

            return response

        except Exception:
            return service_pb2.StatResponse()

    async def GetUserOnlineStats(self, request, context):
        return service_pb2.OnlineStatResponse(
            name=request.name,
            value=0,
        )

    async def GetUserOnlineIpListStats(self, request, context):
        return service_pb2.StatsOnlineIpListResponse(
            name=request.name,
        )

    async def SyncUser(self, request_iterator, context):
        async for user in request_iterator:
            # فعلاً فقط دریافت می‌کنیم.
            # مرحله بعدی تبدیل User پاسارگارد به User نهان است.
            pass

        return service_pb2.Empty()

    async def SyncUsers(self, request, context):
        for user in request.users:
            # فعلاً فقط دریافت می‌کنیم.
            pass

        return service_pb2.Empty()

    async def SyncUsersChunked(self, request_iterator, context):
        async for chunk in request_iterator:
            for user in chunk.users:
                pass

        return service_pb2.Empty()

    async def Start(self, request, context):
        return service_pb2.BaseInfoResponse(
            started=True,
            core_version="nahan",
            node_version="bridge-1.0",
        )

    async def Stop(self, request, context):
        return service_pb2.Empty()


async def create_server():
    server = grpc.aio.server()

    service_pb2_grpc.add_NodeServiceServicer_to_server(
        NodeService(),
        server,
    )

    return server
