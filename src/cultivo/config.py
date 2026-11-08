"""Configuração central do projeto: constantes de módulo (ADR-0006).

Este módulo não importa nada do pacote `cultivo` (ADR-0007, regra 1) e não lê arquivos.
Valor ainda não decidido fica `None`; quem o usa deve levantar um erro claro.
"""

from pathlib import Path

# Caminhos, todos dentro da raiz do projeto (src/cultivo/config.py -> raiz).
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
HOLDOUT_DIR: Path = PROJECT_ROOT / "data" / "holdout"  # só o caminho; leitura bloqueada até a H4
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# Hipótese de C-004: confirmada só pela validação de schema na ingestão.
TARGET: str = "label"
EXPECTED_FEATURES: tuple[str, ...] = (
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
)

# Protocolo experimental: seed/split da H2; CV, metricas, busca e paralelismo da ADR-0012 D6
# (S9/S11). Mudar SEARCH_N_ITER depois que o EXP-002 rodar exige nova ADR.
SEED: int = 42
TEST_SIZE: float = 0.2
CV_N_SPLITS: int = 5
CV_SHUFFLE: bool = True
PRIMARY_METRIC: str = "f1_macro"
REPORTED_METRICS: tuple[str, ...] = (
    "precision_macro",
    "recall_macro",
    "f1_macro",
    "precision_weighted",
    "recall_weighted",
    "f1_weighted",
)
SEARCH_N_ITER: int = 30
TUNING_N_CANDIDATES: int = 3
# Paralelismo em nivel unico (ADR-0012 D5): so no nivel externo; estimadores com 1 job.
N_JOBS: int = -1
ESTIMATOR_N_JOBS: int = 1

# Fonte publica fixada por commit (ADR-0009 e ADR-0010).
DATASET_ID: str = "KrissshSaini/Crop-Recommendation-System"
DATASET_REVISION: str = "a90b2ed5365bc558baef1ad4e327d2715e53ea2a"
DATASET_FILE: str = "Crop_recommendation.csv"
DATASET_URL: str = (
    f"https://raw.githubusercontent.com/{DATASET_ID}/{DATASET_REVISION}/{DATASET_FILE}"
)
DATASET_SIZE_BYTES: int = 150034
DATASET_GIT_BLOB_SHA1: str = "31dbf061867597840c9afd69ed825163adb31f2f"
DATASET_DECLARED_ORIGIN: str = "kaggle:atharvaingle/crop-recommendation-dataset"
