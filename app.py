import os
import asyncio
import grpc

from bridge.server import create_server


async def main():
    port = int(os.getenv("PORT", "62050"))

    server = await create_server()

    server.add_insecure_port(f"0.0.0.0:{port}")

    print(f"PasarGuard Bridge started on port {port}")

    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())
