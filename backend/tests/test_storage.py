# File Name: test_storage.py
# Description: Unit tests for the pluggable storage backend (local disk and Cloudflare R2).
# Created At: 2026-11-13
# Created By: AI Agent

import sys
import types
from pathlib import Path

import pytest

from app.core import config
from app.core import storage as storage_module
from app.core.storage import (
    LocalStorage,
    R2Storage,
    get_storage,
    read_bytes_from_url,
    reset_storage,
)


@pytest.fixture(autouse=True)
def _clear_storage_cache():
    """Keep the lru_cache from leaking a backend/config between tests."""
    reset_storage()
    yield
    reset_storage()


# --------------------------------------------------------------------------- local


def test_local_roundtrip_and_url_mapping(tmp_path):
    storage = LocalStorage(tmp_path)

    storage.put("questions/q_img_abc.png", b"png-bytes", "image/png")

    assert (tmp_path / "questions" / "q_img_abc.png").read_bytes() == b"png-bytes"
    assert storage.get("questions/q_img_abc.png") == b"png-bytes"
    assert storage.exists("questions/q_img_abc.png") is True
    assert storage.size("questions/q_img_abc.png") == len(b"png-bytes")

    assert storage.url("questions/q_img_abc.png") == "/uploads/questions/q_img_abc.png"
    assert storage.key_from_url("/uploads/questions/q_img_abc.png") == "questions/q_img_abc.png"
    assert storage.key_from_url(
        "https://example.test/uploads/questions/q_img_abc.png"
    ) == "questions/q_img_abc.png"
    assert storage.key_from_url("/sgk-images/ch1/p1.png") == "sgk_images/ch1/p1.png"
    assert storage.key_from_url("/other/x.png") is None
    assert storage.key_from_url("https://example.test/other/x.png") is None
    assert storage.key_from_url("/uploads/../secret.txt") is None

    storage.delete("questions/q_img_abc.png")
    assert storage.exists("questions/q_img_abc.png") is False
    storage.delete("questions/q_img_abc.png")  # deleting a missing key is a no-op


def test_read_bytes_from_url_local(tmp_path, monkeypatch):
    storage = LocalStorage(tmp_path)
    storage.put("questions/x.png", b"abc")
    monkeypatch.setattr(storage_module, "get_storage", lambda: storage)

    assert read_bytes_from_url("/uploads/questions/x.png") == b"abc"
    with pytest.raises(FileNotFoundError):
        read_bytes_from_url("/uploads/questions/missing.png")
    with pytest.raises(FileNotFoundError):
        read_bytes_from_url("https://example.test/not-ours.png")


# --------------------------------------------------------------------------- R2 fakes


class _FakeClientError(Exception):
    """Minimal stand-in for botocore.exceptions.ClientError."""

    def __init__(self, code: str, status: int = 404):
        self.response = {
            "Error": {"Code": str(code)},
            "ResponseMetadata": {"HTTPStatusCode": status},
        }
        super().__init__(str(code))


class _FakeBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeS3Client:
    def __init__(self):
        self.objects: dict[str, bytes] = {}
        self.put_calls: list[dict] = []
        self.get_calls: list[dict] = []
        self.head_calls: list[dict] = []
        self.delete_calls: list[dict] = []
        self.head_error: Exception | None = None

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)
        self.objects[kwargs["Key"]] = kwargs["Body"]

    def get_object(self, **kwargs):
        self.get_calls.append(kwargs)
        if kwargs["Key"] not in self.objects:
            raise _FakeClientError("NoSuchKey")
        return {"Body": _FakeBody(self.objects[kwargs["Key"]])}

    def head_object(self, **kwargs):
        self.head_calls.append(kwargs)
        if self.head_error is not None:
            raise self.head_error
        if kwargs["Key"] not in self.objects:
            raise _FakeClientError("404")
        return {"ContentLength": len(self.objects[kwargs["Key"]])}

    def delete_object(self, **kwargs):
        self.delete_calls.append(kwargs)
        self.objects.pop(kwargs["Key"], None)


@pytest.fixture
def fake_boto3(monkeypatch):
    """Inject a fake boto3/botocore so R2 tests run without the optional dependency."""
    client = _FakeS3Client()
    calls: list[tuple[str, dict]] = []
    configs: list[object] = []

    class FakeConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            configs.append(self)

    def fake_client(service_name, **kwargs):
        calls.append((service_name, kwargs))
        return client

    boto3_module = types.ModuleType("boto3")
    boto3_module.client = fake_client

    botocore_module = types.ModuleType("botocore")
    botocore_config_module = types.ModuleType("botocore.config")
    botocore_config_module.Config = FakeConfig
    botocore_module.config = botocore_config_module

    monkeypatch.setitem(sys.modules, "boto3", boto3_module)
    monkeypatch.setitem(sys.modules, "botocore", botocore_module)
    monkeypatch.setitem(sys.modules, "botocore.config", botocore_config_module)
    return client, calls, configs


def _r2_storage() -> R2Storage:
    return R2Storage(
        account_id="acct",
        access_key_id="access",
        secret_access_key="secret",
        bucket="bucket",
        public_base_url="https://files.example.com/",
    )


# --------------------------------------------------------------------------- R2


def test_r2_roundtrip_and_url_mapping(fake_boto3):
    client, calls, configs = fake_boto3
    storage = _r2_storage()

    assert len(calls) == 1
    service_name, kwargs = calls[0]
    assert service_name == "s3"
    assert kwargs["endpoint_url"] == "https://acct.r2.cloudflarestorage.com"
    assert kwargs["region_name"] == "auto"
    assert kwargs["aws_access_key_id"] == "access"
    assert kwargs["aws_secret_access_key"] == "secret"
    assert kwargs["config"].kwargs == {"signature_version": "s3v4"}
    assert configs[0].kwargs == {"signature_version": "s3v4"}

    storage.put("questions/x.png", b"data", "image/png")
    assert client.put_calls == [
        {
            "Bucket": "bucket",
            "Key": "questions/x.png",
            "Body": b"data",
            "ContentType": "image/png",
        }
    ]
    assert storage.get("questions/x.png") == b"data"
    assert storage.exists("questions/x.png") is True
    assert storage.size("questions/x.png") == 4

    assert storage.url("questions/x.png") == "https://files.example.com/questions/x.png"
    assert storage.key_from_url(
        "https://files.example.com/questions/x.png"
    ) == "questions/x.png"
    assert storage.key_from_url(
        "https://files.example.com/questions/x.png?token=1"
    ) == "questions/x.png"
    assert storage.key_from_url("https://other.example.com/questions/x.png") is None

    storage.delete("questions/x.png")
    assert client.delete_calls == [{"Bucket": "bucket", "Key": "questions/x.png"}]
    assert storage.exists("questions/x.png") is False


def test_r2_exists_returns_false_on_404(fake_boto3):
    client, _, _ = fake_boto3
    storage = _r2_storage()

    client.head_error = _FakeClientError("404")
    assert storage.exists("missing.png") is False

    client.head_error = _FakeClientError("NoSuchKey")
    assert storage.exists("missing.png") is False

    client.head_error = _FakeClientError("AccessDenied", status=403)
    with pytest.raises(_FakeClientError):
        storage.exists("missing.png")


def test_read_bytes_from_url_r2(fake_boto3, monkeypatch):
    storage = _r2_storage()
    monkeypatch.setattr(storage_module, "get_storage", lambda: storage)
    storage.put("questions/x.png", b"data")

    assert read_bytes_from_url("https://files.example.com/questions/x.png") == b"data"
    with pytest.raises(FileNotFoundError):
        read_bytes_from_url("https://files.example.com/questions/missing.png")


# --------------------------------------------------------------------------- config


def test_r2_backend_without_credentials_raises(monkeypatch):
    monkeypatch.setattr(config, "STORAGE_BACKEND", "r2")
    monkeypatch.setattr(config, "R2_ACCOUNT_ID", "")
    monkeypatch.setattr(config, "R2_ACCESS_KEY_ID", "")
    monkeypatch.setattr(config, "R2_SECRET_ACCESS_KEY", "")
    monkeypatch.setattr(config, "R2_BUCKET", "")

    with pytest.raises(RuntimeError) as exc:
        get_storage()

    message = str(exc.value)
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        assert name in message


@pytest.mark.parametrize("value", ["local", "LOCAL", " Local "])
def test_local_backend_is_the_default(monkeypatch, tmp_path, value):
    monkeypatch.setattr(config, "STORAGE_BACKEND", value)
    monkeypatch.setattr(config, "UPLOAD_ROOT", tmp_path)

    storage = get_storage()

    assert isinstance(storage, LocalStorage)
    assert storage.root == Path(tmp_path)


def test_get_storage_is_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "STORAGE_BACKEND", "local")
    monkeypatch.setattr(config, "UPLOAD_ROOT", tmp_path)

    assert get_storage() is get_storage()


@pytest.mark.parametrize("value", ["r2", "R2", "cloud", "S3"])
def test_remote_backend_aliases(monkeypatch, fake_boto3, value):
    monkeypatch.setattr(config, "STORAGE_BACKEND", value)
    monkeypatch.setattr(config, "R2_ACCOUNT_ID", "acct")
    monkeypatch.setattr(config, "R2_ACCESS_KEY_ID", "access")
    monkeypatch.setattr(config, "R2_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(config, "R2_BUCKET", "bucket")
    monkeypatch.setattr(config, "R2_PUBLIC_BASE_URL", "https://files.example.com")

    storage = get_storage()

    assert isinstance(storage, R2Storage)
