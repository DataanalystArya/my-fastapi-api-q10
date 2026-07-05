import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "24f2000456@ds.study.iitm.ac.in"

LIMIT = 12
WINDOW = 10

clients = defaultdict(list)


@app.middleware("http")
async def middleware(request: Request, call_next):

    # ---------- Handle CORS Preflight ----------
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Expose-Headers": "X-Request-ID",
            },
        )

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Rate Limiting ----------
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["Retry-After"] = str(WINDOW)
        response.headers["X-Request-ID"] = request_id
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"
        return response

    clients[client].append(now)

    response = await call_next(request)

    # ---------- Required Headers ----------
    response.headers["X-Request-ID"] = request_id
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "X-Request-ID"

    return response


@app.get("/")
async def home():
    return {"status": "ok"}


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }


@app.options("/ping")
async def options_ping():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Expose-Headers": "X-Request-ID",
        },
    )
