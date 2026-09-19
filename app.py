import os
import asyncio
import grpc

from bridge.server import create_server
from bridge.nahan import NahanAPI


async def main():
    port = int(os.getenv("PORT", "62050"))

    print("Testing Nahan API connection...")

    try:
        nahan = NahanAPI()
        users = await nahan.users()

        print("Nahan API connection: SUCCESS")
        print(f"Nahan users response type: {type(users).__name__}")

        if isinstance(users, dict):
            print(f"Nahan users keys: {list(users.keys())}")

        elif isinstance(users, list):
            print(f"Nahan users count: {len(users)}")

        else:
            print(
                f"Nahan users value type: "
                f"{type(users).__name__}"
            )

    except Exception as e:
        print("Nahan API connection: FAILED")
        print(f"Error: {type(e).__name__}: {e}")

    server = await create_server()

    server.add_insecure_port(
        f"0.0.0.0:{port}"
    )

    print(
        f"PasarGuard Bridge started on port {port}"
    )

    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())
