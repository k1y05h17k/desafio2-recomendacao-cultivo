# Runbook

Atualizado em 2026-11-07. Execute os comandos na raiz do projeto. Este documento descreve a reprodução da Entrega 1 usando os artefatos distribuídos; os registros históricos de implementação e verificação ficam apenas no ambiente local do autor.

## Aviso: conjunto de teste (holdout)

O holdout permanece intocado até a aprovação humana H4. Nenhum procedimento desta entrega requer datasets. Não repetir ingestão, recriar o split ou reabrir bruto/holdout. Até H4, métricas preditivas somente por validação cruzada no treino. Esta entrega não produz métricas de classificação.

## 1. Preparar o ambiente

Pré-requisito: [uv](https://docs.astral.sh/uv/). Não é necessário Python no PATH: o projeto usa Python 3.11, fixado em `.python-version`, com dependências em `uv.lock`.

```bash
uv --version
uv python find 3.11
uv sync --locked
uv run --locked python -c "import cultivo; print(cultivo.__name__)"
```

Resultados esperados: uv disponível, interpretador 3.11, instalação com saída 0 e importação imprimindo `cultivo`. `uv sync --locked` cria/atualiza `.venv` sem alterar o lock. Se houver incompatibilidade com `pyproject.toml`, interrompa e corrija a origem; não regenere o lock para contornar a falha. Instalação pode exigir rede. Esses são procedimentos de uso; esta revisão documental não repetiu instalação nem execução.

## 2. Rodar os testes (somente ambiente local do autor)

`tests/` não é distribuído pelo Git. Os comandos abaixo requerem esses arquivos locais e não são necessários para visualizar a entrega:

```bash
uv run --locked pytest -q
uv run --locked pytest -m smoke -q
uv run --locked pytest --cov=cultivo --cov-fail-under=85 -q
```

Resultado a conferir no ambiente completo: saída 0, nenhum erro/falha e cobertura mínima de 85%. Nenhuma nova contagem de testes é afirmada nesta revisão.

## 3. Lint e formatação (ambiente local completo)

```bash
uv run --locked ruff check src tests
uv run --locked ruff format --check src tests
```

Resultados esperados: saída 0 e arquivos sem alterações. Esses comandos também dependem de `tests/` local.

## 4. Qualidade pelo Makefile

Com GNU Make e o ambiente local completo:

```bash
make lint
make typecheck
make security
make test
make quality
```

`lint` verifica Ruff; `typecheck`, mypy; `security`, Bandit e auditoria de dependências; `test`, pytest e cobertura. `quality` exige todas as etapas aprovadas. Os alvos que usam testes dependem dos arquivos locais não distribuídos. A auditoria exige rede e grava exportação descartável em `.cache/requirements-audit.txt`. Falha de rede não equivale a ausência de vulnerabilidades.

## 5. Hooks de desenvolvimento

A configuração de hooks permanece somente no ambiente local do autor. Hooks não são pré-requisito para executar o notebook entregue. Os registros internos de qualidade, decisões e aprovações não fazem parte da distribuição pública.

## 6. Docker: Jupyter e execução pontual

Pré-requisitos: Docker Desktop com engine Linux e Docker Compose. A imagem usa Python 3.11, uv 0.13.7, ambiente `/opt/venv` e usuário `app` UID 1000. Há serviços `lab` e `app`, sem banco; a `.venv` Windows não é reutilizada no Linux.

Por solicitação do autor, o Jupyter dispensa token e senha, com porta restrita a `127.0.0.1`. Nenhuma variável `JUPYTER_TOKEN` é necessária:

```bash
docker compose config --quiet
docker compose config --services
docker compose up -d --build lab
docker compose ps
```

Resultados a conferir: validação saída 0, serviços `lab` e `app`, inicialização saída 0 e `lab` saudável após o período inicial. Abra [JupyterLab](http://127.0.0.1:8888/lab), [docs](http://127.0.0.1:8888/lab/tree/docs) ou o [notebook](http://127.0.0.1:8888/lab/tree/notebooks/00_entrega_parcial.ipynb), sem credenciais. Mantenha a porta restrita ao localhost.

`docs/`, `notebooks/`, `reports/`, `README.md`, `project/` e o PDF da rubrica são montados somente para leitura, assim como código/configuração. O volume `tool-cache` permite gravar em `/workspace/.cache`. Dados brutos, treino e holdout não são montados. A interface exibe JSONs/PNGs existentes e não recalcula a EDA. Alterações nos binds somente para leitura não são salvas no host.

Para executar uma cópia do notebook com outputs no cache gravável:

```bash
docker compose exec lab uv run --locked jupyter nbconvert --to notebook --execute --output 00_entrega_parcial --output-dir /workspace/.cache notebooks/00_entrega_parcial.ipynb
```

Confira saída 0 e o arquivo `/workspace/.cache/00_entrega_parcial.ipynb`; baixe uma cópia pelo navegador se precisar conservá-la. Não use `--inplace` no notebook montado em Docker. O guard do notebook exige o mesmo ambiente indicado por `UV_PROJECT_ENVIRONMENT`, ou `.venv` do projeto quando a variável não está definida. O comando acima é orientação de uso, sem nova execução nesta revisão.

O serviço `app` e os comandos de qualidade com testes dependem do ambiente local completo:

```bash
docker compose run --rm --no-deps app uv run --locked pytest -m smoke -q -p no:cacheprovider
make quality UV="docker compose run --rm --no-deps app uv"
```

Resultado esperado nesse ambiente: saída 0. Para encerrar os serviços:

```bash
docker compose down
```

Resultado esperado: saída 0. Não adicionar mounts de datasets para visualizar esta entrega.

## 7. Atalhos pipeline e exportação

```bash
make pipeline
make docs
```

`make pipeline` executa o notebook local. `make docs` ainda não implementa exportação. Esses alvos não executam avaliação final. Em Docker, use o procedimento da seção 6 para gravar outputs no cache.

## 8. Schema e integridade

O contrato das entradas está em `src/cultivo/data/`: sete features e alvo textual `label`. O [relatório de qualidade](../reports/data/quality.json) registra integridade agregada da etapa anterior ao split; não é EDA do holdout. Unidades, métodos e períodos de medição permanecem desconhecidos; finitude numérica não comprova plausibilidade agronômica. O CSV não é redistribuído porque a fonte não declara licença.

## 9. Split único preservado

O split já foi criado uma única vez. A reprodução do notebook não usa `load_train()`, ingestão ou split e não depende dos CSVs ausentes da distribuição. Não reconstruir o protegido usando o bruto ou metadados. Estados parciais de dados exigem intervenção humana; não apagar marcadores para repetir operações. H4 permanece pendente.

## 10. Interface EDA e pré-processamento

O [notebook](../notebooks/00_entrega_parcial.ipynb) lê apenas [EDA](../reports/data/eda.json), [extremos](../reports/data/outliers.json), [política de extremos](../reports/data/outlier-policy.json) e PNGs existentes. Exibir esses artefatos difere de recalcular a EDA. Não usar `run_eda()` para sobrescrever relatórios nesta reprodução.

A política S8 conserva 1760 observações e sete entradas, sem clipping/remoção. Futuro treinamento deve ajustar transformadores dentro de cada fold, com validação/inferência usando apenas transform. A EDA não pré-ajusta scaler, imputador ou clipping. O notebook não ajusta classificadores nem transformadores reais.

## 11. Entrega 1 — revisão acadêmica atual (2026-11-07)

Artefatos: [notebook](../notebooks/00_entrega_parcial.ipynb), [síntese](entrega-parcial/sintese.md) e [rubrica oficial](<../Modulo4_Rubricas_Avaliacao (1).pdf>). A entrega cobre problema, hipóteses exploratórias, interpretação da EDA e justificativa das sete entradas. As hipóteses foram formuladas depois da EDA inicial e verificadas descritivamente na mesma amostra; não são confirmação independente.

No host, com JSONs/PNGs já preparados e venv/kernel do projeto:

```bash
uv run --locked jupyter nbconvert --to notebook --execute --inplace notebooks/00_entrega_parcial.ipynb
```

Resultado a conferir: saída 0, 21 células de código executadas em ordem, 16 PNGs e nenhum output de erro. A última célula deve registrar `raw_holdout_open_attempts: 0`, `train_write_attempts: 0`, `dataset_csvs_read: False` e `real_fit_performed: False`. A execução exibe artefatos; não recalcula ciência nem consulta CSVs. Esta revisão alterou apenas documentação e preservou código/outputs existentes, sem reexecutar o notebook.

S9 aprovou `f1_macro` e `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)` para a etapa posterior. Aprovar o protocolo não significa experimento executado: não há métrica preditiva produzida neste notebook. Não há modelo final, SHAP ou banco nesta entrega. Verificações e aprovações internas ficam registradas apenas localmente; esta orientação não concede H4 nem encerra gates.
