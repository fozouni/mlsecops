from sklearn.svm import SVC
import pandas as pd
import mlflow
import mlflow.sklearn
import joblib
import os

#############################################################
#############################################################
#############################################################

import yaml

with open("./params.yaml", "r") as f:
    config = yaml.safe_load(f)

mlflow.set_tracking_uri(config["mlflow_tracking_uri"])

#############################################################
#############################################################
#############################################################

mlflow.set_experiment("SVC-model-training")

# enable autologging
# mlflow.sklearn.autolog()


# Load dataset
print("\n ✅ Loading train dataset \n")
train = pd.read_csv("data/train.csv")
X_train = train.drop("label", axis=1)
y_train = train.label


# Train model
with mlflow.start_run() as run:
    print("\n ✅ Training model \n")
    clf = SVC(kernel="linear", probability=True)
    clf.fit(X_train, y_train)

    print("\n ✅ Saving model locally and logging to MLflow \n")
    os.makedirs("models/SVC", exist_ok=True)
    joblib.dump(clf, "models/SVC/model")  # Save locally

    mlflow.sklearn.log_model(  # type: ignore
        sk_model=clf, name="svc_model", registered_model_name="SVCClassifier"
    )

    print("\n ✅ Saving parameters locally and logging to MLflow \n")
    # Save the variables we used
    run_id = run.info.run_id
    run_name = mlflow.get_run(run_id).data.tags["mlflow.runName"]
    parameters = {"run_id": run_id, "run_name": run_name}

    # Save the parameters to a local YAML file
    parameters_file_path = "models/SVC/model_parameters.yaml"
    with open(parameters_file_path, "w") as f:
        f.write("\n".join(f"{k}: {v}" for k, v in parameters.items()))

    # --- NEW: Log the local YAML file as an artifact ---
    mlflow.log_artifact(parameters_file_path)


print("\n 🚀 Done")
