from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
import uvicorn

iris = load_iris()
model = LogisticRegression(max_iter=200).fit(iris.data, iris.target)  # type: ignore


# --------------------
# --------------------
class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")  # unknown keys -> 422
    features: list[float] = Field(min_length=4, max_length=4)  # exactly 4


# --------------------
# --------------------

app = FastAPI()


@app.post("/predict")
def predict(body: PredictRequest):
    label = model.predict([body.features])[
        0
    ]  # Note that here we get features from body
    # print(body.features)
    # print(body)
    return {"label": int(label)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
