"""Helper functions for communicating with the Storagegrid S3 system"""

from __future__ import annotations

import boto3
from botocore.config import Config
from django.conf import settings


def get_storagegrid_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.STORAGEGRID_ENDPOINT_URL,
        aws_access_key_id=settings.STORAGEGRID_ACCESS_KEY_ID,
        aws_secret_access_key=settings.STORAGEGRID_SECRET_ACCESS_KEY,
        region_name=settings.STORAGEGRID_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def generate_presigned_download_url(
    *,
    bucket: str,
    key: str,
    filename: str | None = None,
    expires_in: int | None = None,
) -> str:
    params = {
        "Bucket": bucket,
        "Key": key,
    }

    if filename:
        params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

    return get_storagegrid_client().generate_presigned_url(
        ClientMethod="get_object",
        Params=params,
        ExpiresIn=expires_in or settings.PORTAL_DATA_SIGNED_URL_TTL_SECONDS,
    )
