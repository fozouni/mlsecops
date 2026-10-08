import mlflow
import mlflow.sklearn
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
)

print("\n ✅ Loading test dataset \n")
test = pd.read_csv("data/test.csv")
X_test = test.drop("label", axis=1)
y_test = test.label
print("\n ✅ Loading model \n")
clf = joblib.load("models/SVC/model")


mlflow.set_experiment("SVC-model-testing")

# Get model info
with open("models/SVC/model_parameters.yaml", "r") as f:
    run_info = {line.split(":")[0].strip(): line.split(":")[1].strip() for line in f}

print(f"\n ✅ Run info: {run_info} \n")


with mlflow.start_run(run_name="MLflow-2-P2") as run:
    # Set same runName so we can easily see it in MlFlow
    # mlflow.set_tag("mlflow.runName", run_info.get("run_name")+"LOVE")

    mlflow.set_tag("session", "MLflow-2-DVC")

    print("\n ✅ Evaluating model \n")

    input_example = X_test.head(3)

    mlflow.sklearn.log_model(  # type: ignore
        sk_model=clf,
        name="SVC",
        input_example=input_example,
        registered_model_name="Support Vector Classification",
    )

    predictions = clf.predict(X_test)
    cm = confusion_matrix(y_test, predictions, labels=clf.classes_)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=clf.classes_)
    disp.plot()
    # Save the confusion matrix, so that we can then save it in mlflow as an artifact
    plt.savefig("models/SVC/confusion_matrix.png")
    plt.close()

    # Determine the feature importances (how important each feature is for the final assessment)
    perm_importance = permutation_importance(clf, X_test, y_test)
    sorted_idx = perm_importance.importances_mean.argsort()  # type: ignore
    features = X_test.columns
    plt.barh(features[sorted_idx], perm_importance.importances_mean[sorted_idx])  # type: ignore
    plt.xlabel("Permutation Importance")
    plt.gcf().set_size_inches(20, 10)
    plt.savefig("models/SVC/feature_importances.png")
    plt.close()

    # Calculate the scores
    scores_acc = accuracy_score(y_test, predictions)
    scores_prec = precision_score(y_test, predictions, average="weighted")
    scores_recall = recall_score(y_test, predictions, average="weighted")

    mlflow.log_metric("accuracy", scores_acc)  # type: ignore
    mlflow.log_metric("precision", scores_prec)  # type: ignore
    mlflow.log_metric("recall", scores_recall)  # type: ignore
    mlflow.log_artifact("models/SVC/confusion_matrix.png")
    mlflow.log_artifact("models/SVC/feature_importances.png")
    # Save model ID and metrics to a text file
    metrics = mlflow.get_run(run.info.run_id).data.metrics
    print("Metrics", metrics)
    with open("models/SVC/metrics.yaml", "w") as f:
        f.write(f"Run ID: {run.info.run_id}\n")
        f.write("\n".join(f"{k}: {v}" for k, v in metrics.items()))

print("\n 🚀 Done")
