import time
import uuid
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

EMAIL = "24f2000456@ds.study.iitm.ac.in"

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Exam ke liye easiest
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ---------- Rate Limiter ----------
LIMIT = 12
WINDOW = 10

clients = defaultdict(list)

@app.middleware("http")
async def request_context(request: Request, call_next):

    # Request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # Rate limit
    client = request.headers.get("X-Client-Id", "anonymous")
    now = time.time()

    clients[client] = [t for t in clients[client] if now - t < WINDOW]

    if len(clients[client]) >= LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
        )

    clients[client].append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request.state.request_id

    return response


@app.get("/")
def home():
    return {"status": "ok"}


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
