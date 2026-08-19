import httpx
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

class LLMProxyService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        await self.client.aclose()

    async def proxy_request(
        self, 
        provider_url: str, 
        headers: dict, 
        payload: dict
    ) -> StreamingResponse:
        clean_headers = {
            "Authorization": headers.get("authorization"),
            "Content-Type": "application/json"
        }

        try:
            req = self.client.build_request(
                "POST", 
                provider_url, 
                headers=clean_headers, 
                json=payload
            )
            response = await self.client.send(req, stream=True)
            
            if response.status_code != 200:
                error_body = await response.aread()
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Upstream provider error: {error_body.decode()}"
                )

            async def stream_generator() -> AsyncGenerator[bytes, None]:
                async for chunk in response.aiter_bytes():
                    yield chunk
                await response.aclose()

            return StreamingResponse(
                stream_generator(), 
                status_code=response.status_code,
                media_type=response.headers.get("content-type", "application/json")
            )

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Gateway connection error to upstream provider: {str(exc)}"
            )

proxy_service = LLMProxyService()
