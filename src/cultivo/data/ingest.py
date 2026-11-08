"""Ingestao unica verificada e carga local do bruto (ADR-0009/0010)."""

import csv
import hashlib
import io
import os
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from urllib.request import urlopen

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from cultivo import config


class RawManifest(BaseModel):
    """Metadados medidos dos bytes verificados da fonte fixada."""

    model_config = ConfigDict(extra="forbid", strict=True)
    source: Literal["github"]
    source_url: str
    repository: str
    revision: str
    path_in_repo: str
    declared_origin: str
    license: None
    downloaded_at: str
    size_bytes: int = Field(gt=0)
    git_blob_sha1: str = Field(pattern=r"^[0-9a-f]{40}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    n_rows: int = Field(ge=0)
    columns: list[str]
    python_version: str


def _guard_split() -> None:
    # Apenas existencia: nunca abrir particoes, inclusive em split interrompido.
    artifacts = [
        config.PROCESSED_DIR / name
        for name in ("train.csv", "train.csv.tmp", "SPLIT_MANIFEST.json", "SPLIT_MANIFEST.json.tmp")
    ] + [config.HOLDOUT_DIR / name for name in ("holdout.csv", "holdout.csv.tmp")]
    if any(path.exists() for path in artifacts):
        raise RuntimeError("Bruto bloqueado apos split ou estado parcial; exige protocolo H4.")


def _paths() -> tuple[Path, Path]:
    return config.RAW_DIR / "crop_recommendation.csv", config.RAW_DIR / "MANIFEST.json"


def _verify_bytes(content: bytes) -> tuple[str, str]:
    if len(content) != config.DATASET_SIZE_BYTES:
        raise ValueError(f"Tamanho esperado {config.DATASET_SIZE_BYTES}; recebido {len(content)}.")
    blob = hashlib.sha1(
        f"blob {len(content)}\0".encode() + content, usedforsecurity=False
    ).hexdigest()
    if blob != config.DATASET_GIT_BLOB_SHA1:
        raise ValueError(f"Blob esperado {config.DATASET_GIT_BLOB_SHA1}; recebido {blob}.")
    return blob, hashlib.sha256(content).hexdigest()


def _structure(content: bytes) -> tuple[list[str], int]:
    reader = csv.reader(io.StringIO(content.decode("utf-8"), newline=""))
    columns = next(reader)
    return columns, sum(1 for _ in reader)


def _download() -> bytes:
    parsed = urlsplit(config.DATASET_URL)
    expected = (
        f"https://raw.githubusercontent.com/{config.DATASET_ID}/"
        f"{config.DATASET_REVISION}/{config.DATASET_FILE}"
    )
    if (
        parsed.scheme != "https"
        or parsed.netloc != "raw.githubusercontent.com"
        or config.DATASET_URL != expected
    ):
        raise ValueError("URL deve ser HTTPS da fonte GitHub fixada em config.")
    # ADR-0009: URL constante validada, timeout, leitura limitada e bytes conferidos.
    with urlopen(config.DATASET_URL, timeout=30) as response:  # ADR-0009: URL fixa/limite/blob # nosec B310
        return bytes(response.read(config.DATASET_SIZE_BYTES + 1))


def _manifest(content: bytes) -> RawManifest:
    blob, sha256 = _verify_bytes(content)
    columns, n_rows = _structure(content)
    return RawManifest(
        source="github",
        source_url=config.DATASET_URL,
        repository=config.DATASET_ID,
        revision=config.DATASET_REVISION,
        path_in_repo=config.DATASET_FILE,
        declared_origin=config.DATASET_DECLARED_ORIGIN,
        license=None,
        downloaded_at=datetime.now(UTC).isoformat(),
        size_bytes=len(content),
        git_blob_sha1=blob,
        sha256=sha256,
        n_rows=n_rows,
        columns=columns,
        python_version=platform.python_version(),
    )


def _read_verified(csv_path: Path, manifest_path: Path) -> tuple[RawManifest, bytes]:
    manifest = RawManifest.model_validate_json(manifest_path.read_bytes())
    expected = {
        "source_url": config.DATASET_URL,
        "repository": config.DATASET_ID,
        "revision": config.DATASET_REVISION,
        "path_in_repo": config.DATASET_FILE,
        "declared_origin": config.DATASET_DECLARED_ORIGIN,
    }
    for key, value in expected.items():
        if getattr(manifest, key) != value:
            raise ValueError(f"Manifest diverge da fonte fixada: {key}.")
    timestamp = datetime.fromisoformat(manifest.downloaded_at)
    offset = timestamp.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("downloaded_at deve estar em UTC.")
    content = csv_path.read_bytes()
    blob, sha256 = _verify_bytes(content)
    columns, n_rows = _structure(content)
    if (
        manifest.size_bytes != len(content)
        or manifest.git_blob_sha1 != blob
        or manifest.sha256 != sha256
        or manifest.columns != columns
        or manifest.n_rows != n_rows
    ):
        raise ValueError("Integridade do bruto/manifest divergente.")
    return manifest, content


def _check_state() -> tuple[Path, Path, bool]:
    _guard_split()
    csv_path, manifest_path = _paths()
    for path in (csv_path, manifest_path):
        if path.with_suffix(path.suffix + ".tmp").exists():
            raise FileExistsError("Temporario existente; intervencao humana necessaria.")
    csv_exists, manifest_exists = csv_path.exists(), manifest_path.exists()
    if csv_exists != manifest_exists:
        raise FileExistsError("Par CSV/manifest incompleto; intervencao humana necessaria.")
    return csv_path, manifest_path, csv_exists


def _publish(path: Path, content: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise FileExistsError("Destino existente; nao sobrescrever; intervencao humana.")
    os.replace(temporary, path)


def ingest_raw() -> RawManifest:
    """Baixa uma vez os bytes fixados, ou verifica o par local sem rede."""
    csv_path, manifest_path, exists = _check_state()
    if exists:
        return _read_verified(csv_path, manifest_path)[0]
    content = _download()
    manifest = _manifest(content)
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    _publish(csv_path, content)
    _publish(manifest_path, (manifest.model_dump_json(indent=2) + "\n").encode("utf-8"))
    return manifest


def load_raw() -> pd.DataFrame:
    """Le somente cache verificado antes do split.

    Parse explicito UTF8/virgula com inferencia numerica pandas na borda;
    nao imputa, corrige ou valida schema de dominio.
    """
    csv_path, manifest_path, exists = _check_state()
    if not exists:
        raise FileNotFoundError("Bruto local ausente; execute ingest_raw explicitamente.")
    _, content = _read_verified(csv_path, manifest_path)
    return pd.read_csv(io.BytesIO(content), encoding="utf-8", sep=",", keep_default_na=True)
