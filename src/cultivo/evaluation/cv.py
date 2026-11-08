"""Validacao cruzada e busca aleatoria somente no treino (ADR-0012 D3/D4/D5/D9).

Nenhuma funcao deste modulo le arquivos: dados e Pipeline chegam por parametro.
"""

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.base import clone
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from cultivo import config

STD_DDOF = 1
SEARCH_STRATEGY = "RandomizedSearchCV"
_JSON_SCALARS = (str, bool, int, type(None))


def build_cv() -> StratifiedKFold:
    """Cria o StratifiedKFold do protocolo a partir de ``config``.

    Returns:
        ``StratifiedKFold(CV_N_SPLITS, shuffle=CV_SHUFFLE, random_state=SEED)``.

    Raises:
        ValueError: constante ausente (None) ou ``CV_N_SPLITS < 2``.
    """
    n_splits, shuffle, seed = config.CV_N_SPLITS, config.CV_SHUFFLE, config.SEED
    if n_splits is None or shuffle is None or seed is None:
        raise ValueError("CV_N_SPLITS, CV_SHUFFLE e SEED devem estar definidos em config.")
    if type(n_splits) is not int or n_splits < 2:
        raise ValueError(f"CV_N_SPLITS deve ser inteiro >= 2; recebido {n_splits!r}.")
    return StratifiedKFold(n_splits=n_splits, shuffle=shuffle, random_state=seed)


def encode_labels(y: pd.Series) -> tuple[NDArray[np.int64], list[str]]:
    """Codifica rotulos em indices de classes ordenadas, sem mutar ``y``.

    Args:
        y: rotulos do alvo.

    Returns:
        ``(y_enc, classes)``: indices ``int64`` e ``sorted(set(y))`` como ``str``.

    Raises:
        ValueError: ``y`` vazio ou com nulos.
    """
    if len(y) == 0:
        raise ValueError("y vazio: nada a codificar.")
    if y.isna().any():
        raise ValueError("y contem nulos; rotulos devem estar completos.")
    labels = y.astype(str).to_numpy()
    classes = sorted(set(labels.tolist()))
    index = {label: position for position, label in enumerate(classes)}
    y_enc = np.fromiter((index[label] for label in labels), dtype=np.int64, count=len(labels))
    return y_enc, classes


def decode_labels(y_enc: NDArray[np.integer[Any]], classes: Sequence[str]) -> NDArray[np.object_]:
    """Inverso de ``encode_labels``.

    Args:
        y_enc: indices de classe.
        classes: nomes das classes na ordem de codificacao.

    Returns:
        Array de rotulos ``str`` (dtype object).

    Raises:
        ValueError: indice fora de ``[0, len(classes))``.
    """
    codes = np.asarray(y_enc)
    if codes.size and (codes.min() < 0 or codes.max() >= len(classes)):
        raise ValueError(f"Indice de classe fora de [0, {len(classes)}).")
    return np.asarray(classes, dtype=object)[codes.astype(np.int64)]


def _json_value(value: object) -> object:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, _JSON_SCALARS):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    return repr(value)


def _model_params(pipeline: Pipeline) -> dict[str, object]:
    model_params = pipeline.named_steps["model"].get_params(deep=False)
    params = {f"model__{key}": _json_value(val) for key, val in sorted(model_params.items())}
    scaling = pipeline.named_steps["preprocess"].named_steps["scaling"]
    params["preprocess__scaling"] = _json_value(scaling)
    return params


def _summary(values: NDArray[np.float64]) -> dict[str, object]:
    folds = [float(v) for v in values]
    return {
        "mean": float(np.mean(folds)),
        "std": float(np.std(folds, ddof=STD_DDOF)),
        "folds": folds,
    }


def _check_inputs(x: pd.DataFrame, y_enc: NDArray[np.int64], cv: StratifiedKFold) -> None:
    if len(x) != len(y_enc):
        raise ValueError(f"len(X)={len(x)} difere de len(y_enc)={len(y_enc)}.")
    n_splits = cv.get_n_splits()
    if n_splits < 2:
        raise ValueError(f"cv.n_splits deve ser >= 2; recebido {n_splits}.")
    counts = np.bincount(np.asarray(y_enc, dtype=np.int64))
    present = counts[counts > 0]
    if present.size == 0 or present.min() < n_splits:
        raise ValueError(f"Alguma classe tem menos de {n_splits} amostras (n_splits).")


def evaluate_cv(
    pipeline: Pipeline, x: pd.DataFrame, y_enc: NDArray[np.int64], cv: StratifiedKFold
) -> dict[str, Any]:
    """Avalia o Pipeline por CV, com fit do Pipeline inteiro em cada fold.

    Args:
        pipeline: Pipeline nao ajustado (``preprocess`` + ``model``); nao e modificado.
        x: features do treino.
        y_enc: rotulos codificados por ``encode_labels``.
        cv: o ``StratifiedKFold`` de ``build_cv()``.

    Returns:
        Bloco "modelo" do JSON: ``status``, ``params``, ``metrics`` (6 metricas com mean, std
        ddof=1 e folds), ``fit_time``, ``score_time`` (segundos) e ``search=None``.

    Raises:
        ValueError: tamanhos diferentes, ``n_splits < 2`` ou classe com menos de n_splits amostras.
    """
    _check_inputs(x, y_enc, cv)
    scores = cross_validate(
        pipeline,
        x,
        y_enc,
        cv=cv,
        scoring=list(config.REPORTED_METRICS),
        n_jobs=config.N_JOBS,
        error_score="raise",
        return_train_score=False,
    )
    return {
        "status": "avaliado",
        "params": _model_params(pipeline),
        "metrics": {m: _summary(scores[f"test_{m}"]) for m in config.REPORTED_METRICS},
        "fit_time": _summary(scores["fit_time"]),
        "score_time": _summary(scores["score_time"]),
        "search": None,
    }


def _best_index(ranks: Sequence[int] | NDArray[np.integer[Any]]) -> int:
    """Menor indice com rank 1 (desempate deterministico do melhor ponto, ADR-0012 D4)."""
    tops = [index for index, rank in enumerate(ranks) if int(rank) == 1]
    if not tops:
        raise ValueError("Nenhum ponto com rank 1 em cv_results_.")
    return tops[0]


def _describe_distribution(dist: Any) -> object:
    if isinstance(dist, list):
        return [_json_value(v) for v in dist]
    frozen = getattr(dist, "dist", None)
    name = getattr(frozen, "name", None)
    if not isinstance(name, str) or not hasattr(dist, "rvs"):
        raise ValueError(f"Distribuicao nao suportada no espaco de busca: {dist!r}.")
    args = [repr(_json_value(a)) for a in dist.args]
    kwds = [f"{key}={_json_value(val)!r}" for key, val in sorted(dist.kwds.items())]
    return f"{name}({', '.join([*args, *kwds])})"


def _describe_space(param_distributions: dict[str, Any]) -> dict[str, object]:
    """Descricao textual deterministica do espaco (sem enderecos de memoria; Q-2 da TASK-049)."""
    return {key: _describe_distribution(val) for key, val in sorted(param_distributions.items())}


def _search_summary(results: dict[str, Any], best: int, n_splits: int) -> dict[str, Any]:
    metrics = {
        m: _summary(np.asarray([results[f"split{k}_test_{m}"][best] for k in range(n_splits)]))
        for m in config.REPORTED_METRICS
    }
    timings = {
        timing: {
            "mean": float(results[f"mean_{timing}"][best]),
            "std": float(results[f"std_{timing}"][best]),  # ddof=0 do scikit-learn (D9)
            "folds": [],
        }
        for timing in ("fit_time", "score_time")
    }
    return {"metrics": metrics, **timings}


def tune_cv(
    pipeline: Pipeline,
    param_distributions: dict[str, Any],
    x: pd.DataFrame,
    y_enc: NDArray[np.int64],
    cv: StratifiedKFold,
) -> dict[str, Any]:
    """Busca aleatoria por CV no treino e bloco "modelo" do melhor ponto (ADR-0012 D4/D9).

    Args:
        pipeline: Pipeline nao ajustado (``preprocess`` + ``model``); nao e modificado.
        param_distributions: espaco (listas ou distribuicoes ``scipy.stats``).
        x: features do treino.
        y_enc: rotulos codificados por ``encode_labels``.
        cv: o ``StratifiedKFold`` de ``build_cv()``.

    Returns:
        Bloco com ``status``, ``params`` (com o melhor ponto aplicado), ``metrics`` (6 metricas,
        mean e std ddof=1 recalculados de ``split{k}_test_<m>``), ``fit_time``/``score_time``
        (``folds=[]``, std ddof=0) e ``search``.

    Raises:
        ValueError: entradas invalidas (como em ``evaluate_cv``) ou nenhum ponto com rank 1.
    """
    _check_inputs(x, y_enc, cv)
    search = RandomizedSearchCV(
        pipeline,
        param_distributions,
        n_iter=config.SEARCH_N_ITER,
        scoring={m: m for m in config.REPORTED_METRICS},
        refit=False,
        cv=cv,
        random_state=config.SEED,
        n_jobs=config.N_JOBS,
        error_score="raise",
    )
    search.fit(x, y_enc)
    results = search.cv_results_
    best = _best_index(results[f"rank_test_{config.PRIMARY_METRIC}"])
    best_params = {key: _json_value(val) for key, val in sorted(results["params"][best].items())}
    tuned = clone(pipeline).set_params(**results["params"][best])
    return {
        "status": "avaliado",
        "params": _model_params(tuned),
        **_search_summary(results, best, cv.get_n_splits()),
        "search": {
            "strategy": SEARCH_STRATEGY,
            "n_iter": config.SEARCH_N_ITER,
            "random_state": config.SEED,
            "refit_metric": config.PRIMARY_METRIC,
            "param_distributions": _describe_space(param_distributions),
            "best_params": best_params,
            "n_candidates": len(results["params"]),
        },
    }
