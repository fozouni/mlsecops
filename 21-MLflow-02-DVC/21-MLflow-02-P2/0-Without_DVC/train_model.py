from sklearn.svm import SVC
import pandas as pd
import mlflow
import mlflow.sklearn
import joblib
import os

# Will create and set new experiment
mlflow.set_experiment("SVC-model-training")

# enable autologging
mlflow.sklearn.autolog()  # type: ignore
# mlflow.set_tracking_uri("http://localhost:5000")

# Load dataset
print("\n ✅ Loading train dataset \n")
train = pd.read_csv("data/train-v1.2.csv")
X_train = train.drop("label", axis=1)
y_train = train.label


# Train model
with mlflow.start_run() as run:
    print("\n ✅ Training model \n")
    clf = SVC(
        kernel="poly", probability=True
    )  # (JUST A BEST PRACTICE) If you used additional parameters then you should also save them in a file
    clf.fit(X_train, y_train)
    print("\n ✅ Saving model \n")
    os.makedirs("models/SVC", exist_ok=True)
    joblib.dump(clf, "models/SVC/model")
    print("\n ✅ Saving parameters \n")

    # Save the variables we used
    run_id = run.info.run_id
    run_name = mlflow.get_run(run_id).data.tags["mlflow.runName"]
    parameters = {"run_id": run_id, "run_name": run_name}

    # 🚩 Log the training dataset
    mlflow.log_param("dataset_name", "wine_training_data")
    mlflow.log_param("dataset_source", "data/train-v1.2.csv")
    mlflow.log_param("dataset_version", "v1.2")
    mlflow.log_param("dataset_size", len(train))
    mlflow.log_param("dataset_shape", f"{train.shape[0]}x{train.shape[1]}")

    with open("models/SVC/model_parameters.yaml", "w") as f:
        f.write("\n".join(f"{k}: {v}" for k, v in parameters.items()))


print("\n 🚀 Done")

""" 🚩🚩🚩

- Parameters (log_param) = Inputs to your model (hyperparameters) [String/Number/Bool]

- Metrics (log_metric) = Outputs from your model (performance) [Numeric only]

- Tags (set_tag) = Context about the run (metadata) [String only]

"""
