"""Pre-processamento sem I/O; cada clone aprende somente no seu fold."""

from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from pandas.api.types import is_bool_dtype, is_complex_dtype, is_numeric_dtype
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.utils.validation import check_is_fitted

from cultivo.config import EXPECTED_FEATURES


def _ordered_values(x: pd.DataFrame) -> NDArray[np.float64]:
    if not isinstance(x, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame with the configured features.")
    if x.columns.has_duplicates:
        raise ValueError("Duplicate feature columns are not allowed.")
    if set(x.columns) != set(EXPECTED_FEATURES):
        raise ValueError("Columns must match EXPECTED_FEATURES exactly.")
    ordered = x.loc[:, list(EXPECTED_FEATURES)]
    for dtype in ordered.dtypes:
        if not is_numeric_dtype(dtype) or is_bool_dtype(dtype) or is_complex_dtype(dtype):
            raise TypeError("Features must have real numeric dtypes without coercion.")
    if ordered.isna().any().any():
        raise ValueError("Null feature values are not allowed.")
    values = ordered.to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(values).all():
        raise ValueError("Feature values must be finite.")
    return values


class _FeatureValidator(TransformerMixin, BaseEstimator):
    """Confere schema em fit/transform e preserva nomes e ordem canonicos."""

    def fit(self, x: pd.DataFrame, y: object = None) -> "_FeatureValidator":
        """Valida features e registra o estado ajustado; y nao e alterado."""
        _ordered_values(x)
        self.n_features_in_ = len(EXPECTED_FEATURES)
        self.feature_names_in_ = np.asarray(EXPECTED_FEATURES, dtype=object)
        return self

    def transform(self, x: pd.DataFrame) -> NDArray[np.float64]:
        """Valida a inferencia e devolve matriz copiada na ordem configurada."""
        check_is_fitted(self)
        return _ordered_values(x)

    def get_feature_names_out(self, input_features: object = None) -> NDArray[np.object_]:
        """Devolve nomes canonicos apos fit, conferindo nomes opcionais."""
        check_is_fitted(self)
        if input_features is not None and not np.array_equal(
            np.asarray(input_features, dtype=object), self.feature_names_in_
        ):
            raise ValueError("input_features must match the configured feature order.")
        return self.feature_names_in_.copy()


def build_preprocessor(*, scaling: Literal["none", "standard", "minmax"]) -> Pipeline:
    """Cria Pipeline nao ajustado; scaling e obrigatorio e nao escolhe familia."""
    if scaling not in ("none", "standard", "minmax"):
        raise ValueError("scaling must be one of: none, standard, minmax.")
    scaler: str | StandardScaler | MinMaxScaler = "passthrough"
    if scaling == "standard":
        scaler = StandardScaler()
    elif scaling == "minmax":
        scaler = MinMaxScaler()
    return Pipeline([("validate", _FeatureValidator()), ("scaling", scaler)])
