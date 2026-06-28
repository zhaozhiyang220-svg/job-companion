import boto3
from botocore.config import Config
from mypy_boto3_s3.client import S3Client

from src.core.config import get_settings


def _client() -> S3Client:
    s = get_settings()
    return boto3.client(
        "s3",
        region_name=s.s3_region,
        endpoint_url=s.s3_endpoint_url or None,
        aws_access_key_id=s.s3_access_key_id,
        aws_secret_access_key=s.s3_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def presign_put(key: str, content_type: str, expires_in: int = 600) -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": get_settings().s3_bucket, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def presign_get(key: str, expires_in: int = 86400) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": get_settings().s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def download_bytes(key: str) -> bytes:
    obj = _client().get_object(Bucket=get_settings().s3_bucket, Key=key)
    return obj["Body"].read()
