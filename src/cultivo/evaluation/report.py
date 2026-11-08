"""Documento de metricas ``kind="cv"``: montagem, validacao, gravacao e selecao D7.

Schema e regras: ADR-0012 D9 (compativel com ADR-0003). Este modulo nao le arquivos;
o unico I/O e a gravacao em ``write_metrics``.
"""

import json
import math
import platform
import re
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from cultivo import config
from cultivo.evaluation.cv import SEARCH_STRATEGY, STD_DDOF

KIND_CV = "cv"
STATUS_EVALUATED = "avaliado"
STATUS_REMOVED_PREFIX = "removido: "
BASELINE_MODEL = "dummy"
CV_STRATEGY = "StratifiedKFold"
VERSIONED_PACKAGES = ("scikit-learn", "numpy", "pandas", "xgboost", "lightgbm")
_EXPERIMENT_ID = re.compile(r"^EXP-\d{3}$")
_CREATED = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOP_KEYS = frozenset(
    {
        "experiment_id",
        "kind",
        "created",
        "seed",
        "cv",
        "holdout",
        "data",
        "classes",
        "versions",
        "primary_metric",
        "metrics_reported",
        "parallelism",
        "selected_from",
        "models",
    }
)
_SEARCH_KEYS = frozenset(
    {
        "strategy",
        "n_iter",
        "random_state",
        "refit_metric",
        "param_distributions",
        "best_params",
        "n_candidates",
    }
)
_PARAM_PREFIXES = ("model__", "preprocess__")


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "nao instalado"


def _versions() -> dict[str, str]:
    found = {name: _package_version(name) for name in VERSIONED_PACKAGES}
    return {"python": platform.python_version(), **found}


def build_cv_report(
    experiment_id: str,
    models: dict[str, dict[str, Any]],
    classes: list[str],
    data: dict[str, Any],
    selected_from: str | None = None,
) -> dict[str, Any]:
    """Monta o documento ``kind="cv"`` com os metadados da execucao.

    Args:
        experiment_id: ``EXP-NNN``.
        models: blocos por nome do registry (saida de ``evaluate_cv`` ou status removido).
        classes: classes na ordem de ``encode_labels``.
        data: ``{"sha256_train": ..., "n_train": ...}`` copiado do manifesto pelo chamador.
        selected_from: EXP de origem dos candidatos (EXP com busca); ``None`` sem busca.

    Returns:
        Documento no schema de ADR-0012 D9 (ainda nao validado).
    """
    return {
        "experiment_id": experiment_id,
        "kind": KIND_CV,
        "created": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": config.SEED,
        "cv": {
            "strategy": CV_STRATEGY,
            "n_splits": config.CV_N_SPLITS,
            "shuffle": config.CV_SHUFFLE,
            "random_state": config.SEED,
            "std_ddof": STD_DDOF,
        },
        "holdout": None,
        "data": {"sha256_train": data["sha256_train"], "n_train": data["n_train"]},
        "classes": list(classes),
        "versions": _versions(),
        "primary_metric": config.PRIMARY_METRIC,
        "metrics_reported": list(config.REPORTED_METRICS),
        "parallelism": {"n_jobs": config.N_JOBS, "estimator_n_jobs": config.ESTIMATOR_N_JOBS},
        "selected_from": selected_from,
        "models": models,
    }


def _require(condition: bool, field: str, reason: str) -> None:
    if not condition:
        raise ValueError(f"Campo invalido '{field}': {reason}.")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _check_header(doc: dict[str, Any]) -> None:
    _require(isinstance(doc, dict), "<doc>", "documento deve ser um objeto")
    missing = sorted(_TOP_KEYS - set(doc))
    _require(not missing, ",".join(missing), "chave obrigatoria ausente")
    experiment_id = doc["experiment_id"]
    _require(
        isinstance(experiment_id, str) and bool(_EXPERIMENT_ID.match(experiment_id)),
        "experiment_id",
        "deve casar ^EXP-\\d{3}$",
    )
    _require(doc["kind"] == KIND_CV, "kind", f"esperado '{KIND_CV}'")
    created = doc["created"]
    _require(isinstance(created, str) and bool(_CREATED.match(created)), "created", "UTC ISO Z")
    _require(_is_int(doc["seed"]), "seed", "deve ser inteiro")
    _require(doc["holdout"] is None, "holdout", "deve ser null em kind=cv")


def _check_cv(cv: Any, seed: object) -> int:
    _require(isinstance(cv, dict), "cv", "obrigatorio em kind=cv")
    _require(cv.get("strategy") == CV_STRATEGY, "cv.strategy", f"esperado {CV_STRATEGY}")
    n_splits = cv.get("n_splits")
    _require(_is_int(n_splits) and n_splits >= 2, "cv.n_splits", "inteiro >= 2")
    _require(isinstance(cv.get("shuffle"), bool), "cv.shuffle", "deve ser booleano")
    _require(cv.get("random_state") == seed, "cv.random_state", "deve ser igual a seed")
    _require(cv.get("std_ddof") == STD_DDOF, "cv.std_ddof", f"deve ser {STD_DDOF}")
    return int(n_splits)


def _check_context(doc: dict[str, Any]) -> None:
    data = doc["data"]
    _require(isinstance(data, dict) and set(data) == {"sha256_train", "n_train"}, "data", "chaves")
    _require(bool(_SHA256.match(str(data["sha256_train"]))), "data.sha256_train", "hex64")
    _require(_is_int(data["n_train"]) and data["n_train"] > 0, "data.n_train", "inteiro > 0")
    classes = doc["classes"]
    _require(
        isinstance(classes, list) and bool(classes) and all(isinstance(c, str) for c in classes),
        "classes",
        "lista nao vazia de str",
    )
    _require(len(set(classes)) == len(classes), "classes", "sem repeticao")
    _require(classes == sorted(classes), "classes", "ordenadas como em encode_labels")
    versions = doc["versions"]
    expected = {"python", *VERSIONED_PACKAGES}
    _require(isinstance(versions, dict) and set(versions) == expected, "versions", "chaves")
    reported = doc["metrics_reported"]
    _require(
        reported == list(config.REPORTED_METRICS),
        "metrics_reported",
        "deve ser REPORTED_METRICS, na ordem do config",
    )
    _require(doc["primary_metric"] in reported, "primary_metric", "deve estar em metrics_reported")
    parallelism = doc["parallelism"]
    _require(
        isinstance(parallelism, dict)
        and _is_int(parallelism.get("n_jobs"))
        and _is_int(parallelism.get("estimator_n_jobs")),
        "parallelism",
        "n_jobs e estimator_n_jobs inteiros",
    )


def _check_summary(summary: Any, field: str, n_splits: int, *, upper: float | None) -> None:
    _require(isinstance(summary, dict), field, "deve ser objeto com mean, std e folds")
    folds = summary.get("folds")
    _require(isinstance(folds, list) and len(folds) == n_splits, field, "len(folds) != n_splits")
    values = [summary.get("mean"), summary.get("std"), *folds]
    _require(all(_is_number(v) for v in values), field, "valores finitos obrigatorios")
    low_ok = all(v >= 0 for v in values)
    high_ok = upper is None or all(v <= upper for v in values)
    _require(low_ok and high_ok, field, f"fora de [0, {upper if upper is not None else 'inf'}]")
    mean = sum(folds) / n_splits
    std = math.sqrt(sum((v - mean) ** 2 for v in folds) / (n_splits - STD_DDOF))
    _require(math.isclose(summary["mean"], mean, rel_tol=1e-9, abs_tol=1e-12), field, "mean")
    _require(math.isclose(summary["std"], std, rel_tol=1e-9, abs_tol=1e-12), field, "std ddof=1")


def _check_params(params: object, field: str) -> None:
    _require(isinstance(params, dict), field, "deve ser objeto")
    try:
        json.dumps(params, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Campo invalido '{field}': nao serializavel em JSON ({error}).") from None


def _check_search_timing(summary: Any, field: str) -> None:
    _require(isinstance(summary, dict), field, "deve ser objeto com mean, std e folds")
    _require(summary.get("folds") == [], field, "folds deve ser [] em EXP com busca (D9)")
    values = [summary.get("mean"), summary.get("std")]
    _require(all(_is_number(v) and v >= 0 for v in values), field, "mean e std finitos >= 0")


def _check_search(search: Any, params: dict[str, Any], doc: dict[str, Any], field: str) -> None:
    _require(isinstance(search, dict) and set(search) == _SEARCH_KEYS, field, "chaves de D9")
    _require(search["strategy"] == SEARCH_STRATEGY, f"{field}.strategy", SEARCH_STRATEGY)
    n_iter, n_candidates = search["n_iter"], search["n_candidates"]
    _require(_is_int(n_iter) and n_iter >= 1, f"{field}.n_iter", "inteiro >= 1")
    _require(search["random_state"] == doc["seed"], f"{field}.random_state", "igual a seed")
    _require(
        search["refit_metric"] == doc["primary_metric"], f"{field}.refit_metric", "primary_metric"
    )
    _require(
        _is_int(n_candidates) and 1 <= n_candidates <= n_iter,
        f"{field}.n_candidates",
        "inteiro em [1, n_iter]",
    )
    space, best = search["param_distributions"], search["best_params"]
    _check_params(space, f"{field}.param_distributions")
    _require(
        bool(space) and all(str(k).startswith(_PARAM_PREFIXES) for k in space),
        f"{field}.param_distributions",
        "nao vazio, chaves model__/preprocess__",
    )
    _check_params(best, f"{field}.best_params")
    _require(set(best) == set(space), f"{field}.best_params", "chaves = param_distributions")
    _require(
        all(k in params and params[k] == best[k] for k in best),
        f"{field}.best_params",
        "deve coincidir com params",
    )


def _check_model(name: str, block: Any, doc: dict[str, Any], n_splits: int) -> None:
    field = f"models.{name}"
    _require(isinstance(block, dict), field, "deve ser objeto")
    status = block.get("status")
    if isinstance(status, str) and status.startswith(STATUS_REMOVED_PREFIX):
        _require(bool(status[len(STATUS_REMOVED_PREFIX) :].strip()), field, "motivo vazio")
        _require("metrics" not in block, f"{field}.metrics", "modelo removido sem metrics")
        return
    _require(status == STATUS_EVALUATED, f"{field}.status", "'avaliado' ou 'removido: <motivo>'")
    _check_params(block.get("params"), f"{field}.params")
    reported = doc["metrics_reported"]
    metrics = block.get("metrics")
    _require(isinstance(metrics, dict) and set(metrics) == set(reported), f"{field}.metrics", "6")
    for metric in reported:
        _check_summary(metrics[metric], f"{field}.metrics.{metric}", n_splits, upper=1.0)
    search = block.get("search")
    if search is not None:
        _check_search(search, block["params"], doc, f"{field}.search")
    for timing in ("fit_time", "score_time"):
        if search is None:
            _check_summary(block.get(timing), f"{field}.{timing}", n_splits, upper=None)
        else:
            _check_search_timing(block.get(timing), f"{field}.{timing}")


def _check_search_mode(doc: dict[str, Any]) -> None:
    evaluated = {
        name: block for name, block in doc["models"].items() if block["status"] == STATUS_EVALUATED
    }
    has_search = any(block.get("search") is not None for block in evaluated.values())
    for name, block in evaluated.items():
        _require(
            (block.get("search") is not None) == has_search,
            f"models.{name}.search",
            "todos os modelos avaliados com busca ou todos sem busca",
        )
    selected_from = doc["selected_from"]
    if not has_search:
        _require(selected_from is None, "selected_from", "deve ser null em EXP sem busca")
        return
    _require(
        isinstance(selected_from, str)
        and bool(_EXPERIMENT_ID.match(selected_from))
        and selected_from != doc["experiment_id"],
        "selected_from",
        "EXP-NNN de origem, diferente de experiment_id, em EXP com busca",
    )


def _check_file_name(doc: dict[str, Any], path: Path) -> None:
    target = Path(path)
    _require(
        target.suffix == ".json" and target.stem == doc["experiment_id"],
        "experiment_id",
        f"nome do arquivo deve ser {doc['experiment_id']}.json (recebido {target.name})",
    )


def validate_metrics(doc: dict[str, Any], path: Path | None = None) -> None:
    """Valida um documento ``kind="cv"`` (com ou sem busca) pelas regras de ADR-0012 D9.

    Args:
        doc: documento montado por ``build_cv_report`` ou lido de ``reports/metrics/``.
        path: arquivo de origem ou destino, se houver; o nome deve ser ``<experiment_id>.json``.

    Raises:
        ValueError: com o campo e o motivo da primeira regra violada.
    """
    _check_header(doc)
    if path is not None:
        _check_file_name(doc, path)
    n_splits = _check_cv(doc["cv"], doc["seed"])
    _check_context(doc)
    models = doc["models"]
    _require(isinstance(models, dict) and bool(models), "models", "objeto nao vazio")
    for name, block in models.items():
        _check_model(name, block, doc, n_splits)
    _check_search_mode(doc)


def write_metrics(doc: dict[str, Any], path: Path) -> None:
    """Valida e grava o documento em JSON (UTF-8, indent=2, sort_keys, sem NaN).

    Args:
        doc: documento de metricas.
        path: destino ``<experiment_id>.json`` dentro de ``config.PROJECT_ROOT``.

    Raises:
        ValueError: documento invalido, nome diferente do experiment_id ou caminho fora da raiz.
        FileExistsError: o destino ja existe (registros nao sao sobrescritos).
    """
    validate_metrics(doc, path)
    target = Path(path).resolve()
    if not target.is_relative_to(config.PROJECT_ROOT.resolve()):
        raise ValueError(f"Destino fora da raiz do projeto: {target}.")
    content = json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content + "\n")


def _ranking_key(item: tuple[str, dict[str, Any]]) -> tuple[float, float, float, str]:
    name, block = item
    primary = block["metrics"][config.PRIMARY_METRIC]
    return (-primary["mean"], primary["std"], block["fit_time"]["mean"], name)


def select_top_candidates(doc: dict[str, Any]) -> list[str]:
    """Aplica a regra D7 (S10): top ``TUNING_N_CANDIDATES`` por f1_macro, sem o Dummy.

    Ordem: ``f1_macro.mean`` decrescente, ``f1_macro.std`` crescente, ``fit_time.mean``
    crescente (igualdade exata) e nome. Candidatos abaixo do Dummy continuam elegiveis.

    Args:
        doc: documento ``kind="cv"`` valido.

    Returns:
        Nomes selecionados, na ordem de D7.

    Raises:
        ValueError: documento invalido, metrica principal diferente ou poucos elegiveis.
    """
    validate_metrics(doc)
    _require(doc["primary_metric"] == config.PRIMARY_METRIC, "primary_metric", "difere do config")
    eligible = [
        (name, block)
        for name, block in doc["models"].items()
        if name != BASELINE_MODEL and block["status"] == STATUS_EVALUATED
    ]
    if len(eligible) < config.TUNING_N_CANDIDATES:
        raise ValueError(
            f"Elegiveis insuficientes: {len(eligible)} < {config.TUNING_N_CANDIDATES} (D7)."
        )
    ranked = sorted(eligible, key=_ranking_key)
    return [name for name, _ in ranked[: config.TUNING_N_CANDIDATES]]
