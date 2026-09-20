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

        if isinstance(data, dict):
            users = data.get("users", [])

            print(f"Nahan users count: {len(users)}")
            print(f"Nahan total: {data.get('total')}")

            for index, user in enumerate(users):
                if not isinstance(user, dict):
                    continue

                print(
                    f"Nahan user #{index + 1}: "
                    f"fields={list(user.keys())}"
                )

                usage = user.get("usage")

                if isinstance(usage, dict):
                    print(
                        f"Nahan user #{index + 1} usage fields: "
                        f"{list(usage.keys())}"
                    )

                print(
                    f"Nahan user #{index + 1} status type: "
                    f"{type(user.get('status')).__name__}"
                )

        else:
            print(
                f"Unexpected users response type: "
                f"{type(data).__name__}"
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
