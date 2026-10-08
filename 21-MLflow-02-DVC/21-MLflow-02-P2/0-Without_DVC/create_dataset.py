from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
import pandas as pd
import os

vars = {"random_state": 42, "test_size": 0.2}

# Load Wine dataset
wine = load_wine()


# Divide the dataset into dates and label
wine_ds = pd.DataFrame(wine.data, columns=wine.feature_names)  # type: ignore
wine_ds["label"] = wine.target  # type: ignore


# Be sure to put a number in the random state otherwise the sets will be different each time the program is ran.
train, test = train_test_split(
    wine_ds, test_size=vars["test_size"], random_state=vars["random_state"]
)


# Save The Wine dataset (this will need to be version controlled by DVC)
print("\n ✅ Saving dataset")


os.makedirs("data", exist_ok=True)
train.to_csv("data/train.csv", index=False)
test.to_csv("data/test.csv", index=False)


# Save the variables we used
print("\n ✅ Saving some metadata")

with open("data/dataset_parameters.yaml", "w") as f:
    f.write("\n".join(f"{k}: {v}" for k, v in vars.items()))

print("\n 🚀 Done \n")
