# File Name: storage.py
# Description: Pluggable storage backend for uploaded files (local disk or Cloudflare R2).
# Created At: 2026-11-13
# Created By: AI Agent

"""Storage abstraction used by upload/ingest/export services.

The database keeps storing URL strings (``/uploads/questions/x.png`` locally or
``https://files.example.com/questions/x.png`` on R2), so switching backends does
not require a schema change.
"""

from __future__ import annotations

import functools
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.core import config

# STORAGE_BACKEND values that mean Cloudflare R2 (S3-compatible API).
REMOTE_BACKENDS = frozenset({"r2", "cloud", "s3"})


def _clean_key(key: str) -> str | None:
    """Normalize a storage key and reject empty/path-traversal keys."""
    key = (key or "").replace("\\", "/").strip("/")
    if not key:
        return None
    parts = key.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return None
    return key


def _is_not_found_error(exc: Exception) -> bool:
    """True for S3 ``ClientError`` 404/NoSuchKey responses (and local FileNotFoundError)."""
    if isinstance(exc, FileNotFoundError):
        return True
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    error = response.get("Error") or {}
    code = str(error.get("Code") or "") if isinstance(error, dict) else ""
    if code in ("404", "NoSuchKey", "NotFound"):
        return True
    metadata = response.get("ResponseMetadata") or {}
    status = metadata.get("HTTPStatusCode") if isinstance(metadata, dict) else None
    return str(status) == "404"


class Storage:
    """Base interface for a file storage backend."""

    backend: str = "base"

    def put(self, key: str, data: bytes, content_type: str | None = None) -> None:
        raise NotImplementedError

    def get(self, key: str) -> bytes:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def url(self, key: str) -> str:
        raise NotImplementedError

    def key_from_url(self, url: str) -> str | None:
        raise NotImplementedError

    def size(self, key: str) -> int:
        """Object size in bytes (default implementation reads the object)."""
        return len(self.get(key))


class LocalStorage(Storage):
    """Store objects under a local root directory and serve them under a URL prefix."""

    backend = "local"

    def __init__(self, root: Path, url_prefix: str = "/uploads"):
        self.root = Path(root)
        self._root_path = self.root.resolve()
        self.url_prefix = (url_prefix or "/uploads").rstrip("/") or "/uploads"

    def _path(self, key: str) -> Path:
        clean = _clean_key(key)
        if clean is None:
            raise ValueError(f"Invalid storage key: {key!r}")
        path = (self._root_path / clean).resolve()
        try:
            path.relative_to(self._root_path)
        except ValueError as exc:
            raise ValueError(f"Storage key escapes root: {key!r}") from exc
        return path

    def put(self, key: str, data: bytes, content_type: str | None = None) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def path_for(self, key: str) -> Path:
        """Absolute filesystem path for a key (local backend only)."""
        return self._path(key)

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def url(self, key: str) -> str:
        clean = _clean_key(key)
        if clean is None:
            raise ValueError(f"Invalid storage key: {key!r}")
        return f"{self.url_prefix}/{clean}"

    def key_from_url(self, url: str) -> str | None:
        if not url or not isinstance(url, str):
            return None
        path = unquote(urlsplit(url).path or "")
        if not path:
            return None
        if not path.startswith("/"):
            path = "/" + path

        prefix = "/" + self.url_prefix.strip("/")
        if path.startswith(prefix + "/"):
            return _clean_key(path[len(prefix) + 1:])

        # Legacy SGK figures were served from /sgk-images but live under uploads/sgk_images.
        legacy_prefix = "/sgk-images"
        if path.startswith(legacy_prefix + "/"):
            return _clean_key("sgk_images/" + path[len(legacy_prefix) + 1:])
        return None

    def size(self, key: str) -> int:
        return self._path(key).stat().st_size


class R2Storage(Storage):
    """Store objects in a Cloudflare R2 bucket through the S3-compatible API."""

    backend = "r2"

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        public_base_url: str,
    ):
        # boto3 is an optional dependency: only import it when R2 is actually used.
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:  # pragma: no cover - exercised only without boto3 installed
            raise RuntimeError(
                "boto3 is required when STORAGE_BACKEND=r2; install it with "
                "`pip install 'boto3>=1.34'`."
            ) from exc

        self.bucket = bucket
        self.public_base_url = (public_base_url or "").rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            region_name="auto",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
        )

    def _key(self, key: str) -> str:
        clean = _clean_key(key)
        if clean is None:
            raise ValueError(f"Invalid storage key: {key!r}")
        return clean

    def put(self, key: str, data: bytes, content_type: str | None = None) -> None:
        self._client.put_object(
            Bucket=self.bucket,
            Key=self._key(key),
            Body=data,
            ContentType=content_type or "application/octet-stream",
        )

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=self._key(key))
        except Exception as exc:  # botocore.exceptions.ClientError on missing keys
            if _is_not_found_error(exc):
                raise FileNotFoundError(f"Stored object not found: {key}") from exc
            raise
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._key(key))
            return True
        except Exception as exc:  # botocore.exceptions.ClientError on missing keys
            if _is_not_found_error(exc):
                return False
            raise

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=self._key(key))

    def url(self, key: str) -> str:
        return f"{self.public_base_url}/{self._key(key)}"

    def key_from_url(self, url: str) -> str | None:
        if not url or not isinstance(url, str) or not self.public_base_url:
            return None
        prefix = self.public_base_url + "/"
        if not url.startswith(prefix):
            return None
        key = url[len(prefix):].split("?", 1)[0].split("#", 1)[0]
        return _clean_key(unquote(key))

    def size(self, key: str) -> int:
        try:
            response = self._client.head_object(Bucket=self.bucket, Key=self._key(key))
        except Exception as exc:
            if _is_not_found_error(exc):
                raise FileNotFoundError(f"Stored object not found: {key}") from exc
            raise
        return int(response.get("ContentLength", 0))


@functools.lru_cache(maxsize=1)
def get_storage() -> Storage:
    """Return the configured storage backend (cached for the process lifetime)."""
    backend = (config.STORAGE_BACKEND or "local").strip().lower()
    if backend in REMOTE_BACKENDS:
        required = (
            ("R2_ACCOUNT_ID", config.R2_ACCOUNT_ID),
            ("R2_ACCESS_KEY_ID", config.R2_ACCESS_KEY_ID),
            ("R2_SECRET_ACCESS_KEY", config.R2_SECRET_ACCESS_KEY),
            ("R2_BUCKET", config.R2_BUCKET),
            # Without a public base URL every stored URL would be a bare "/key" that
            # nothing serves, so treat it as required too.
            ("R2_PUBLIC_BASE_URL", config.R2_PUBLIC_BASE_URL),
        )
        missing = [name for name, value in required if not (value or "").strip()]
        if missing:
            raise RuntimeError(
                f"STORAGE_BACKEND={backend} requires these environment variables: "
                + ", ".join(missing)
            )
        return R2Storage(
            account_id=config.R2_ACCOUNT_ID,
            access_key_id=config.R2_ACCESS_KEY_ID,
            secret_access_key=config.R2_SECRET_ACCESS_KEY,
            bucket=config.R2_BUCKET,
            public_base_url=config.R2_PUBLIC_BASE_URL,
        )
    return LocalStorage(config.UPLOAD_ROOT)


# Keep a direct reference so reset_storage() still works when tests monkeypatch get_storage.
_get_storage_cached = get_storage


def reset_storage() -> None:
    """Clear the cached backend (used by tests and after config changes)."""
    _get_storage_cached.cache_clear()


def is_remote_backend() -> bool:
    """True when STORAGE_BACKEND selects R2/cloud/S3 instead of local disk."""
    return (config.STORAGE_BACKEND or "local").strip().lower() in REMOTE_BACKENDS


def read_bytes_from_url(url: str) -> bytes:
    """Read an object's bytes from the configured storage backend via its stored URL."""
    storage = get_storage()
    key = storage.key_from_url(url)
    if not key:
        raise FileNotFoundError(f"Unsupported storage URL: {url!r}")
    try:
        return storage.get(key)
    except FileNotFoundError:
        raise
    except Exception as exc:
        if _is_not_found_error(exc):
            raise FileNotFoundError(f"Stored object not found: {key}") from exc
        raise
