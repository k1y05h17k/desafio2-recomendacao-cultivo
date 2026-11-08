"""Schema computacional estrito e integridade pre-split, sem correcao de dados."""

import math
from collections import Counter
from numbers import Real
from typing import Annotated, Any

import pandas as pd
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, ValidationError
from pydantic_core import PydanticCustomError

from cultivo import config


def _finite_real(value: Any) -> Any:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PydanticCustomError("invalid_numeric", "Numero real requerido")
    # Representabilidade float computacional, sem limite agronomico.
    try:
        is_finite = math.isfinite(value)
    except OverflowError as error:
        raise PydanticCustomError(
            "numeric_not_representable", "Numero nao representavel no contrato float"
        ) from error
    if not is_finite:
        raise PydanticCustomError("non_finite", "Numero finito requerido")
    return value


def _nonempty(value: str) -> str:
    if not value.strip():
        raise PydanticCustomError("empty_target", "Alvo textual nao vazio requerido")
    return value


FiniteReal = Annotated[float, BeforeValidator(_finite_real)]
TargetText = Annotated[str, AfterValidator(_nonempty)]


class FeatureSample(BaseModel):
    """Amostra numerica; unidades nao confirmadas e sem faixas agronomicas."""

    model_config = ConfigDict(strict=True, extra="forbid")
    N: FiniteReal
    P: FiniteReal
    K: FiniteReal
    temperature: FiniteReal
    humidity: FiniteReal
    ph: FiniteReal
    rainfall: FiniteReal


class Observation(FeatureSample):
    """Amostra acompanhada de cultura textual, sem whitelist de classes."""

    label: TargetText


class SchemaIssue(BaseModel):
    """Problema sanitizado, sem valor individual ou representacao da linha."""

    column: str
    position: int | None = None
    code: str


class SchemaReport(BaseModel):
    """Resultado estruturado da validacao sem alterar o DataFrame."""

    valid: bool
    require_target: bool
    schema_diff: dict[str, list[str]]
    issues: list[SchemaIssue]
    classes: list[str]
    units: dict[str, str]
    rules: list[str]


class SchemaError(ValueError):
    """Falha de schema com relatorio sanitizado acessivel em report."""

    def __init__(self, report: SchemaReport) -> None:
        self.report = report
        locations = [
            f"coluna={issue.column}, posicao={issue.position}, codigo={issue.code}"
            for issue in report.issues
        ]
        super().__init__("Schema invalido: " + "; ".join(locations))


def _columns(df: pd.DataFrame, require_target: bool) -> dict[str, list[str]]:
    names = list(df.columns)
    expected = list(config.EXPECTED_FEATURES) + ([config.TARGET] if require_target else [])
    allowed = set(config.EXPECTED_FEATURES) | {config.TARGET}
    return {
        "missing": [name for name in expected if name not in names],
        "extra": [str(name) for name in names if name not in allowed],
        "duplicate": [str(name) for name, count in Counter(names).items() if count > 1],
    }


def _row_issues(df: pd.DataFrame, duplicates: list[str]) -> list[SchemaIssue]:
    has_target = config.TARGET in df.columns and config.TARGET not in duplicates
    model = Observation if has_target else FeatureSample
    selected = [
        (position, name)
        for position, name in enumerate(df.columns)
        if name in model.model_fields and name not in duplicates
    ]
    issues = []
    for position, row in enumerate(df.itertuples(index=False, name=None)):
        payload = {name: row[index] for index, name in selected}
        try:
            model.model_validate(payload)
        except ValidationError as error:
            for detail in error.errors(
                include_input=False, include_context=False, include_url=False
            ):
                if detail["type"] != "missing":
                    issues.append(
                        SchemaIssue(
                            column=str(detail["loc"][0]), position=position, code=detail["type"]
                        )
                    )
    return issues


def _class_counts(df: pd.DataFrame) -> dict[str, int]:
    if list(df.columns).count(config.TARGET) != 1:
        return {}
    values = df[config.TARGET].tolist()
    return dict(
        sorted(
            Counter(value for value in values if isinstance(value, str) and value.strip()).items()
        )
    )


def _inspect(df: pd.DataFrame, require_target: bool) -> SchemaReport:
    diff = _columns(df, require_target)
    issues = [SchemaIssue(column=name, code=kind) for kind, names in diff.items() for name in names]
    issues.extend(_row_issues(df, diff["duplicate"]))
    return SchemaReport(
        valid=not issues,
        require_target=require_target,
        schema_diff=diff,
        issues=issues,
        classes=list(_class_counts(df)),
        units={name: "nao confirmada na fonte aprovada" for name in config.EXPECTED_FEATURES},
        rules=[
            "features: numeros reais finitos, sem bool ou strings",
            "alvo: texto nao vazio quando presente",
            "sem limites agronomicos aprovados",
            "CSV: inferencia numerica explicita em load_raw; validacao nao corrige valores",
        ],
    )


def validate_schema(df: pd.DataFrame, require_target: bool = True) -> SchemaReport:
    """Valida colunas/valores sem mutacao; levanta SchemaError com report se invalido."""
    report = _inspect(df, require_target)
    if not report.valid:
        raise SchemaError(report)
    return report


def integrity_report(df: pd.DataFrame) -> dict[str, Any]:
    """Mede somente integridade agregada permitida no dataset completo antes do split."""
    schema = _inspect(df, require_target=True)
    counts = _class_counts(df)
    frequencies = list(counts.values())
    invalid = Counter(
        (issue.column, issue.code) for issue in schema.issues if issue.position is not None
    )
    invalid_values: dict[str, dict[str, int]] = {}
    for (column, code), count in invalid.items():
        invalid_values.setdefault(column, {})[code] = count
    complete = not any(schema.schema_diff.values())
    duplicates = {
        "definition": "igualdade de todas as features e alvo; excedentes apos primeira ocorrencia",
        "rows_beyond_first": int(df.duplicated(keep="first").sum()) if complete else None,
        "rows_in_duplicate_groups": int(df.duplicated(keep=False).sum()) if complete else None,
        "checked": complete,
    }
    return {
        "scope": "full",
        "n_rows": len(df),
        "classes": list(counts),
        "class_distribution": counts,
        "balance": {
            "n_classes": len(counts),
            "min_count": min(frequencies) if frequencies else None,
            "max_count": max(frequencies) if frequencies else None,
            "ratio_min_to_max": min(frequencies) / max(frequencies) if frequencies else None,
        },
        "duplicates": duplicates,
        "nulls": [
            {
                "column": str(name),
                "column_position": index,
                "count": int(df.iloc[:, index].isna().sum()),
            }
            for index, name in enumerate(df.columns)
        ],
        "dtypes": [
            {"column": str(name), "column_position": index, "dtype": str(dtype)}
            for index, (name, dtype) in enumerate(zip(df.columns, df.dtypes, strict=True))
        ],
        "schema_diff": schema.schema_diff,
        "schema_valid": schema.valid,
        "invalid_values": invalid_values,
        "units": schema.units,
        "rules": schema.rules,
    }
