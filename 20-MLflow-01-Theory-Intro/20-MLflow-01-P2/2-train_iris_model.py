import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

""" 🚩
MLflow ===> experiment tracking,
scikit-learn ===> machine learning components,
numpy ===> numerical operations
"""

iris = load_iris()
X = iris.data  # type: ignore
y = iris.target  # type: ignore

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

sample_input = X_train[:1]

""" 🚩
sample_input variable captures one training example to use later as an input example for the model.
X_train[:1] selects the first row of the X_train array or DataFrame.
"""

print(f"✅ X_train is  {X_train}")
print(f"✅ Sample input is  {sample_input}")

mlflow.set_experiment("iris_experiments")

with mlflow.start_run(run_name="logistic_regression_iris_final"):
    # 🚩 Everything inside this block will be tracked as part of a single experiment run.
    solver = "lbfgs"  # 🚩 Go to https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html to see other options
    max_iter = 200  # 🚩 Maximum iterations for convergence
    random_state = 42  # 🚩 Seed for reproducibility

    # 🚩 The next three lines just logs the three abve parameters
    mlflow.log_param("solver", solver)
    mlflow.log_param("max_iter", max_iter)
    mlflow.log_param("random_state", random_state)
    mlflow.log_param("CourseName", "MLSecOps")

    """🚩
    Model Training
    A logistic regression model is created with the specified parameters and trained on the training data.
    """

    model = LogisticRegression(
        solver=solver, max_iter=max_iter, random_state=random_state
    )
    model.fit(X_train, y_train)

    # 🚩 Model Evaluation
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)  # 🚩 Overall correctness
    precision = precision_score(
        y_test, y_pred, average="weighted"
    )  # 🚩 How many positive predictions were actually correct (weighted average across classes)
    recall = recall_score(
        y_test, y_pred, average="weighted"
    )  # 🚩 How many actual positives were correctly identified (weighted average)
    f1 = f1_score(
        y_test, y_pred, average="weighted"
    )  # 🚩 Harmonic mean of precision and recall (weighted average)

    # 🚩 All calculated metrics are logged to MLflow for tracking and comparison.
    mlflow.log_metric("accuracy", accuracy)  # type: ignore
    mlflow.log_metric("precision", precision)  # type: ignore
    mlflow.log_metric("recall", recall)  # type: ignore
    mlflow.log_metric("f1_score", f1)  # type: ignore

    """ 🚩
    The trained model is saved to MLflow with a name and an input example.
    This allows the model to be loaded later for inference or deployment.
    """
    mlflow.sklearn.log_model(  # type: ignore
        model,
        name="logistic_regression_model",
        input_example=sample_input,  # 🚩 (Will be saved here) file:E:/MLSecOps/Contents/20-MLSecOps-MLflow-01-Theory-Intro/20-MLflow-01-P2/mlruns/1/models/m-2879b90dfd93437fba23528174df6a46/artifacts/serving_input_example.json
        registered_model_name="registered_logistic_regression_model",  # 🚩 In the next sessions of MLFlow, you will learn about how we can send these models to S3.
    )

    """ 🚩
    Tags are added to help organize and filter experiments.
    These provide metadata about the model type and dataset used.
    """
    mlflow.set_tag("model_type", "logistic_regression")
    mlflow.set_tag("dataset", "iris")
    # mlflow.set_tag("mlflow.runName", "MLFlow-1")

print(
    "✅ MLFlow Run completed. Open MLFlow UI at http:localhost:5000 to view the results"
)
