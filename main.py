import time
import uuid
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ---------- CHANGE THESE TWO ----------
EMAIL = "23f3001733@ds.study.iitm.ac.in"                       # your logged-in email
EXAM_ORIGIN = "https://PUT-EXAM-PAGE-ORIGIN-HERE"      # see note below

# ---------- Already set for you ----------
MY_ORIGIN = "https://app-x02zy1.example.com"
RATE_LIMIT = 15
WINDOW = 10

app = FastAPI()
hits = defaultdict(deque)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id") or request.client.host
        now = time.monotonic()
        q = hits[client_id]
        while q and now - q[0] >= WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return JSONResponse({"detail": "Too many requests"}, status_code=429)
        q.append(now)
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@app.get("/ping")
async def ping(request: Request):
    return {"email": EMAIL, "request_id": request.state.request_id}


# Last added = outermost. Order: CORS -> Context -> RateLimit -> endpoint
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[MY_ORIGIN, EXAM_ORIGIN],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["X-Request-ID", "X-Client-Id", "Content-Type"],
    expose_headers=["X-Request-ID"],
)
