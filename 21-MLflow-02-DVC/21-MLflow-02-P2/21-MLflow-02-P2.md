# Using DVC beside MLflow

[toc]

## Initialize git and DVC

```bash
git init

dvc init

touch .gitignore # or New-Item .gitignore

echo "mlruns/" >> .gitignore
echo "models/" >> .gitignore
echo "mlflow.db" >> .gitignore
```



## Install libraries 

We need some libraries in our dedicated`.mlflow` virtual env

```bash
pip install pandas
pip install matplotlib
pip install scikit-learn
pip install -i https://mirror-pypi.runflare.com/simple dvc==3.67.1 dvc-s3==3.3.0
```



## Project Structure

We should have a project tree like this:

```bash
/21-MLflow-02-P2
  - /models
    - /SVC
  - /data
  - create_dataset.py
  - train_model.py
  - eval_model.py
```



## Create ML pipeline with DVC



### First add one stage for data creation and management:

```bash
dvc stage add -n create_dataset `
  -d create_dataset.py `
  -o data/train.csv `
  -o data/test.csv `
  -o data/dataset_parameters.yaml `
  python create_dataset.py
```



**Now you can run `dvc repro` to see what will happen 👌.**



### Second we add another step for model training:

```bash
dvc stage add -n train_model `
    -d data/train.csv `
    -d train_model.py `
    -o models/SVC/model `
    -o models/SVC/model_parameters.yaml `
    python train_model.py
```



**Now you can run `dvc repro` to see what will happen 👌.**



### Third we add another step for model evaluation:

```bash
dvc stage add -n eval_model `
  -d eval_model.py `
  -d data/test.csv `
  -d models/SVC/model `
  -o models/SVC/metrics.yaml `
  -o models/SVC/confusion_matrix.png `
  -o models/SVC/feature_importances.png `
  python eval_model.py
```

**Now you can run `dvc repro` to see what will happen 👌.**



## See the `dvc.yaml` file

```yaml
stages:
  create_dataset:
    cmd: python create_dataset.py
    deps:
    - create_dataset.py
    outs:
    - data/dataset_parameters.yaml
    - data/test.csv
    - data/train.csv
  train_model:
    cmd: python train_model.py
    deps:
    - data/train.csv
    - train_model.py
    outs:
    - models/SVC/model
    - models/SVC/model_parameters.yaml
  eval_model:
    cmd: python eval_model.py
    deps:
    - data/test.csv
    - eval_model.py
    - models/SVC/model
    outs:
    - models/SVC/confusion_matrix.png
    - models/SVC/feature_importances.png
    - models/SVC/metrics.yaml
```



## Visualize the pipeline

```bash
dvc dag

dvc dag -o
```



## Commit your project

```bash
git add .  

git commit -m "My first ML pipeline with DVC and MLFlow"
```



## Make one small change

In the `create_dateset.py` file change the `random_state` parameter to a different number (e.g. 422) and attempt to commit.

```bash
dvc repro
# This will rerun some affected stages in your pipeline

git add .

git commit -m "My second dataset is used"
```



## Get back our previous Data using DVC

```bash
git log --oneline

git checkout <commit-hash>

dvc checkout

# 🚀 ENJOY
```

