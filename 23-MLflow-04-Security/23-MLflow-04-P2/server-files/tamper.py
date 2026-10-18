import os, sys, boto3
from mlflow import MlflowClient

BUCKET = "mlflow-bucket-33559418"
VERSION, mode = sys.argv[1], sys.argv[2]

mv = MlflowClient().get_model_version("SVCClassifier", VERSION)
print("version", VERSION, "-> run", mv.run_id)

s3 = boto3.client("s3", endpoint_url=os.environ["MLFLOW_S3_ENDPOINT_URL"])
keys = []
for page in s3.get_paginator("list_objects_v2").paginate(
    Bucket=BUCKET, Prefix="mlflow_artifacts/"
):
    keys += [o["Key"] for o in page.get("Contents", [])]
key = next(k for k in keys if mv.run_id in k and k.endswith("svc_model/model.skops"))
print("model file:", key)

backup = f"backup-v{VERSION}.skops"
if mode == "break":
    data = s3.get_object(Bucket=BUCKET, Key=key)["Body"].read()
    open(backup, "wb").write(data)
    s3.put_object(Bucket=BUCKET, Key=key, Body=data + b"X")
    print("Tampered. Backup saved as", backup)
else:
    s3.put_object(Bucket=BUCKET, Key=key, Body=open(backup, "rb").read())
    print("Restored.")
