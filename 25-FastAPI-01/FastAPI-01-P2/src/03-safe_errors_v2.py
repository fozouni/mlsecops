# 03_safe_errors.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
import uvicorn
from typing import Annotated

iris = load_iris()
model = LogisticRegression(max_iter=200).fit(iris.data, iris.target)  # type: ignore

# --------------------
# --------------------
Feature = Annotated[float, Field(ge=0.0, le=10.0, allow_inf_nan=False)]
# give me 4 numbers, each between 0 and 10, and no NaN/Infinity
# Annotated[X, info] means: "a value of type X, with extra info attached"


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: Annotated[list[Feature], Field(min_length=4, max_length=4)]
    # features: list[float] = Field(min_length=4, max_length=4)


# --------------------
# --------------------

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def bad_input(request: Request, exc: RequestValidationError):
    # Return only where + why. Never echo the rejected value.
    errors = [
        {"loc": [str(p) for p in e["loc"]], "msg": e["msg"]} for e in exc.errors()
    ]
    return JSONResponse({"detail": errors}, status_code=422)


@app.post("/predict")
def predict(body: PredictRequest):
    label = model.predict([body.features])[0]
    return {"label": int(label)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
