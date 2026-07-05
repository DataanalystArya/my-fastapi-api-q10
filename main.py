import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "24f2000456@ds.study.iitm.ac.in"

LIMIT = 12
WINDOW = 10

ALLOWED_ORIGIN = "https://app-hqeluh.example.com"

clients = defaultdict(list)


def cors_headers(origin: str | None):
    headers = {
        "Access-Control-Expose-Headers": "X-Request-ID",
    }
    if origin == ALLOWED_ORIGIN:
        headers["Access-Control-Allow-Origin"] = origin
    return headers


@app.middleware("http")
async def middleware(request: Request, call_next):

    origin = request.headers.get("origin")

    # ---------- Preflight ----------
    if request.method == "OPTIONS":
        resp = Response(status_code=200)
        if origin == ALLOWED_ORIGIN:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "*"
            resp.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
        return resp

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    # ---------- Rate Limit ----------
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        resp = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        resp.headers["Retry-After"] = str(WINDOW)
        resp.headers["X-Request-ID"] = request_id

        if origin == ALLOWED_ORIGIN:
            resp.headers["Access-Control-Allow-Origin"] = origin

        return resp

    clients[client].append(now)

    response = await call_next(request)

    # ---------- Response headers ----------
    response.headers["X-Request-ID"] = request_id

    if origin == ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
