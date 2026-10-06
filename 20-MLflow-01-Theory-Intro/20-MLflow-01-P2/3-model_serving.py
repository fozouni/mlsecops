import mlflow
import mlflow.pyfunc
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 🚩 Just for Testing use this approach:

# RUN_ID = "acf613548516407f9525e9e4c26d9ee2"
# model = mlflow.pyfunc.load_model(f"runs:/{RUN_ID}/logistic_regression_model")

################################
# 🚩 pyfunc = MLflow's "one interface fits all" for model loading and prediction
################################

# 🚩 For production environment, use the following one:

model = mlflow.pyfunc.load_model("models:/registered_logistic_regression_model/latest")

iris = load_iris()
X = iris.data  # type: ignore
y = iris.target  # type: ignore

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("\n 🚩 Predictions \n")

predictions = model.predict(X_test)
print(f"Test set predictions: {predictions}")
print(f"Actual labels: {y_test}")

accuracy = accuracy_score(y_test, predictions)
print(f"Accuracy: {accuracy:.4f}")  # 4 digits after the decimal point

class_names = ["Setosa", "Versicolor", "Virginica"]

print("\n 🚩 Predicted classes: \n")

for i, pred in enumerate(predictions):
    actual_class = class_names[y_test[i]]
    predicted_class = class_names[int(pred)]
    print(f"Sample {i+1}: Predicted={predicted_class}, Actual={actual_class}")


print("\n 🚩 Classification Report: \n")

print(classification_report(y_test, predictions, target_names=class_names))


print("\n 🚩 Custom Test Examples \n")

custom_tests = np.array(
    [[4.9, 3.0, 1.4, 0.2], [6.2, 2.9, 4.3, 1.3], [7.3, 2.9, 6.3, 1.8]]
)

custom_predictions = model.predict(custom_tests)
for i, pred in enumerate(custom_predictions):
    features = custom_tests[i]
    predicted_class = class_names[int(pred)]
    print(f"Features {features} -> Predicted: {predicted_class}")
