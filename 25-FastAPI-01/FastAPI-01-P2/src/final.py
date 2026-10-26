import hashlib, hmac, os, time, uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from pydantic import BaseModel, ConfigDict, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

iris = load_iris()

model = LogisticRegression(max_iter=200).fit(iris.data, iris.target)  # type: ignore

SECRET, ALG = (
    os.urandom(32).hex(),
    "HS256",
)  # random per run; env var in prod or use Vault
ISS, AUD = "mlsecops", "ml-api"
MAX_BYTES, LIMIT, WINDOW, TOKEN_MIN = 16_384, 30, 60, 15
W, B = None, None  # not used; placeholder


# ----------------------------------------------------------
# ----------------------------------------------------------
# User store with hashed passwords:
# each user is created with a random salt and a scrypt hash, never the plaintext.
# Timing-safe login:
# an unknown username is hashed against a dummy record, so the response time can't reveal which usernames exist.


def scrypt(pw: str, salt: bytes) -> bytes:
    return hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)


@dataclass(frozen=True)
class User:
    username: str
    salt: bytes
    hash: bytes
    scopes: frozenset


def mk(n: str, p: str, s: set[str]) -> User:
    salt = os.urandom(16)
    return User(n, salt, scrypt(p, salt), frozenset(s))


USERS = {
    "alice": mk("alice", "alice-secret-123", {"predict"}),
    "admin": mk("admin", "admin-secret-123", {"predict", "admin"}),
}
DUMMY = mk("dummy", "dummy-password-for-timing", set())
# DUMMY is for timing protection
# make "user doesn't exist" take exactly as long as "wrong password",
# so the response time doesn't reveal which usernames are real.

# Timing leaks are a recon technique. The attacker doesn't gain access yet. They gather information to plan the attack.

# --------------------------------------------------------
# -------------------------------------------------------
#  schema
Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]


# --------------------------------------------------------
# --------------------------------------------------------
#  limiter
hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request):
    key = request.client.host if request.client else "unknown"
    now, q = time.monotonic(), hits[key]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= LIMIT:
        raise HTTPException(
            429, "Too many requests", headers={"Retry-After": str(WINDOW)}
        )
    q.append(now)


# --------------------------------------------------------
# --------------------------------------------------------
#  auth

oauth2 = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"predict": "call /predict", "admin": "read model info"},
)


# To get a valid token without calling /token.
def issue(user: User, scopes: list[str]) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": user.username,
            "scopes": scopes,
            "iss": ISS,
            "aud": AUD,
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_MIN),
        },
        SECRET,
        ALG,
    )


def current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2)) -> User:
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
    user = USERS.get(claims["sub"])
    if user is None:
        raise HTTPException(401, "Could not validate credentials")
    effective = set(claims.get("scopes", [])) & user.scopes
    for need in security_scopes.scopes:
        if need not in effective:
            raise HTTPException(403, "Insufficient scope")
    return user


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)  # docs OFF by default

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


@app.middleware("http")
async def guard(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    n = request.headers.get("content-length")
    if n is not None and (not n.isdigit() or int(n) > MAX_BYTES):
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers[k] = v
    response.headers["X-Request-ID"] = rid
    return response


@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    errs = [{"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse({"detail": errs}, status_code=422)


@app.exception_handler(Exception)
async def boom(request: Request, exc: Exception):
    return JSONResponse({"detail": "Internal server error"}, status_code=500)


# --------------------------------------------------------
# --------------------------------------------------------
#  routes
@app.get("/health")
def health():
    return {"status": "ok"}


# /token calls issue() so the "how to build a JWT" logic lives in one place. Tests reuse it.
@app.post("/token", dependencies=[Depends(rate_limit)])
def token(form: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form.username)
    target = user or DUMMY  # same work if user unknown
    ok = hmac.compare_digest(scrypt(form.password, target.salt), target.hash)
    if not (user and ok):
        raise HTTPException(401, "Incorrect username or password")
    requested = set(form.scopes) or {"predict"}
    granted = sorted(requested & user.scopes)
    if not granted:
        raise HTTPException(400, "No scopes granted")
    return {
        "access_token": issue(user, granted),
        "token_type": "bearer",
        "scope": " ".join(granted),
    }


@app.post("/predict", dependencies=[Depends(rate_limit)])
def predict(
    body: PredictRequest, user: User = Security(current_user, scopes=["predict"])
):
    label = model.predict([body.features])[0]
    return {"label": int(label), "user": user.username}


@app.get("/admin/model-info", dependencies=[Depends(rate_limit)])
def model_info(user: User = Security(current_user, scopes=["admin"])):
    return {
        "classes": list(map(int, model.classes_)),
        "n_features": int(model.n_features_in_),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
