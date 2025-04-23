import os
import json
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

S3_BUCKET = os.environ.get("S3_BUCKET")
S3_FILE_KEY = os.environ.get("S3_FILE_KEY", "trade_data.json")
LOCAL_FILE = "local_trade_data.json"

s3_client = boto3.client("s3")

def load_trade_data():
    if S3_BUCKET:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_FILE_KEY)
            return json.loads(response["Body"].read().decode("utf-8"))
        except (ClientError, NoCredentialsError, s3_client.exceptions.NoSuchKey):
            print("S3 unavailable or file missing, falling back to local.")
    try:
        with open(LOCAL_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_trade_data(data):
    if S3_BUCKET:
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=S3_FILE_KEY,
                Body=json.dumps(data).encode("utf-8"),
                ContentType="application/json"
            )
            return
        except (ClientError, NoCredentialsError):
            print("Failed to save to S3. Saving locally instead.")
    with open(LOCAL_FILE, "w") as f:
        json.dump(data, f, indent=2)
