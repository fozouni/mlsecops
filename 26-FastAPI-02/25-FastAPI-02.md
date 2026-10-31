# FastAPI-02: Docker + Redis + SQLAlchemy + Compose + Traefik

After finalizing our API using FastAPI, now its time to get it to prod environment. In this tutorial I will show you this important matter. 

[toc]

## Project layout

```
fastapi-prod/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── seed.py
├── weights.json
└── app/
    ├── __init__.py
    ├── main.py
    └── db.py
```



## `requirements.txt`

```txt
fastapi==0.162.0
uvicorn[standard]==0.54.0
gunicorn==26.2.0
pydantic==2.14.1
pydantic-settings==2.16.2
pyjwt==2.15.1
python-multipart==0.0.32
scikit-learn==1.9.1
redis==8.1.0
slowapi==0.1.10
sqlalchemy[asyncio]==2.1.6
aiosqlite==0.22.1
asyncpg==0.32.0
```



## `app/db.py`

This file, **defines the database connection** and the `users` **table**.

```python
import os
from sqlalchemy import Column, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/users.db") 
#🚩 see the following note regarding this line

engine = create_async_engine(DATABASE_URL, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class UserRow(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True)
    salt = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    scopes = Column(String, nullable=False)   # space-separated


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```



> Regarding the line `DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/users.db")`:
>
> - **`os.getenv("DATABASE_URL", ...)`**, reads the `DATABASE_URL` environment variable.
> - If it's **set**, use it (e.g., your Postgres URL).
> - If it's **not set**, fall back to the default: **SQLite** at `./data/users.db`.
>
> ------
>
> **Example values:**
>
> - SQLite (default): `sqlite+aiosqlite:///./data/users.db`
> - Postgres: `postgresql+asyncpg://user:pass@host:5432/dbname`



## `app/__init__.py`

```python
# empty
```



> An empty `__init__.py` tells Python: **"treat this folder as a package."**



## `app/main.py`

```python
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
The leading underscore "_" is a Python convention for "internal use only."
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
```



## `seed.py`

This code, creates the initial users in the database. Without it, the `users` table is empty, and nobody can log in (`/auth/token` returns `401` for everyone).

> 🚩 Note that in real prod envs, we automate this phase **during** container initialization. 

```python
import asyncio, hashlib, os
from app.db import SessionLocal, UserRow, init_db

def scrypt(pw: str, salt: bytes) -> bytes:
    return hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

async def seed():
    await init_db()
    users = [
        ("alice", os.getenv("ALICE_PASSWORD", "alice-secret-123"), "predict"),
        ("admin", os.getenv("ADMIN_PASSWORD", "admin-secret-123"), "predict admin"),
    ]
    async with SessionLocal() as session:
        for name, pw, scopes in users:
            salt = os.urandom(16)
            session.add(UserRow(
                username=name, salt=salt.hex(),
                password_hash=scrypt(pw, salt).hex(), scopes=scopes,
            ))
        await session.commit()
    print(f"seeded {len(users)} users")

if __name__ == "__main__":
    asyncio.run(seed())
```



## `weights.json`

```json
{"w":[0.8,-0.4,0.3,1.1],"bias":-0.2}
```



## `Dockerfile`

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

RUN useradd -m appuser && mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser

COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

COPY app ./app
COPY seed.py ./seed.py
COPY weights.json ./weights.json

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "app.main:app"]
```



## `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"          
    environment:
      MLAPI_SECRET: "${MLAPI_SECRET}"
      MODEL_SHA256: "${MODEL_SHA256}"
      MODEL_PATH: "weights.json"
      REDIS_URL: "redis://redis:6379/0"
      DATABASE_URL: "sqlite+aiosqlite:////app/data/users.db"
      MAX_BYTES: "16384"
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--save", "", "--appendonly", "no"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped
```



## `.env` (create at project root, **never commit**)

```env
MLAPI_SECRET=paste output of 'python -c "import secrets;print(secrets.token_hex(32))"'
MODEL_SHA256=paste output of 'python -c "import hashlib;print(hashlib.sha256(open('weights.json','rb').read()).hexdigest())"'
```

> - `MLAPI_SECRET` = the JWT signing key (keep secret).
>
> - `MODEL_SHA256` = the model's fingerprint (integrity check).
>
> - Make root the owner of `.env`
>
>   ```bash
>   sudo chown root:root .env
>   ```
>
>   Lock it down (only root can read/write)
>
>   ```bash
>   sudo chmod 600 .env
>   ```
>
> - If we change any characters of `MODEL_SHA256` and `dc down -v` and then `dc up -d` the `app` service will through hash error and will not start at all.



## Run and Enjoy

### Build + start

```bash
docker compose --build

docker compose up -d

docker compose logs -f app
```



### Seed the DB

```bash
docker compose exec app python seed.py
```

**Expected:** `seeded 2 users`



### Test: happy path

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

curl -s -X POST localhost:8000/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}' -w '\n'
```

**Expected:** `{"label":1,"user":"alice"}`



### Test: rate limit hits Redis

```bash
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:8000/predict \
       -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
       -d '{"features":[5.1,3.5,1.4,0.2]}'
done; echo
```

**Expected:** 30 × `200`, then 5 × `429`.



### Test, scale up or down, rate limit still holds

First in the `docker-compose.yaml` file turn `8000:8000` into just '8000'. In this way, locally, docker assign a random port to the three new apps. Then 

```bash
docker compose down -v
```

Now do this:

```bash
docker compose up --scale app=3 -d

docker compose up --scale app=1 -d
```

Wait for 5 seconds. **Get a new token** (the old one is fine, but the rate-limit bucket is per-IP and shared via Redis). Rerun the flood:

```bash
# Pick one of: 56429, 56535, 55967
PORT=46657

# Get a token
TOKEN=$(curl -s -X POST localhost:$PORT/auth/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Flood — you will see 30 × 200, then 429
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code} " -X POST localhost:$PORT/predict \
       -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
       -d '{"features":[5.1,3.5,1.4,0.2]}'
done; echo
```

**Still 30 × `200` then `429`**, because Redis is the **shared counter across all 3 app containers.** This is the demo that proves Redis matters.



## What you have now

| Component                    | What it does                                               |
| :--------------------------- | :--------------------------------------------------------- |
| **App** (Gunicorn + Uvicorn) | Our API written by FastAPI                                 |
| **Redis**                    | shared rate-limit counters                                 |
| **SQLite via SQLAlchemy**    | user store (swap to Postgres via `DATABASE_URL`)           |
| **Model**                    | JSON weights, SHA-256-pinned, loaded once at startup       |
| **Port**                     | `127.0.0.1:8000`, **localhost only**, not public           |
| **Traefik** (in the sequel)  | Forward request from `api.elmedade.ir` to `127.0.0.1:8000` |



## Now put your api behind the reverse proxy

After `docker compose up -d` give you back the terminal, you can test by running

```bash
docker ps
```

to see if the containers are up and running. Now we go for Traefik and by running this command

```bash
sudo traefik --configfile=/etc/traefik/traefik.yml
```

we start the traefik server. Note that for `api.elmedade.ir` i should define of `A` record on Arvan panel.

If everything is ok, test by running the following commands:

```bash
# Send One request
# Get token
TOKEN=$(curl -s -X POST https://api.elmedade.ir/auth/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Predict
curl -s -X POST https://api.elmedade.ir/predict \
     -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d '{"features":[5.1,3.5,1.4,0.2]}' -w '\n'
```

```bash
# Send multiple request
# Get a fresh token
TOKEN=$(curl -s -X POST https://api.elmedade.ir/auth/token \
        -d 'username=alice&password=alice-secret-123&scope=predict' | \
        python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Flood /predict endpoint (limit is 30/min)
for i in $(seq 1 35); do
  curl -s -o /dev/null -w "%{http_code} " -X POST https://api.elmedade.ir/predict \
       -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
       -d '{"features":[5.1,3.5,1.4,0.2]}'
done; echo
```



## Final Notes:

1. The rootless mode generally reduce the speed. But this is only valid for old Linux Kernel. For example for `Ubuntu 24.04` this is little and negligible. 

2. Definitely, remove the `ubuntu` user from `docker` group. Because if we run this command

   ```bash
   ls -l /var/run/docker.sock
   ```

   we will see that `docker.socket` is owned by root and is in `docker` group. So any user in docker group can get access to this file. Now if the attackers get a shell session with `ubuntu` user on our server, they will break us completely by running the following command:

   ```bash
   docker run -v /:/host -it ubuntu chroot /host
   ```

   It means, they have the root filesystem of our host inside a running container and can do ANYTHING.

3. One good practice without rootless is this:

   i: remove `ubuntu` from `docker` group.

   ```bash
   sudo gpasswd -d ubuntu docker
   sudo systemctl restart docker
   newgrp docker
   
   # Now the follwoing command will not work 
   docker ps
   
   # This works
   sudo docker ps
   ```


   ii: Give `ubuntu` a password (so sudo will ask for it) [**🔴Do this as a practice🔴**]

​        So, now we have two layers of defence [`ubuntu` do not have `root` privileges and if attackers wanted to do anything harmful, need its password for sudo jobs].



![](.\Privilege-Escalation-Flow.png)
