import os
import asyncio
import grpc

from bridge.server import create_server
from bridge.nahan import NahanAPI


async def main():

    port = int(
        os.getenv("PORT", "62050")
    )

    print(
        "Starting Nahan-PasarGuard Bridge..."
    )

    print(
        "Testing Nahan API connection..."
    )

    try:
        nahan = NahanAPI()

        data = await nahan.users()

        print(
            "Nahan API connection: SUCCESS"
        )

        if isinstance(data, dict):

            users = data.get(
                "users",
                [],
            )

            print(
                f"Nahan users count: "
                f"{len(users)}"
            )

            print(
                f"Nahan total: "
                f"{data.get('total')}"
            )

            for index, user in enumerate(
                users
            ):

                if not isinstance(
                    user,
                    dict,
                ):
                    continue

                print(
                    f"Nahan user #{index + 1}: "
                    f"fields="
                    f"{list(user.keys())}"
                )

                usage = user.get(
                    "usage"
                )

                if isinstance(
                    usage,
                    dict,
                ):
                    print(
                        f"Nahan user #{index + 1} "
                        f"usage fields: "
                        f"{list(usage.keys())}"
                    )

                print(
                    f"Nahan user #{index + 1} "
                    f"status type: "
                    f"{type(user.get('status')).__name__}"
                )

        else:
            print(
                "Unexpected users response type: "
                f"{type(data).__name__}"
            )

    except Exception as e:

        print(
            "Nahan API connection: FAILED"
        )

        print(
            f"Error: "
            f"{type(e).__name__}: {e}"
        )

    server, credentials = await create_server()
    print("========== SERVER CA BEGIN ==========")

    try:
        with open(
            "/app/certs/server.crt",
            "r",
        ) as cert_file:
            print(cert_file.read())
    except Exception as e:
        print(
            f"Could not read certificate: "
            f"{type(e).__name__}: {e}"
        )

    print("=========== SERVER CA END ===========")

    server.add_secure_port(
        f"0.0.0.0:{port}",
        credentials,
    )

    print(
        f"PasarGuard Bridge TLS started "
        f"on port {port}"
    )

    await server.start()

    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(main())
