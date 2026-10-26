from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, ConfigDict, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression

iris = load_iris()
model = LogisticRegression(max_iter=200).fit(iris.data, iris.target)  # type: ignore

# --------------------
# --------------------
# constant configs
SECRET, ALG = "k" * 40, "HS256"
ISS, AUD = "mlsecops", "ml-api"
USER, PASSWORD = "alice", "alice-secret-123"
# For prod envs, use Vault (or a secret manager) for SECRET. Database for USER/PASSWORD.
# Note that ALG, ISS, AUD stay in code or config.
# --------------------
# --------------------

Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]


oauth2 = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    errors = [
        {"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse({"detail": errors}, status_code=422)


# --------------------
# --------------------
#  login endpoint
@app.post("/token")
def token(
    form: OAuth2PasswordRequestForm = Depends(),
):  # Without Depends, FastAPI would treat `form` as a query parameter (?form=...) and fail to parse the form body.
    if form.username != USER or form.password != PASSWORD:
        raise HTTPException(401, "Incorrect username or password")
    now = datetime.now(timezone.utc)
    tok = jwt.encode(
        payload={
            "sub": USER,
            "iss": ISS,
            "aud": AUD,
            "iat": now,  # iat comes from issued at. It is the moment the token was created.
            "exp": now + timedelta(minutes=15),
        },
        key=SECRET,
        algorithm=ALG,
    )
    return {"access_token": tok, "token_type": "bearer"}


# --------------------
# --------------------
# dependency: verify token
# Indeed, token in and then username out.
# This function answer to this question: Is this token valid? Who is it for? Are they allowed?
def current_user(token: str = Depends(oauth2)) -> str:
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
    return claims["sub"]


@app.post("/predict")
def predict(
    body: PredictRequest, user: str = Depends(current_user)
):  # With Depends(current_user) the route is protected
    label = model.predict([body.features])[0]
    return {"label": int(label), "user": user}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
