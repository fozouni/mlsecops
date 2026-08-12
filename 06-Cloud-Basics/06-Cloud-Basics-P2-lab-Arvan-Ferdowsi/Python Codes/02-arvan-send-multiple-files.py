import os
import boto3
import logging

from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)


def upload_files_from_directory(directory):
    try:
        s3_resource = boto3.resource(
            "s3",
            endpoint_url="https://s3.ir-thr-at1.arvanstorage.ir",
        )

        bucket_name = "created-by-code-911116666"

        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):  # Check if it's a file
                object_name = filename  # Use the filename as the object name

                with open(file_path, "rb") as file:
                    s3_resource.Bucket(  # pyright: ignore[reportAttributeAccessIssue]
                        bucket_name
                    ).put_object(ACL="private", Body=file, Key=object_name)

                logging.info(f"File '{filename}' uploaded successfully")
    except Exception as e:
        logging.error(e)


# Specify the directory containing files to upload
directory_path = "C:\\Users\\User\\Desktop\\test"  # Change this to your directory
upload_files_from_directory(directory_path)
