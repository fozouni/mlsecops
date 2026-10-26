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

# --------------------
# --------------------
# username: (password, allowed scopes)
USERS = {
    "alice": ("alice-secret-123", {"predict"}),
    "admin": ("admin-secret-123", {"predict", "admin"}),
}
# --------------------
# --------------------

Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]


oauth2 = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "predict": "call /predict",
        "admin": "read model info",
    },  # Pay attention to this line
)
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse({"detail": errors}, status_code=422)


@app.post("/token")
def token(form: OAuth2PasswordRequestForm = Depends()):
    entry = USERS.get(form.username)
    if entry is None or not hmac.compare_digest(form.password, entry[0]):
        # hmac.compare_digest instead of != (constant-time; timing-safe)
        raise HTTPException(401, "Incorrect username or password")
    allowed = entry[1]
    # least privilege. The client may ASK for scopes, but only gets
    # the intersection with what the server says they are allowed to have.
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
    return {
        "access_token": tok,
        "token_type": "bearer",
        "scope": " ".join(granted),
    }  # report granted scopes


def current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2)) -> str:
    # `security_scopes` is filled by FastAPI from Security(current_user, scopes=[...]) on each route.
    try:
        claims = jwt.decode(
            jwt=token,
            key=SECRET,
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

    # Do NOT trust the token's scopes alone. Intersect with the server record
    effective = set(claims.get("scopes", [])) & USERS[user][1]

    for need in security_scopes.scopes:
        if need not in effective:
            raise HTTPException(403, "Insufficient scope")
    return user


@app.post("/predict")
def predict(
    body: PredictRequest, user: str = Security(current_user, scopes=["predict"])
):  # Security(...) instead of Depends(...). Same thing, plus scopes.
    label = model.predict([body.features])[0]
    return {"label": int(label), "user": user}


@app.get("/admin/model-info")  # NEW route
def model_info(user: str = Security(current_user, scopes=["admin"])):
    return {
        "classes": list(map(int, model.classes_)),
        "n_features": int(model.n_features_in_),
        "coef_shape": list(model.coef_.shape),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
