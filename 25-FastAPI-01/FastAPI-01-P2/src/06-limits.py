import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Annotated

import hmac
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

SECRET, ALG = "k" * 40, "HS256"
ISS, AUD = "mlsecops", "ml-api"
USERS = {
    "alice": ("alice-secret-123", {"predict"}),
    "admin": ("admin-secret-123", {"predict", "admin"}),
}

# --------------------
# --------------------
MAX_BYTES, LIMIT, WINDOW = 16_384, 5, 60  # Note that 16_384 bytes = 16 KB
hits: dict[str, deque] = defaultdict(deque)
# --------------------
# --------------------

Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]


oauth2 = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={"predict": "call /predict", "admin": "read model info"},
)
app = FastAPI()


# -------------------------------------------------
# -------------------------------------------------
# middleware: body-size limit
@app.middleware("http")
async def limit_body(request: Request, call_next):
    n = request.headers.get("content-length")
    if n is not None and (not n.isdigit() or int(n) > MAX_BYTES):
        return JSONResponse({"detail": "Payload too large"}, status_code=413)
    return await call_next(request)


# -------------------------------------------------
# ---------- safe 422 ----------------------------
@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse({"detail": errors}, status_code=422)


# -------------------------------------------------
# -------------------------------------------------
# rate limit dependency
async def rate_limit(request: Request):
    key = request.client.host if request.client else "unknown"
    now, q = time.monotonic(), hits[key]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= LIMIT:
        raise HTTPException(
            429, "Too many requests", headers={"Retry-After": str(WINDOW)}
        )
    q.append(now)


# -------------------------------------------------
# ---------- auth ---------------------------------
@app.post(
    "/token", dependencies=[Depends(rate_limit)]
)  # /token is rate-limited, otherwise an attacker floods logins.
def token(form: OAuth2PasswordRequestForm = Depends()):
    entry = USERS.get(form.username)
    if entry is None or not hmac.compare_digest(form.password, entry[0]):
        raise HTTPException(401, "Incorrect username or password")
    allowed = entry[1]
    requested = set(form.scopes) or {"predict"}
    granted = sorted(requested & allowed)
    if not granted:
        raise HTTPException(400, "No scopes granted")
    now = datetime.now(timezone.utc)
    tok = jwt.encode(
        {
            "sub": form.username,
            "scopes": granted,
            "iss": ISS,
            "aud": AUD,
            "iat": now,
            "exp": now + timedelta(minutes=15),
        },
        SECRET,
        ALG,
    )
    return {"access_token": tok, "token_type": "bearer", "scope": " ".join(granted)}


def current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2)) -> str:
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
    user = claims["sub"]
    if user not in USERS:
        raise HTTPException(401, "Could not validate credentials")
    effective = set(claims.get("scopes", [])) & USERS[user][1]
    for need in security_scopes.scopes:
        if need not in effective:
            raise HTTPException(403, "Insufficient scope")
    return user


@app.post("/predict", dependencies=[Depends(rate_limit)])
def predict(
    body: PredictRequest, user: str = Security(current_user, scopes=["predict"])
):
    label = model.predict([body.features])[0]
    return {"label": int(label), "user": user}


@app.get("/admin/model-info", dependencies=[Depends(rate_limit)])
def model_info(user: str = Security(current_user, scopes=["admin"])):
    return {
        "classes": list(map(int, model.classes_)),
        "n_features": int(model.n_features_in_),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
