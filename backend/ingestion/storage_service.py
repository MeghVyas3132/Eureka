import os
import uuid
from datetime import datetime

import boto3

from core.config import get_settings

settings = get_settings()

USE_LOCAL_STORAGE = settings.use_local_storage
LOCAL_UPLOAD_DIR = settings.local_upload_dir
S3_BUCKET = settings.s3_bucket_name
AWS_REGION = settings.aws_region


def _build_s3_key(import_type: str, file_format: str, original_filename: str) -> str:
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    unique_id = uuid.uuid4().hex[:8]
    safe_name = original_filename.replace(" ", "_")
    return f"imports/{import_type}/{date_prefix}/{unique_id}_{safe_name}"


async def archive_file(
    file_bytes: bytes,
    import_type: str,
    file_format: str,
    original_filename: str,
) -> str | None:
    try:
        if USE_LOCAL_STORAGE:
            os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
            key = _build_s3_key(import_type, file_format, original_filename)
            local_path = os.path.join(LOCAL_UPLOAD_DIR, key.replace("/", "_"))
            with open(local_path, "wb") as file_obj:
                file_obj.write(file_bytes)
            return local_path

        s3 = boto3.client("s3", region_name=AWS_REGION)
        key = _build_s3_key(import_type, file_format, original_filename)
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType="application/octet-stream",
            Metadata={
                "import_type": import_type,
                "original_filename": original_filename,
                "uploaded_at": datetime.utcnow().isoformat(),
            },
        )
        return key
    except Exception as exc:
        print(f"[WARN] File archiving failed: {exc}")
        return None
