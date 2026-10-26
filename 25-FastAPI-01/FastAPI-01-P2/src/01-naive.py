from fastapi import FastAPI
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
import uvicorn

iris = load_iris()
model = LogisticRegression(max_iter=200).fit(iris.data, iris.target)  # type: ignore

app = FastAPI()


@app.post("/predict")
def predict(features: list[float]):
    label = model.predict([features])[0]
    return {"label": int(label)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
