"""Registry dos 7 candidatos e espacos de busca do EXP-002 (ADR-0004, ADR-0012 D4/D5/D9).

Cada construtor devolve um ``Pipeline`` novo e nao ajustado com os passos
``[("preprocess", build_preprocessor(scaling=...)), ("model", estimador)]``.
Os hiperparametros fixos ficam nas constantes abaixo, declaradas antes de qualquer
resultado (TASK-048). Onde coincidem com o padrao da biblioteca, sao explicitados
para ficarem registrados em ``params`` no JSON de metricas.
``PARAM_DISTRIBUTIONS`` guarda os espacos do ``RandomizedSearchCV`` dos 3 candidatos do
EXP-001 (D7), aprovados no PLAN_READY da TASK-049.
"""

from collections.abc import Callable
from typing import Any, Literal

from scipy.stats import loguniform, randint, uniform
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from cultivo.config import ESTIMATOR_N_JOBS, SEED
from cultivo.features.preprocessing import build_preprocessor

DUMMY_PARAMS: dict[str, Any] = {"strategy": "most_frequent"}
# Sem n_jobs (ADR-0012 D5 item 2) e sem penalty (deprecated no scikit-learn 1.9; padrao L2).
LOGREG_PARAMS: dict[str, Any] = {"C": 1.0, "solver": "lbfgs", "max_iter": 1000}
DECISION_TREE_PARAMS: dict[str, Any] = {
    "criterion": "gini",
    "max_depth": None,
    "min_samples_leaf": 1,
}
RANDOM_FOREST_PARAMS: dict[str, Any] = {
    "n_estimators": 100,
    "criterion": "gini",
    "max_depth": None,
    "max_features": "sqrt",
}
XGBOOST_PARAMS: dict[str, Any] = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.3,
    "tree_method": "hist",
    "objective": "multi:softprob",
    "eval_metric": "mlogloss",
}
# verbose nao definido: os logs nativos do LightGBM ficam visiveis (decisao Q-2 do orchestrator).
LIGHTGBM_PARAMS: dict[str, Any] = {"n_estimators": 100, "learning_rate": 0.1, "num_leaves": 31}
MLP_PARAMS: dict[str, Any] = {
    "hidden_layer_sizes": (100,),
    "activation": "relu",
    "solver": "adam",
    "alpha": 0.0001,
    "max_iter": 1000,
    "early_stopping": False,
}


def _compose(scaling: Literal["none", "standard"], estimator: object) -> Pipeline:
    return Pipeline([("preprocess", build_preprocessor(scaling=scaling)), ("model", estimator)])


def _dummy() -> Pipeline:
    return _compose("none", DummyClassifier(**DUMMY_PARAMS, random_state=SEED))


def _logreg() -> Pipeline:
    return _compose("standard", LogisticRegression(**LOGREG_PARAMS, random_state=SEED))


def _decision_tree() -> Pipeline:
    return _compose("none", DecisionTreeClassifier(**DECISION_TREE_PARAMS, random_state=SEED))


def _random_forest() -> Pipeline:
    model = RandomForestClassifier(
        **RANDOM_FOREST_PARAMS, random_state=SEED, n_jobs=ESTIMATOR_N_JOBS
    )
    return _compose("none", model)


def _xgboost() -> Pipeline:
    from xgboost import XGBClassifier  # import tardio: ImportError vira "removido" (ADR-0004)

    model = XGBClassifier(**XGBOOST_PARAMS, random_state=SEED, n_jobs=ESTIMATOR_N_JOBS)
    return _compose("none", model)


def _lightgbm() -> Pipeline:
    from lightgbm import LGBMClassifier  # import tardio: ImportError vira "removido" (ADR-0004)

    model = LGBMClassifier(**LIGHTGBM_PARAMS, random_state=SEED, n_jobs=ESTIMATOR_N_JOBS)
    return _compose("none", model)


def _mlp() -> Pipeline:
    return _compose("standard", MLPClassifier(**MLP_PARAMS, random_state=SEED))


# Espacos do EXP-002 (TASK-049, plano secao A). Notacao scipy.stats: randint(a, b) em [a, b);
# uniform(loc, scale) em [loc, loc + scale]; loguniform(a, b) em [a, b]. Parametros fora do
# espaco ficam como nos construtores acima (inclusive random_state e n_jobs).
_N_ESTIMATORS_RANGE = (100, 501)
_FRACTION_RANGE = (0.6, 0.4)  # uniform -> [0.6, 1.0]
_LEARNING_RATE_RANGE = (0.01, 0.3)

PARAM_DISTRIBUTIONS: dict[str, dict[str, Any]] = {
    "random_forest": {
        "model__n_estimators": randint(*_N_ESTIMATORS_RANGE),
        "model__max_depth": [None, 8, 16, 32],
        "model__max_features": ["sqrt", 0.5, 0.75, None],
        "model__min_samples_leaf": randint(1, 6),
        "model__min_samples_split": randint(2, 11),
        "model__criterion": ["gini", "entropy"],
    },
    "xgboost": {
        "model__n_estimators": randint(*_N_ESTIMATORS_RANGE),
        "model__max_depth": randint(3, 11),
        "model__learning_rate": loguniform(*_LEARNING_RATE_RANGE),
        "model__subsample": uniform(*_FRACTION_RANGE),
        "model__colsample_bytree": uniform(*_FRACTION_RANGE),
        "model__reg_lambda": loguniform(0.1, 10.0),
    },
    "lightgbm": {
        "model__n_estimators": randint(*_N_ESTIMATORS_RANGE),
        "model__learning_rate": loguniform(*_LEARNING_RATE_RANGE),
        "model__num_leaves": randint(8, 64),
        "model__min_child_samples": randint(5, 31),
        "model__subsample": uniform(*_FRACTION_RANGE),
        # subsample so tem efeito com subsample_freq > 0 (padrao 0); fixo no espaco, nao no
        # construtor, para nao mudar o lightgbm do EXP-001.
        "model__subsample_freq": [1],
        "model__colsample_bytree": uniform(*_FRACTION_RANGE),
        "model__reg_lambda": loguniform(0.001, 10.0),
    },
}

MODEL_REGISTRY: dict[str, Callable[[], Pipeline]] = {
    "dummy": _dummy,
    "logreg": _logreg,
    "decision_tree": _decision_tree,
    "random_forest": _random_forest,
    "xgboost": _xgboost,
    "lightgbm": _lightgbm,
    "mlp": _mlp,
}


def build_pipeline(name: str) -> Pipeline:
    """Devolve um Pipeline novo e nao ajustado do candidato ``name``.

    Args:
        name: chave de ``MODEL_REGISTRY``.

    Returns:
        Pipeline ``preprocess`` + ``model`` sem fit.

    Raises:
        KeyError: nome desconhecido; a mensagem lista os nomes validos.
    """
    try:
        builder = MODEL_REGISTRY[name]
    except KeyError:
        valid = ", ".join(sorted(MODEL_REGISTRY))
        raise KeyError(f"Modelo desconhecido: {name!r}. Nomes validos: {valid}.") from None
    return builder()
