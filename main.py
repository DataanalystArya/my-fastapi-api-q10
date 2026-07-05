import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

EMAIL = "24f2000456@ds.study.iitm.ac.in"

# Allowed Origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app-hqeluh.example.com",
        "https://exam.sanand.workers.dev",
        "https://dash-j0c4z9.example.com",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIMIT = 12
WINDOW = 10

clients = defaultdict(list)


@app.middleware("http")
async def middleware(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # ⭐ IMPORTANT: endpoint se pehle state me save karo
    request.state.request_id = request_id

    # Rate Limit
    client = request.headers.get("X-Client-Id", "anonymous")

    now = time.time()

    clients[client] = [
        t for t in clients[client]
        if now - t < WINDOW
    ]

    if len(clients[client]) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
