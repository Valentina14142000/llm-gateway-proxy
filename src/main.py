from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from src.services.proxy_service import proxy_service
from src.middleware.auth_limit import RateLimitMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await proxy_service.close()

app = FastAPI(
    title="Enterprise LLM Gateway",
    version="1.0.0",
    lifespan=lifespan
)

# Register the distributed rate-limiting middleware (60 requests per minute default)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

@app.post("/v1/chat/completions")
async def handle_chat_completion(request: Request):
    body = await request.json()
    upstream_url = "https://api.openai.com/v1/chat/completions"
    auth_header = request.headers.get("Authorization", "")
    
    return await proxy_service.proxy_request(
        provider_url=upstream_url,
        headers={"authorization": auth_header},
        payload=body
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "llm-gateway-proxy"}
