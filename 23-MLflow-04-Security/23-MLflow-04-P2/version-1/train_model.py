from sklearn.svm import SVC
import pandas as pd
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from model_hash import sha256_dir
import yaml

with open("./params.yaml", "r") as f:
    config = yaml.safe_load(f)

mlflow.set_tracking_uri(config["mlflow_tracking_uri"])

mlflow.set_experiment("SVC-model-training")
# mlflow.autolog()
# mlflow.sklearn.autolog(log_models=False)

print("\n ✅ Loading train dataset \n")
train = pd.read_csv("data/train.csv")
X_train = train.drop("label", axis=1)
y_train = train.label


with mlflow.start_run() as run:

    print("\n ✅ Training model \n")

    clf = SVC(kernel="linear", probability=True)
    clf.fit(X_train, y_train)

    model_info = mlflow.sklearn.log_model(  # type: ignore
        sk_model=clf, name="svc_model", registered_model_name="SVCClassifier"
    )
    # For each run one version will be created

    #############################################################
    #############################################################
    #############################################################

    artifact_dir = mlflow.artifacts.download_artifacts(model_info.model_uri)  # type: ignore
    model_hash = sha256_dir(artifact_dir)
    mlflow.set_tag("model_sha256", model_hash)

    MlflowClient().set_model_version_tag(
        "SVCClassifier", model_info.registered_model_version, "model_sha256", model_hash  # type: ignore
    )
    # for each version one specific tag will be assigned.

    #############################################################
    #############################################################
    #############################################################

    print(f"\n ✅ Registered version: {model_info.registered_model_version} \n")
    print(f"\n ✅ MLflow artifact SHA-256: {model_hash} \n")

    run_id = run.info.run_id
    run_name = mlflow.get_run(run_id).data.tags["mlflow.runName"]

    parameters = {"run_id": run_id, "run_name": run_name}

    parameters_file_path = "model_parameters.yaml"
    with open(parameters_file_path, "w") as f:
        f.write("\n".join(f"{k}: {v}" for k, v in parameters.items()))

    mlflow.log_artifact(parameters_file_path)


print("\n 🚀 Done. ENJOY")
