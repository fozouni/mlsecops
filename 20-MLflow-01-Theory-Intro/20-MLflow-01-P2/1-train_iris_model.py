import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score

# Load data
iris = load_iris()
X, y = iris.data, iris.target  # type: ignore

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

mlflow.set_tracking_uri("http://localhost:5000")

with mlflow.start_run():
    # Train model
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy}")

    # Log to MLflow
    # You can see these three logs on the UI of MLFlow.

    mlflow.log_metric("RegressionModelAccuracy", accuracy)  # type: ignore

    mlflow.log_param("random_state", 42)

    # 🚩 The following snippet makes a model.skops for us to be used in model inference in the future.

    mlflow.sklearn.log_model(model, name="RegressionModel")  # type: ignore
