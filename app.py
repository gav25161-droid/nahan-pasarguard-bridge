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
        data = await nahan.users()

        print("Nahan API connection: SUCCESS")
        print(f"Nahan users response type: {type(data).__name__}")

        if isinstance(data, dict):
            print(f"Nahan users keys: {list(data.keys())}")

            users = data.get("users", [])

            print(f"Nahan users count: {len(users)}")

            if users:
                first_user = users[0]

                print(
                    f"First user type: "
                    f"{type(first_user).__name__}"
                )

                if isinstance(first_user, dict):
                    print(
                        f"First user keys: "
                        f"{list(first_user.keys())}"
                    )

                    for key, value in first_user.items():
                        if isinstance(value, dict):
                            print(
                                f"Field '{key}' keys: "
                                f"{list(value.keys())}"
                            )

                        elif isinstance(value, list):
                            print(
                                f"Field '{key}' type: list, "
                                f"count: {len(value)}"
                            )

                        else:
                            print(
                                f"Field '{key}' type: "
                                f"{type(value).__name__}"
                            )

        elif isinstance(data, list):
            print(f"Nahan users count: {len(data)}")

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
