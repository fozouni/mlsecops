import shutil
import tempfile

import mlflow
import mlflow.sklearn
import pandas as pd
import yaml
from mlflow import MlflowClient
from sklearn.svm import SVC

from model_hash import sha256_dir

MODEL_NAME = "SVCClassifier"

with open("./params.yaml", "r") as f:
    config = yaml.safe_load(f)

mlflow.set_tracking_uri(config["mlflow_tracking_uri"])
mlflow.set_experiment("SVC-model-training")

print("\n ✅ Loading train dataset \n")
train = pd.read_csv("data/train.csv")
X_train = train.drop("label", axis=1)
y_train = train.label

# mlflow.sklearn.autolog(log_models=False)

with mlflow.start_run() as run:
    print("\n ✅ Training model \n")
    clf = SVC(kernel="linear", probability=True)
    clf.fit(X_train, y_train)

    # 1) Save the model to a LOCAL folder (nothing has left the laptop yet)
    local_dir = tempfile.mkdtemp(prefix="model-") + "/svc_model"
    mlflow.sklearn.save_model(clf, local_dir, input_example=X_train.head(3))  # type: ignore

    # 2) Hash those local files
    model_hash = sha256_dir(local_dir)
    print(f"\n ✅ Model SHA-256 (before upload): {model_hash} \n")

    # 3) Upload exactly those files to MLflow (the bucket in ARvan or even AWS)
    mlflow.log_artifacts(local_dir, artifact_path="svc_model")

    # 4) Register the uploaded files as a new model version
    mv = mlflow.register_model(f"runs:/{run.info.run_id}/svc_model", MODEL_NAME)

    # 5) Store the hash on the run and on the model version
    mlflow.set_tag("model_sha256", model_hash)
    MlflowClient().set_model_version_tag(
        MODEL_NAME, mv.version, "model_sha256", model_hash
    )

    MlflowClient().set_registered_model_alias(MODEL_NAME, "auth", mv.version)

    print(f"\n ✅ Registered version: {mv.version} \n")

    shutil.rmtree(local_dir, ignore_errors=True)

print("\n 🚀 Done")
