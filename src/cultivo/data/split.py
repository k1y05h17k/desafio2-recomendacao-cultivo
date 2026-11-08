"""Split unico estratificado e cargas protegidas (ADR-0001/0010)."""

import hashlib
import io
import json
import math
import os
from pathlib import Path

import pandas as pd
import sklearn
from pandas.testing import assert_frame_equal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sklearn.model_selection import train_test_split

from cultivo import config
from cultivo.data.ingest import RawManifest, load_raw
from cultivo.data.schema import integrity_report, validate_schema


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _ids_hash(indices: list[int]) -> str:
    return _digest(json.dumps(indices, separators=(",", ":")).encode("utf-8"))


class SplitManifest(BaseModel):
    """Proveniencia e IDs posicionais; nunca inclui valores de linhas."""

    model_config = ConfigDict(strict=True, extra="forbid")
    schema_version: str = "1"
    raw_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    seed: int
    test_size: float
    stratify: str
    algorithm: str = "sklearn.model_selection.train_test_split; sorted positional indices"
    sklearn_version: str
    n_total: int = Field(gt=0)
    n_train: int = Field(gt=0)
    n_holdout: int = Field(gt=0)
    train_indices: list[int]
    holdout_indices: list[int]
    train_indices_sha256: str
    holdout_indices_sha256: str
    train_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    holdout_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    serialization: dict[str, str]

    @model_validator(mode="after")
    def validate_partitions(self) -> "SplitManifest":
        """Confere protocolo, completude e hashes dos indices sem ler particoes."""
        train, protected = set(self.train_indices), set(self.holdout_indices)
        if (
            self.seed != config.SEED
            or self.test_size != config.TEST_SIZE
            or self.stratify != config.TARGET
            or self.schema_version != "1"
            or self.n_train != len(self.train_indices)
            or self.n_holdout != len(self.holdout_indices)
            or len(train) != self.n_train
            or len(protected) != self.n_holdout
            or train & protected
            or train | protected != set(range(self.n_total))
            or self.n_train + self.n_holdout != self.n_total
            or self.train_indices != sorted(self.train_indices)
            or self.holdout_indices != sorted(self.holdout_indices)
            or self.train_indices_sha256 != _ids_hash(self.train_indices)
            or self.holdout_indices_sha256 != _ids_hash(self.holdout_indices)
        ):
            raise ValueError("Manifest de split inconsistente.")
        return self


def _destinations() -> tuple[Path, Path, Path]:
    return (
        config.PROCESSED_DIR / "train.csv",
        config.HOLDOUT_DIR / "holdout.csv",
        config.PROCESSED_DIR / "SPLIT_MANIFEST.json",
    )


def _assert_empty() -> None:
    for path in _destinations():
        if path.exists() or path.with_suffix(path.suffix + ".tmp").exists():
            raise FileExistsError(
                "Split/destino/temporario existente; intervencao humana necessaria."
            )


def _parameters(test_size: float, seed: int, stratify_col: str) -> None:
    if (
        type(seed) is not int
        or seed != config.SEED
        or type(test_size) is not float
        or test_size != config.TEST_SIZE
        or not 0 < test_size < 1
        or stratify_col != config.TARGET
    ):
        raise ValueError("Parametros devem corresponder ao protocolo central aprovado.")


def _verified_origin(df: pd.DataFrame) -> str:
    source = load_raw()
    if not df.index.equals(pd.RangeIndex(len(df))):
        raise ValueError("Indice deve corresponder as posicoes originais.")
    try:
        assert_frame_equal(df, source, check_exact=True, check_dtype=True, check_like=False)
    except AssertionError:
        raise ValueError("DataFrame diverge da origem verificada; split recusado.") from None
    manifest = RawManifest.model_validate_json((config.RAW_DIR / "MANIFEST.json").read_bytes())
    return manifest.sha256


def _partition_indices(
    df: pd.DataFrame, test_size: float, seed: int
) -> tuple[list[int], list[int]]:
    validate_schema(df)
    report = integrity_report(df)
    if report["duplicates"]["rows_beyond_first"]:
        raise ValueError("Duplicatas exatas exigem politica aprovada; nenhuma linha removida.")
    counts = df[config.TARGET].value_counts()
    n_test = math.ceil(len(df) * test_size)
    if counts.empty or counts.min() < 2 or min(n_test, len(df) - n_test) < len(counts):
        raise ValueError("Classes insuficientes para estratificacao obrigatoria.")
    train, protected = train_test_split(
        list(range(len(df))), test_size=test_size, random_state=seed, stratify=df[config.TARGET]
    )
    train, protected = sorted(train), sorted(protected)
    classes = set(df[config.TARGET])
    if (
        set(df.iloc[train][config.TARGET]) != classes
        or set(df.iloc[protected][config.TARGET]) != classes
    ):
        raise ValueError("Estratificacao nao preservou todas as classes nas duas particoes.")
    if set(train) & set(protected) or set(train) | set(protected) != set(range(len(df))):
        raise ValueError("Indices nao formam particao completa e disjunta.")
    return train, protected


def _csv_bytes(df: pd.DataFrame, indices: list[int]) -> bytes:
    return (
        df.iloc[indices]
        .to_csv(
            index=False,
            columns=[*config.EXPECTED_FEATURES, config.TARGET],
            sep=",",
            decimal=".",
            lineterminator="\n",
            float_format="%.17g",
        )
        .encode("utf-8")
    )


def _build_manifest(
    df: pd.DataFrame, raw_sha: str, parts: tuple[list[int], list[int]], buffers: tuple[bytes, bytes]
) -> SplitManifest:
    train, protected = parts
    return SplitManifest(
        raw_sha256=raw_sha,
        seed=config.SEED,
        test_size=config.TEST_SIZE,
        stratify=config.TARGET,
        sklearn_version=sklearn.__version__,
        n_total=len(df),
        n_train=len(train),
        n_holdout=len(protected),
        train_indices=train,
        holdout_indices=protected,
        train_indices_sha256=_ids_hash(train),
        holdout_indices_sha256=_ids_hash(protected),
        train_sha256=_digest(buffers[0]),
        holdout_sha256=_digest(buffers[1]),
        serialization={
            "encoding": "UTF-8",
            "separator": ",",
            "decimal": ".",
            "line_terminator": "LF",
            "index": "excluded",
            "float_format": "%.17g",
            "columns": "config.EXPECTED_FEATURES + TARGET",
            "rows": "ascending source positional indices",
            "indices_hash": "SHA256 of compact JSON integer array, UTF-8",
        },
    )


def _publish(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    if path.exists():
        raise FileExistsError("Destino existente; nao sobrescrever nem apagar.")
    os.replace(temporary, path)


def split(df: pd.DataFrame, test_size: float, seed: int, stratify_col: str) -> SplitManifest:
    """Valida origem e protocolo, publica uma divisao unica e devolve metadados em memoria."""
    _parameters(test_size, seed, stratify_col)
    _assert_empty()
    raw_sha = _verified_origin(df)
    parts = _partition_indices(df, test_size, seed)
    buffers = (_csv_bytes(df, parts[0]), _csv_bytes(df, parts[1]))
    manifest = _build_manifest(df, raw_sha, parts, buffers)
    _assert_empty()
    train_path, protected_path, manifest_path = _destinations()
    _publish(train_path, buffers[0])
    _publish(protected_path, buffers[1])
    _publish(manifest_path, (manifest.model_dump_json(indent=2) + "\n").encode("utf-8"))
    return manifest


def _load_partition(protected: bool) -> tuple[pd.DataFrame, pd.Series]:
    train_path, protected_path, manifest_path = _destinations()
    manifest = SplitManifest.model_validate_json(manifest_path.read_bytes())
    path = protected_path if protected else train_path
    content = path.read_bytes()
    expected_hash = manifest.holdout_sha256 if protected else manifest.train_sha256
    expected_rows = manifest.n_holdout if protected else manifest.n_train
    if _digest(content) != expected_hash:
        raise ValueError("Hash da particao diverge do manifest.")
    frame = pd.read_csv(
        io.BytesIO(content), encoding="utf-8", sep=",", float_precision="round_trip"
    )
    validate_schema(frame)
    if len(frame) != expected_rows:
        raise ValueError("Quantidade da particao diverge do manifest.")
    return frame[list(config.EXPECTED_FEATURES)], frame[config.TARGET]


def load_train() -> tuple[pd.DataFrame, pd.Series]:
    """Carrega somente treino verificado pelo manifest; nunca abre bruto ou teste."""
    return _load_partition(protected=False)


def load_holdout() -> tuple[pd.DataFrame, pd.Series]:
    """Exige guard ADR0001 antes de I/O; desbloqueio real cabe ao humano apos H4."""
    if os.environ.get("CULTIVO_HOLDOUT_UNLOCKED") != "1":
        raise PermissionError("Conjunto protegido bloqueado ate autorizacao humana H4.")
    return _load_partition(protected=True)
