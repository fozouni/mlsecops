import hmac
import os
import sys
import tempfile

import mlflow
import mlflow.sklearn
import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException
from mlflow import MlflowClient
from pydantic import BaseModel

from model_hash import sha256_dir

MODEL_NAME = os.environ.get("MODEL_NAME", "SVCClassifier")
MODEL_VERSION = os.environ.get("MODEL_VERSION")


def die(msg: str, code: int = 3):
    print(f"REFUSING TO SERVE: {msg}", file=sys.stderr)
    sys.exit(code)


def load_verified_model():
    if not MODEL_VERSION:
        die("set MODEL_VERSION (e.g. 1)", 2)

    mv = MlflowClient().get_model_version(MODEL_NAME, MODEL_VERSION)  # type: ignore
    expected = mv.tags.get("model_sha256")
    if not expected:
        die(f"{MODEL_NAME} v{MODEL_VERSION} has no model_sha256 tag")

    local = mlflow.artifacts.download_artifacts(  # type: ignore
        artifact_uri=f"models:/{MODEL_NAME}/{MODEL_VERSION}",
        dst_path=tempfile.mkdtemp(prefix="verified-model-"),
    )

    actual = sha256_dir(local)
    if not hmac.compare_digest(actual, expected):  # type: ignore
        die(f"hash mismatch\n  expected {expected}\n  actual   {actual}")
    print(f"Hash OK ({actual[:16]}...) for {MODEL_NAME} v{MODEL_VERSION}")

    return mlflow.sklearn.load_model(local)  # type: ignore


model = load_verified_model()
features = list(getattr(model, "feature_names_in_", []))

app = FastAPI(title="Wine SVC")


class Batch(BaseModel):
    rows: list[list[float]]


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "version": MODEL_VERSION,
        "course": "MLSecOps by Dr. M.Fozouni",
    }


@app.post("/predict")
def predict(batch: Batch):
    if any(len(r) != len(features) for r in batch.rows):
        raise HTTPException(422, f"each row needs {len(features)} values: {features}")
    df = pd.DataFrame(batch.rows, columns=features)
    assert model is not None
    return {"predictions": [int(p) for p in model.predict(df)]}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.environ.get("SERVE_HOST", "0.0.0.0"),
        port=int(os.environ.get("SERVE_PORT", "8000")),
    )
