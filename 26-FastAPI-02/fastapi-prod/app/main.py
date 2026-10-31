import hashlib, hmac, os, json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel, ConfigDict, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select

from .db import SessionLocal, UserRow, engine, init_db

# ----------------------------
# ---------- config ----------
SECRET = os.environ["MLAPI_SECRET"]
ALG = "HS256"
ISS, AUD = "mlsecops", "ml-api"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WEIGHTS = Path(os.getenv("MODEL_PATH", "weights.json"))
PINNED_SHA256 = os.environ["MODEL_SHA256"]
MAX_BYTES = int(os.getenv("MAX_BYTES", "16384"))
TOKEN_MIN = 15

"""🚩👆
os.environ["X"] ===> required.
os.getenv("X", default) ===> optional. 
"""


# ----------------------------
# ---------- model -----------
def load_weights(path: Path, pinned: str) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != pinned:
        raise RuntimeError("model artifact hash mismatch")
    return json.loads(raw)


def predict_label(weights: dict, features: list[float]) -> int:
    z = weights["bias"] + sum(w * x for w, x in zip(weights["w"], features))
    return int(1 / (1 + 2.718281828**-z) >= 0.5)


# ------------------------------
# ---------- password ----------
def scrypt(pw: str, salt: bytes) -> bytes:
    return hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)


DUMMY_SALT = os.urandom(16)
DUMMY_HASH = scrypt("dummy-password-for-timing", DUMMY_SALT)


# ---------------------------------
# ---------- schema ---------------
Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]


# ----------------------------------
# ---------- rate limiter ----------
limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)


# ----------------------------------
# ---------- lifespan --------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.weights = load_weights(WEIGHTS, PINNED_SHA256)
    yield
    await engine.dispose()


"""🚩👆
This block is the startup and shutdown logic for your app.
It runs once when the app starts, and once when it stops.
"""

# ------------------------------------
# ---------- define app --------------
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.state.limiter = limiter  # attaches the rate-limiter object to the app

"""🚩👆
docs_url=None, redoc_url=None, openapi_url=None turns off /docs, /redoc, and /openapi.json.
Because, in production, those pages reveal the entire API structure
(every endpoint, every parameter, every auth scheme). 
"""


# ------------------------------------
# ---------- errors ------------------
@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    errs = [{"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse({"detail": errs}, status_code=422)


@app.exception_handler(RateLimitExceeded)
async def rate_exceeded(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        {"detail": "Too many requests"}, status_code=429, headers={"Retry-After": "60"}
    )


# ------------------------------------
# ---------- middleware --------------
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",  # If a browser ever loads an error page or a JSON response as if it were HTML (misconfiguration), it won't execute scripts.
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",  # Prevents a proxy or browser from caching {"label":0,"user":"alice"}, which could be seen by another user.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


@app.middleware("http")
async def guard(request: Request, call_next):
    n = request.headers.get("content-length")
    if n is not None and (not n.isdigit() or int(n) > MAX_BYTES):
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    return response


"""🚩👆
🚩 A "middleware" is a function that works with every request before it is processed by any specific path operation.
And also with every response before returning it.

🚩 This middleware sits in front of every route and does two things:
Before: blocks bodies > 16 KB with 413.
After: adds 5 security headers to every response.
One function ===> every route protected.
"""

# ------------------------------------
# ---------- auth --------------------
oauth2 = OAuth2PasswordBearer(
    tokenUrl="auth/token",
    scopes={"predict": "call /predict", "admin": "read model info"},
)


def issue(username: str, scopes: list[str]) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": username,
            "scopes": scopes,
            "iss": ISS,
            "aud": AUD,
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_MIN),
        },
        SECRET,
        ALG,
    )


async def _lookup_user(username: str):
    async with SessionLocal() as session:
        return (
            await session.execute(select(UserRow).where(UserRow.username == username))
        ).scalar_one_or_none()


"""🚩👆
The leading underscore "_" is a Python convention for "internal use only".
It means: "This function is a private helper. Don't call it from outside this module."
"""


async def current_user(
    security_scopes: SecurityScopes, token: str = Depends(oauth2)
) -> str:
    try:
        claims = jwt.decode(
            token,
            SECRET,
            algorithms=[ALG],
            audience=AUD,
            issuer=ISS,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Could not validate credentials")

    row = await _lookup_user(claims["sub"])
    if row is None:
        raise HTTPException(401, "Could not validate credentials")

    allowed = set(row.scopes.split())
    effective = set(claims.get("scopes", [])) & allowed
    for need in security_scopes.scopes:
        if need not in effective:
            raise HTTPException(403, "Insufficient scope")
    return row.username  # type: ignore


# ------------------------------------
# ---------- routers -----------------
auth_router = APIRouter(prefix="/auth", tags=["auth"])
predict_router = APIRouter(tags=["predict"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

"""🚩👆
These lines are for better route management. They group related endpoints together (login, predict, admin),
keep the code organized, and make it easier to apply security rules or move a whole group later.
"""


@auth_router.post("/token")
@limiter.limit(
    "10/minute"
)  # Allow at most 10 requests to this endpoint per minute. The 11th request gets 429.
async def token(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    row = await _lookup_user(form.username)
    if row is not None:
        target_salt = bytes.fromhex(row.salt)  # type: ignore
        target_hash = bytes.fromhex(row.password_hash)  # type: ignore
    else:
        target_salt, target_hash = DUMMY_SALT, DUMMY_HASH
    ok = hmac.compare_digest(scrypt(form.password, target_salt), target_hash)
    if not (row and ok):
        raise HTTPException(401, "Incorrect username or password")

    allowed = set(row.scopes.split())
    requested = set(form.scopes) or {"predict"}
    granted = sorted(requested & allowed)
    if not granted:
        raise HTTPException(400, "No scopes granted")

    return {
        "access_token": issue(row.username, granted),  # type: ignore
        "token_type": "bearer",
        "scope": " ".join(granted),
    }


@predict_router.post("/predict")
@limiter.limit("30/minute")
async def predict(
    body: PredictRequest,
    request: Request,
    user: str = Security(current_user, scopes=["predict"]),
):
    label = predict_label(request.app.state.weights, body.features)
    return {"label": label, "user": user}


@admin_router.get("/model-info")
@limiter.limit("30/minute")
async def model_info(
    request: Request, user: str = Security(current_user, scopes=["admin"])
):
    return {"n_features": len(request.app.state.weights["w"])}


app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(admin_router)

"""
These three lines attach the three routers to the app, so their routes actually become part of the running server.
"""


@app.get("/health")
async def health():
    return {"status": "ok"}
