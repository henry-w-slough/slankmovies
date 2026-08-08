import httpx


async def send_request(connection: httpx.AsyncClient, method: str, url: str, *args, **kwargs) -> httpx.Response | None:

    try:
        response = await connection.request(
            method,
            url,
            *args,
            **kwargs
        )

        response.raise_for_status()

        return response

    except httpx.HTTPStatusError as e:
        print("==============================================")
        print(f"Exception caught during '{method}' to '{url}'")
        print("-------------Its---------------------------------")
        print(f"Status Code: '{e.response.status_code}'")
        print("----------------------------------------------")
        print(f"Exception Text: '{e.response.text}'")
        print("==============================================")

    