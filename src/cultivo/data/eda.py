"""EDA descritiva exclusivamente do treino; nenhuma transformacao definitiva."""

import json
import math
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cultivo import config
from cultivo.data.schema import validate_schema
from cultivo.data.split import SplitManifest, load_train

IQR_FACTOR = 1.5
HISTOGRAM_BINS = 20
QUANTILES = (0.0, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0)


def _number(value: float | None, reason: str = "empty_or_nonfinite_arithmetic") -> dict[str, Any]:
    if value is None or not math.isfinite(value):
        return {"value": None, "reason": reason}
    return {"value": float(value), "reason": None}


def _describe(series: pd.Series) -> dict[str, Any]:
    n = len(series)
    return {
        "count": n,
        "dtype": str(series.dtype),
        "nulls": int(series.isna().sum()),
        "inconsistencies": 0,
        "minimum": _number(series.min() if n else None),
        "maximum": _number(series.max() if n else None),
        "mean": _number(series.mean() if n else None),
        "std": _number(
            series.std(ddof=1) if n > 1 else None,
            "fewer_than_two_observations" if n < 2 else "nonfinite_arithmetic",
        ),
        "quantiles": {
            str(q): _number(series.quantile(q, interpolation="linear") if n else None)
            for q in QUANTILES
        },
    }


def _histogram(series: pd.Series) -> dict[str, Any]:
    if series.empty:
        return {"counts": [], "edges": [], "bins": HISTOGRAM_BINS, "reason": "empty_data"}
    minimum, maximum = float(series.min()), float(series.max())
    if not math.isfinite(maximum - minimum) or (
        minimum == maximum and minimum - 0.5 == maximum + 0.5
    ):
        return {
            "counts": [],
            "edges": [],
            "bins": HISTOGRAM_BINS,
            "reason": "histogram_numeric_range_not_representable",
        }
    try:
        counts, edges = np.histogram(series.to_numpy(dtype=float), bins=HISTOGRAM_BINS)
    except (ValueError, OverflowError, FloatingPointError):
        return {
            "counts": [],
            "edges": [],
            "bins": HISTOGRAM_BINS,
            "reason": "histogram_numeric_range_not_representable",
        }
    if not np.isfinite(edges).all():
        return {
            "counts": [],
            "edges": [],
            "bins": HISTOGRAM_BINS,
            "reason": "histogram_numeric_range_not_representable",
        }
    return {
        "counts": counts.tolist(),
        "edges": edges.tolist(),
        "bins": HISTOGRAM_BINS,
        "reason": None,
    }


def _class_counts(y: pd.Series) -> dict[str, int]:
    return {str(label): int(count) for label, count in y.value_counts().sort_index().items()}


def _scenario_summary(x: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
    return {
        "n_rows": len(x),
        "class_distribution": _class_counts(y),
        "summary": {feature: _describe(x[feature]) for feature in config.EXPECTED_FEATURES},
    }


def _comparisons(
    x: pd.DataFrame, y: pd.Series, feature: str, bounds: tuple[float | None, float | None]
) -> dict[str, Any]:
    low, high = bounds
    candidates = (
        (x[feature] < low) | (x[feature] > high) if low is not None else x[feature] < -np.inf
    )
    clipped = x.copy(deep=True)
    if low is not None:
        clipped[feature] = clipped[feature].clip(lower=low, upper=high)
    scenarios = {
        "keep": _scenario_summary(x, y),
        "clip": _scenario_summary(clipped, y),
        "remove_candidates": _scenario_summary(x.loc[~candidates], y.loc[~candidates]),
    }
    return {
        "status": "hypothetical_descriptive_only_not_approved",
        "changes_saved_to_training_data": False,
        "scenarios": scenarios,
    }


def _outlier_feature(x: pd.DataFrame, y: pd.Series, feature: str) -> dict[str, Any]:
    series = x[feature]
    q1 = float(series.quantile(0.25)) if len(series) else None
    q3 = float(series.quantile(0.75)) if len(series) else None
    iqr = q3 - q1 if q1 is not None and q3 is not None else None
    low = q1 - IQR_FACTOR * iqr if q1 is not None and iqr is not None else None
    high = q3 + IQR_FACTOR * iqr if q3 is not None and iqr is not None else None
    below = int((series < low).sum()) if low is not None else 0
    above = int((series > high).sum()) if high is not None else 0
    return {
        "method": "IQR",
        "factor": IQR_FACTOR,
        "quantile_interpolation": "linear",
        "boundary": "strictly below lower or above upper; equality is not a candidate",
        "iqr_zero_policy": "equal quartiles define equal bounds; differing values are candidates",
        "q1": _number(q1),
        "q3": _number(q3),
        "iqr": _number(iqr),
        "lower": _number(low),
        "upper": _number(high),
        "candidates_below": below,
        "candidates_above": above,
        "candidate_count": below + above,
        "confirmed_computational_errors": 0,
        "agronomic_plausibility": "not_verified_units_and_measurement_method_unconfirmed",
        "statistical_extreme_is_confirmed_error": False,
        "comparison": _comparisons(x, y, feature, (low, high)),
        "proposal": {
            "action": "retain_all_pending_P10",
            "approval": "pending_human_decision",
            "reason": f"{below + above} statistical candidates; no demonstrated agronomic error; "
            "review hypothetical class/distribution consequences before treatment",
        },
    }


def _correlations(x: pd.DataFrame) -> dict[str, Any]:
    matrix = x[list(config.EXPECTED_FEATURES)].corr(method="pearson")
    undefined = []
    rows = []
    for feature in config.EXPECTED_FEATURES:
        row = []
        for other in config.EXPECTED_FEATURES:
            number = _number(matrix.loc[feature, other], "constant_or_insufficient_observations")
            row.append(number["value"])
            if number["reason"]:
                undefined.append({"feature": feature, "other": other, "reason": number["reason"]})
        rows.append(row)
    return {
        "method": "pearson",
        "feature_order": list(config.EXPECTED_FEATURES),
        "matrix": rows,
        "undefined": undefined,
    }


def _validate_inputs(x: pd.DataFrame, y: pd.Series) -> None:
    if len(x) != len(y) or not x.index.equals(y.index):
        raise ValueError("x e y devem ter comprimento e indices alinhados.")
    if config.TARGET in x.columns:
        raise ValueError("x deve conter somente features, sem alvo.")
    combined = x.copy(deep=True)
    combined[config.TARGET] = y
    validate_schema(combined)


def analyze_train(x: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
    """Calcula EDA pura sem mutar entradas; valores invalidos interrompem sem correcao."""
    _validate_inputs(x, y)
    labels = list(_class_counts(y))
    result = {
        "schema_version": "1",
        "scope": "train",
        "provenance": {
            "n_rows": len(x),
            "feature_names": list(config.EXPECTED_FEATURES),
            "target_name": config.TARGET,
            "train_sha256": None,
            "train_sha256_reason": "filled_by_run_eda_from_existing_manifest",
        },
        "summary": {feature: _describe(x[feature]) for feature in config.EXPECTED_FEATURES},
        "distributions": {feature: _histogram(x[feature]) for feature in config.EXPECTED_FEATURES},
        "class_distribution": _class_counts(y),
        "feature_class": {
            feature: {label: _describe(x.loc[y == label, feature]) for label in labels}
            for feature in config.EXPECTED_FEATURES
        },
        "correlations": _correlations(x),
        "outliers": {
            "scope": "train",
            "features": {
                feature: _outlier_feature(x, y, feature) for feature in config.EXPECTED_FEATURES
            },
        },
        "figures": {},
    }
    json.dumps(result, allow_nan=False)
    return result


def _save_figure(figure: Any, path: Path) -> None:
    import matplotlib.pyplot as plt

    try:
        figure.tight_layout()
        figure.savefig(path, dpi=140)
    finally:
        plt.close(figure)


def _feature_plots(x: pd.DataFrame, y: pd.Series, feature: str, directory: Path) -> list[Path]:
    import matplotlib.pyplot as plt

    hist_path, class_path = (
        directory / f"{feature}-distribution.png",
        directory / f"{feature}-class.png",
    )
    figure, axis = plt.subplots(figsize=(8, 4))
    axis.hist(x[feature].to_numpy(), bins=HISTOGRAM_BINS, color="#287271", edgecolor="white")
    axis.set(
        xlabel=f"{feature} (unidade nao confirmada)",
        ylabel="Registros",
        title=f"Distribuicao no treino: {feature}",
    )
    _save_figure(figure, hist_path)
    labels = list(_class_counts(y))
    figure, axis = plt.subplots(figsize=(9, max(4, len(labels) * 0.32)))
    if labels:
        axis.boxplot(
            [x.loc[y == label, feature].to_numpy() for label in labels],
            tick_labels=labels,
            orientation="horizontal",
        )
    else:
        axis.text(0.5, 0.5, "Sem observacoes", ha="center")
    axis.set(
        xlabel=f"{feature} (unidade nao confirmada)", title="Relacao feature-classe, somente treino"
    )
    _save_figure(figure, class_path)
    return [hist_path, class_path]


def _figures(x: pd.DataFrame, y: pd.Series, report: dict[str, Any]) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = config.REPORTS_DIR / "figures" / "eda"
    directory.mkdir(parents=True, exist_ok=True)
    paths = [
        path
        for feature in config.EXPECTED_FEATURES
        for path in _feature_plots(x, y, feature, directory)
    ]
    figure, axis = plt.subplots(figsize=(10, 5))
    counts = _class_counts(y)
    axis.barh(list(counts), list(counts.values()), color="#287271")
    axis.set(xlabel="Registros", title="Classes observadas no treino")
    class_path = directory / "class-distribution.png"
    _save_figure(figure, class_path)
    figure, axis = plt.subplots(figsize=(8, 7))
    matrix = np.array(report["correlations"]["matrix"], dtype=float)
    image = axis.imshow(np.ma.masked_invalid(matrix), vmin=-1, vmax=1, cmap="coolwarm")
    axis.set_xticks(range(len(config.EXPECTED_FEATURES)), config.EXPECTED_FEATURES, rotation=45)
    axis.set_yticks(range(len(config.EXPECTED_FEATURES)), config.EXPECTED_FEATURES)
    axis.set_title("Correlacao Pearson somente no treino; celulas vazias indefinidas")
    figure.colorbar(image, ax=axis)
    corr_path = directory / "correlations.png"
    _save_figure(figure, corr_path)
    paths.extend([class_path, corr_path])
    return {path.stem: path.relative_to(config.PROJECT_ROOT).as_posix() for path in paths}


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def _decision_text(outliers: dict[str, Any]) -> str:
    lines = [
        "# Propostas de outliers somente no treino",
        "",
        "P-10 pendente: nenhuma alternativa abaixo esta aprovada ou aplicada.",
        "Extremo estatistico nao demonstra erro agronomico; unidades nao confirmadas.",
        "",
        "| Feature | Candidatos IQR1.5 | Proposta | Evidencia |",
        "|---|---:|---|---|",
    ]
    for feature, details in outliers["features"].items():
        lines.append(
            f"| {feature} | {details['candidate_count']} | Manter ate decisao P-10 | "
            f"outliers.json/features/{feature}; ../figures/eda/{feature}-distribution.png |"
        )
    lines.extend(
        [
            "",
            "Limites estritos e interpolacao linear detalhados em outliers.json.",
            "Comparacoes manter/clipping/remover sao hipoteticas; preservam dados em disco.",
            "Nenhum limite desta EDA e parametro pre-ajustado para CV.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_eda() -> dict[str, Any]:
    """Carrega somente treino verificado, produz figuras/JSON e preserva integridade historica."""
    directory = config.REPORTS_DIR / "data"
    quality_path = directory / "quality.json"
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    manifest = SplitManifest.model_validate_json(
        (config.PROCESSED_DIR / "SPLIT_MANIFEST.json").read_bytes()
    )
    x, y = load_train()
    report = analyze_train(x, y)
    if len(x) != manifest.n_train:
        raise ValueError("Contagem do treino diverge do manifest.")
    report["provenance"].update(
        {
            "train_sha256": manifest.train_sha256,
            "train_sha256_reason": None,
            "versions": {
                "python": platform.python_version(),
                **{name: version(name) for name in ("pandas", "numpy", "matplotlib")},
            },
        }
    )
    report["figures"] = _figures(x, y, report)
    outliers = {
        "schema_version": "1",
        "scope": "train",
        "provenance": report["provenance"],
        "features": report["outliers"]["features"],
    }
    _write_json(directory / "eda.json", report)
    _write_json(directory / "outliers.json", outliers)
    (directory / "outlier-decisions.md").write_text(_decision_text(outliers), encoding="utf-8")
    enriched = {
        **quality,
        "outliers": {
            "scope": "train",
            "report": "reports/data/outliers.json",
            "train_sha256": manifest.train_sha256,
        },
    }
    if any(enriched[key] != value for key, value in quality.items() if key != "outliers"):
        raise ValueError("Integridade historica nao pode ser alterada.")
    _write_json(quality_path, enriched)
    return report
