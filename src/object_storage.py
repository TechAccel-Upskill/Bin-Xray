from __future__ import annotations

import os
import posixpath
import time
import uuid
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class PresignedUpload:
    object_key: str
    upload_url: str
    download_url: str
    expires_in: int


class ObjectStorage:
    def __init__(self, bucket: str, client: Any):
        self.bucket = bucket
        self.client = client

    @staticmethod
    def from_env() -> Optional["ObjectStorage"]:
        bucket = os.getenv("BINXRAY_S3_BUCKET", "").strip()
        if not bucket:
            return None

        try:
            boto3 = importlib.import_module("boto3")
        except Exception as exc:
            raise RuntimeError(
                "boto3 is required for object storage. Install dependencies with: pip install -r requirements.txt"
            ) from exc

        kwargs: Dict[str, Any] = {}
        region = os.getenv("BINXRAY_S3_REGION", "").strip()
        endpoint = os.getenv("BINXRAY_S3_ENDPOINT", "").strip()
        access_key = os.getenv("BINXRAY_S3_ACCESS_KEY", "").strip()
        secret_key = os.getenv("BINXRAY_S3_SECRET_KEY", "").strip()

        if region:
            kwargs["region_name"] = region
        if endpoint:
            kwargs["endpoint_url"] = endpoint
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key

        client = boto3.client("s3", **kwargs)
        return ObjectStorage(bucket=bucket, client=client)

    def build_object_key(self, file_name: str, prefix: str = "uploads") -> str:
        safe_name = Path(file_name).name or "input.bin"
        stamp = int(time.time())
        token = uuid.uuid4().hex[:12]
        joined = posixpath.join(prefix.strip("/"), f"{stamp}-{token}-{safe_name}")
        return joined

    def presign_upload(self, object_key: str, content_type: str = "application/octet-stream", expires_in: int = 900) -> PresignedUpload:
        upload_url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        download_url = self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
        return PresignedUpload(
            object_key=object_key,
            upload_url=upload_url,
            download_url=download_url,
            expires_in=expires_in,
        )

    def presign_download(self, object_key: str, expires_in: int = 900) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )
