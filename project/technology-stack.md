# Stack tecnológica

> Dono: `software-architect`. Última atualização: 2026-11-07 (TASK-024: ferramentas de dev da ADR-0008, cobertura de 85%, remoção de `datasets` pela ADR-0009, versões do `uv.lock` e backend `uv_build`).
> Versões travadas pelo `uv.lock` criado na TASK-003 (2026-11-07). A tabela "Bibliotecas" registra as versões resolvidas.

## Ambiente verificado (2026-11-07)

| Ferramenta | Situação na máquina | Evidência |
|---|---|---|
| `python` / `py` / `pip` no PATH | **ausentes** (`python` aponta para o atalho da Microsoft Store) | `python --version` → "Python was not found" |
| `uv` | **0.13.7** | `uv --version` |
| Interpretadores gerenciados pelo uv | CPython **3.11.18** e **3.15.2** | `uv python list --only-installed` |
| `git` | **2.56.0** (repositório inicializado em 2026-11-07, sem commit) | `git --version`; `docs/status.md` (B-3) |
| `docker` / `docker compose` | **29.9.2** / **v5.6.1**; daemon **não estava rodando** em 2026-11-07 | `docs/evidence/TASK-024/software-architect/ambiente.txt` |
| `make` | **GNU Make 4.4.1** (ezwinports, via WinGet) | idem |
| `conda`, `jupyter` | ausentes | comando não encontrado |

## Decisões de ambiente (propostas)

- **Gerenciador**: `uv`, a única ferramenta disponível. Ambiente em `.venv/` no projeto, com `uv.lock` versionado.
- **Python**: **3.11** (`requires-python = ">=3.11,<3.12"`).
  Motivo: a 3.15 é muito recente e a disponibilidade de wheels para `xgboost`, `lightgbm` e `shap` nela **não foi verificada**.
  Reavaliar se o `uv sync` falhar ou se houver motivo para outra versão.
- Todo comando roda via `uv run`, porque não há Python no PATH.

## Bibliotecas

Versões resolvidas pelo `uv.lock` da TASK-003 em 2026-11-07, para CPython 3.11.18.
Evidência: `docs/evidence/TASK-003/developer/handoff.md` (`resolved_versions`), conferido por leitura do `uv.lock` em `docs/evidence/TASK-024/software-architect/versoes-uvlock.txt`.

| Pacote | Versão (`uv.lock`) | Uso | REQ | Observação |
|---|---|---|---|---|
| `pandas` | 3.1.1 | manipulação de dados | — | 3.x: copy-on-write e dtype `string` padrão (risco no handoff da TASK-003) |
| `numpy` | 2.4.6 | manipulação de dados | — | |
| `scikit-learn` | 1.9.1 | Pipeline, CV, métricas, Dummy, LogReg, DecisionTree, RandomForest, MLP | REQ-005/006/007 | |
| `scipy` | 1.17.1 (`>=1.17,<2`) | distribuições `scipy.stats` nos espaços do `RandomizedSearchCV` (ADR-0012 D4) | REQ-015 | direta desde a TASK-052; antes era transitiva do scikit-learn |
| `xgboost` | 3.2.0 | candidato XGBoost | REQ-006 | pode ser removido com justificativa (ex.: wheel indisponível) |
| `lightgbm` | 4.7.0 | candidato LightGBM | REQ-006 | idem |
| `shap` | 0.51.0 | interpretação | REQ-008 | só no M4/M5; 0.x pode quebrar em minor, e o `uv.lock` protege |
| `matplotlib` | 3.11.2 | gráficos da EDA e dos resultados | REQ-003 | |
| `seaborn` | 0.13.2 | idem | REQ-003 | |
| `jupyter` | 1.1.1 | notebook local | REQ-010 | grupo dev (TASK-003) |
| `nbconvert` | 7.17.2 | execução de ponta a ponta | REQ-010 | grupo dev (TASK-003) |
| `ipykernel` | 7.4.0 | kernel do notebook | REQ-010 | grupo dev (TASK-003) |
| `pytest` | 9.2.0 | testes | — | grupo dev (TASK-003) |
| `pytest-cov` | 7.1.0 | cobertura | — | grupo dev (TASK-003) |
| `ruff` | 0.17.4 | lint e formatação | — | grupo dev (TASK-003) |
| `mypy` | — | checagem de tipos em `src/` | — | dev (ADR-0008 aceita; lock/sync TASK-025) |
| `bandit[toml]` | — | análise estática de segurança em `src/` | — | dev (ADR-0008 aceita; lock/sync TASK-025) |
| `pip-audit` | — | auditoria de vulnerabilidades das dependências do `uv.lock` | — | dev (ADR-0008 aceita; lock/sync TASK-025) |
| `pre-commit` | — | hooks de commit (ruff, mypy, bandit, chave privada, arquivo grande) | — | dev (ADR-0008 aceita; lock/sync TASK-025) |

**Backend de build:** `uv_build` (`[build-system] requires = ["uv_build>=0.13.7,<0.14"]`, `build-backend = "uv_build"`), aceito no G1 da TASK-003.
O teto `<0.14` é mais estrito que "limite de major" de propósito: o `uv_build` está em 0.x e acompanha a versão do `uv` (0.13.7).

Download do dataset: biblioteca padrão (`urllib.request`), sem dependência (ADR-0009, Proposta). O pacote `datasets` (Hugging Face) foi **removido da stack** em 2026-11-07 por decisão humana (P-9) e não deve entrar no `pyproject.toml`.

Política: versão mínima + limite superior de major em `pyproject.toml`, travadas por `uv.lock` (`.claude/rules/security-rules.md`).
Pacotes fora desta tabela exigem justificativa e, se forem estruturais, ADR.

## Comandos

```bash
uv python pin 3.11                       # fixa o interpretador do projeto
uv sync --locked                         # instala conforme uv.lock; falha se desatualizado
uv run pytest -q                         # testes
uv run pytest --cov=cultivo --cov-fail-under=85   # cobertura mínima de 85% em src/ (instrução humana 2026-11-07; valor de referência em [tool.coverage.report] fail_under = 85, que precisa ser igual, ADR-0008)
uv run ruff check src tests              # lint
uv run ruff format --check src tests     # formatação
uv run mypy src                          # tipos (ADR-0008)
uv run bandit -c pyproject.toml -r src   # segurança estática (ADR-0008)
uv export --locked --no-emit-project --format requirements-txt -o .cache/requirements-audit.txt
uv run pip-audit --strict --disable-pip --require-hashes -r .cache/requirements-audit.txt   # vulnerabilidades (ADR-0008; precisa de rede)
uv run pre-commit install                # instala os hooks (ADR-0008)
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/00_entrega_parcial.ipynb   # execução de ponta a ponta (ADR-0008: saídas gravadas no próprio notebook)
```

O `pyproject.toml` e o `uv.lock` existem desde a TASK-003, e a execução dos comandos do núcleo está nas evidências dela (`docs/evidence/TASK-003/`). Este documento não os reexecutou. Os comandos de `mypy`, `bandit`, `pip-audit` e `pre-commit` só passam a valer depois da TASK-025.

## Ambiente containerizado e atalhos (ADR-0008, Aceita)

Valem depois que a ADR-0008 for aceita e a TASK-025 criar os arquivos (a TASK-003 cria só o núcleo: `pyproject.toml`, `uv.lock`, `.gitignore`, `.python-version`). O caminho `uv` acima continua sendo o padrão.

```bash
make quality        # lint → typecheck → security → test (cobertura >= 85%)
make up             # docker compose up -d --build lab  (Jupyter em 127.0.0.1:8888; exige JUPYTER_TOKEN no .env)
make down           # docker compose down
make quality UV="docker compose run --rm app uv"       # mesmos alvos dentro do contêiner app, inclusive o uv export (sem uv no host)
```

Imagem: `python:3.11-slim-bookworm` (digest registrado na TASK-025), `uv` 0.13.7 da imagem oficial, `uv sync --locked`, usuário não-root `app` (UID 1000).
Serviços: `lab` e `app`, sem `db` (ADR-0002). Detalhes: `docs/adr/ADR-0008-ambiente-e-qualidade.md`.

## Evidência da continuação TASK-025

As quatro versões de ferramentas novas acima foram conferidas no lock/sync da TASK-025, registrado em docs/evidence/TASK-025/developer/checks.txt. A instalação local passou; isso não valida build Linux ou daemon Docker. A documentação operacional atual é docs/runbook.md.

## Proposta tecnica Prompt14 - TASK-030 (2026-11-07)

Pydanticv2 foi escolhido pelo humano para schema; proposta de declaracao `pydantic>=2,<3`, resolucao exata e lock pelo developer. Nao e afirmada instalacao nesta etapa. Motivo e alternativas na ADR-0010. Download continua stdlib/ADR-0009, sem datasets. config.py permanece fonte unica; seed42/test_size0.2 aprovados; demais parametros H2 pendentes. TD002: mounts seletivos e cache compartilhado de ferramentas, sem raiz/data/.env/holdout por padrao; implementacao e verificacao antes dos dados reais.