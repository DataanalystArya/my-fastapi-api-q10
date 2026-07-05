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
    expose_headers=["X-Request-ID"],
)

LIMIT = 12
WINDOW = 10

clients = defaultdict(list)


@app.middleware("http")
async def middleware(request: Request, call_next):

    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    # Endpoint se pehle save
    request.state.request_id = request_id

    response = await call_next(request)

    # SAME value response header me bhejo
    response.headers["X-Request-ID"] = request.state.request_id

    return response


@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }
