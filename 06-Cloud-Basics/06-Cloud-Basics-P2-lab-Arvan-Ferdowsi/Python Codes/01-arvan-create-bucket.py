import boto3  # pip install boto3==1.43.54
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

# 🔴 Two important credentials are set in "C:\Users\User\.aws\credentials" file

try:
    s3_resource = boto3.resource(
        "s3",
        endpoint_url="https://s3.ir-thr-at1.arvanstorage.ir",
    )
except Exception as exc:
    logging.error(exc)
else:
    bucket_name = "created-by-code-911116666"

    try:
        bucket = s3_resource.Bucket(  # pyright: ignore[reportAttributeAccessIssue]
            bucket_name
        )
        bucket.create(ACL="public-read")
    except ClientError as exc:
        logging.error(exc)
