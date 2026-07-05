import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

EMAIL = "24f2000456@ds.study.iitm.ac.in"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # exam ke liye easiest
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

LIMIT = 12
WINDOW = 10

clients = defaultdict(list)


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # -------- Request ID --------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # -------- Rate Limit --------
    client_id = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    clients[client_id] = [
        t for t in clients[client_id]
        if now - t < WINDOW
    ]

    if len(clients[client_id]) >= LIMIT:
        response = JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )
        response.headers["Retry-After"] = str(WINDOW)
        response.headers["X-Request-ID"] = request_id
        return response

    clients[client_id].append(now)

    response = await call_next(request)

    # Echo request id
    response.headers["X-Request-ID"] = request_id

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
