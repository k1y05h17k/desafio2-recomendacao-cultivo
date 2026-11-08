# Recomendação de cultivo (Desafio 2)

Projeto acadêmico de classificação multiclasse: a partir de sete medições de solo e clima (`N`, `P`, `K`, `temperature`, `humidity`, `ph` e `rainfall`), indicar qual das 22 culturas do dataset (`label`) corresponde àquelas condições.

Usuário-alvo: produtor rural ou agrônomo que precisa de uma primeira indicação de cultura. Trata-se de uma prova de conceito acadêmica: a indicação apoia, mas não substitui, a avaliação agronômica, e não comprova produtividade nem generalização para outras regiões ou safras. Unidades, métodos e períodos de medição não são informados pela fonte. Problema e limites: [visão geral](project/overview.md).

## Entrega 1 — parcial

- [Notebook](notebooks/00_entrega_parcial.ipynb): problema e objetivo, hipóteses exploratórias, interpretação dos 16 gráficos da EDA, justificativa das sete variáveis, metodologia, primeiro experimento e próximos passos.
- [Síntese](docs/entrega-parcial/sintese.md): resumo de duas páginas com os mesmos itens.
- [Rubrica oficial](<Modulo4_Rubricas_Avaliacao (1).pdf>).

**Estado em 2026-11-08:** a [EDA do treino](reports/data/eda.json) registra 1760 observações, sete entradas, 22 classes e 80 registros por classe. As hipóteses foram formuladas após a EDA inicial e são checadas descritivamente, sem caráter confirmatório. O notebook lê JSONs e PNGs preparados e não treina modelos; ele apresenta os resultados do primeiro experimento (EXP-001, validação cruzada no treino).

A fonte é o GitHub `KrissshSaini/Crop-Recommendation-System`, CSV fixado no commit `a90b2ed5365bc558baef1ad4e327d2715e53ea2a` (origem declarada: Kaggle `atharvaingle/crop-recommendation-dataset`). O CSV não é redistribuído: a fonte não declara licença. A divisão treino/teste foi feita uma única vez. A [política de valores extremos](reports/data/outlier-policy.json) mantém todas as observações e as sete entradas, sem limitar nem remover valores; o `StandardScaler` é usado só na regressão logística e no MLP.

[EXP-001](reports/experiments/EXP-001.md): sete modelos comparados por validação cruzada estratificada (5 folds, seed 42) somente no treino, com F1 macro como métrica principal; a Random Forest teve 0,9948 ± 0,0052, e o baseline Dummy, 0,0040 ± 0,0000. O conjunto de teste reservado ainda não foi usado.

## Configuração e execução

### Preparação comum

1. Baixe e extraia o projeto ou clone o repositório pelo endereço fornecido pelo autor.
2. Abra um terminal na raiz do projeto: a pasta que contém `pyproject.toml` e `docker-compose.yml`.
3. Escolha **um** dos caminhos abaixo. Ambos usam a porta `8888`; encerre o ambiente anterior antes de trocar de caminho. Se o Docker já estiver rodando, use `docker compose down` antes de iniciar o Jupyter sem Docker.

| Caminho | Pré-requisitos |
|---|---|
| [Sem Docker](#sem-docker) | uv instalado; Python 3.11 gerenciado pelo uv, sem exigir Python no PATH. |
| [Com Docker](#com-docker) | Docker Desktop ou Docker Engine Linux com Compose ativo; dispensa Python e uv no computador. |

A primeira instalação de dependências ou construção da imagem pode exigir internet. O notebook distribuído já contém outputs salvos. Executá-lo exibe JSONs e PNGs preparados: não recalcula a EDA, não treina modelos e não acessa datasets; as métricas de validação cruzada do EXP-001 são apenas lidas e exibidas. Não é necessário repetir ingestão ou split. Detalhes: [runbook](docs/runbook.md), seções 6 e 11.

### Sem Docker

1. Instale o uv seguindo o [guia oficial](https://docs.astral.sh/uv/getting-started/installation/). No Windows, com WinGet disponível, use:

   ```powershell
   winget install --id=astral-sh.uv -e
   ```

2. Reabra o terminal na raiz do projeto, confira a instalação e prepare o ambiente:

   ```bash
   uv --version
   uv sync --locked
   ```

   O uv obtém o Python 3.11 indicado em `.python-version`, se necessário, cria `.venv` e instala as versões de `uv.lock`. Não é preciso ativar o ambiente manualmente. Consulte o [guia de Python gerenciado](https://docs.astral.sh/uv/guides/install-python/) para detalhes.

3. Inicie o JupyterLab local:

   ```bash
   uv run --locked jupyter lab --ip=127.0.0.1 --port=8888 --no-browser --IdentityProvider.token= --PasswordIdentityProvider.hashed_password=
   ```

   O comando mantém o terminal ocupado. O acesso sem token e senha fica restrito ao próprio computador pelo endereço `127.0.0.1`; mantenha esse endereço.

4. Abra o [notebook no JupyterLab](http://127.0.0.1:8888/lab/tree/notebooks/00_entrega_parcial.ipynb). Execute as células em ordem, de cima para baixo, pelo menu **Run → Run All Cells**. Salve com **Ctrl+S**; as alterações ficam no arquivo local.
5. Para encerrar, volte ao terminal, pressione **Ctrl+C** e confirme se solicitado.

Como alternativa à interface, execute e salve o notebook pelo terminal:

```bash
uv run --locked jupyter nbconvert --to notebook --execute --inplace notebooks/00_entrega_parcial.ipynb
```

Resultado esperado: conclusão sem erros e outputs descritivos atualizados no notebook, usando os artefatos existentes.

### Com Docker

1. Instale o [Docker Desktop](https://docs.docker.com/desktop/) para seu sistema e inicie-o com o engine Linux. No Linux, também é possível usar Docker Engine com o plugin Compose instalado e o daemon ativo.
2. Na raiz do projeto, confira Docker e Compose e valide a configuração:

   ```bash
   docker --version
   docker compose version
   docker info
   docker compose config --quiet
   ```

   O último comando deve terminar sem erros e sem saída.

3. Construa a imagem e inicie o serviço `lab`:

   ```bash
   docker compose up -d --build lab
   docker compose ps
   ```

   Aguarde `lab` aparecer como `healthy`; repita `docker compose ps` durante a inicialização, se necessário.

4. Abra o [JupyterLab](http://127.0.0.1:8888/lab), os [documentos](http://127.0.0.1:8888/lab/tree/docs) ou o [notebook](http://127.0.0.1:8888/lab/tree/notebooks/00_entrega_parcial.ipynb), sem token ou senha. O acesso é local, em `127.0.0.1:8888`.
5. No notebook, execute as células em ordem pelo menu **Run → Run All Cells**. Os materiais do projeto são montados somente para leitura e nenhum dataset é montado. Salvar sobre o original no host não é permitido. Para obter uma cópia executada, use o procedimento abaixo.

Para executar automaticamente e guardar uma nova cópia, com `lab` ativo, use o cache gravável e depois copie o resultado para o computador:

```bash
docker compose exec lab uv run --locked jupyter nbconvert --to notebook --execute --output 00_entrega_parcial --output-dir /workspace/.cache notebooks/00_entrega_parcial.ipynb
docker compose cp lab:/workspace/.cache/00_entrega_parcial.ipynb ./00_entrega_parcial.executado.ipynb
```

O resultado esperado é a execução sem erros e o arquivo `00_entrega_parcial.executado.ipynb` na raiz do projeto. Não use `--inplace` no notebook montado em Docker. A cópia segue a sintaxe oficial de [docker compose cp](https://docs.docker.com/reference/cli/docker/compose/cp/).

Para encerrar os serviços após a execução e a cópia, mantendo o volume de cache:

```bash
docker compose down
```

### Problemas comuns

| Problema | Como resolver |
|---|---|
| `uv` não encontrado | Instale pelo guia oficial e reabra o terminal. |
| Docker não conecta ao engine | Abra o Docker Desktop e aguarde o engine Linux ficar ativo; no Linux, confira o daemon. |
| Porta `8888` ocupada | Encerre o Jupyter anterior com Ctrl+C ou o serviço Docker com `docker compose down` antes de iniciar o outro caminho. |
| Erro ao salvar no Docker | O arquivo original é somente para leitura. Use o cache e `docker compose cp` para obter uma cópia executada, conforme acima. |

## Onde está cada coisa

| Caminho | Conteúdo |
|---|---|
| `src/cultivo/` | Configuração, ingestão, schema, split/carga de treino, EDA e pré-processamento. |
| `notebooks/00_entrega_parcial.ipynb` | Notebook da Entrega 1 (EDA, metodologia e EXP-001), com narrativa e outputs salvos. |
| `docs/entrega-parcial/sintese.md` | Síntese da Entrega 1. |
| `reports/data/`, `reports/figures/eda/` | Agregados descritivos, política de extremos e gráficos do treino. |
| `reports/metrics/`, `reports/experiments/` | Métricas e relatórios dos experimentos por validação cruzada no treino; a Entrega 1 apresenta o EXP-001. |
| `pyproject.toml`, `uv.lock`, `.python-version` | Dependências e versões do ambiente. |
| `docker/Dockerfile`, `docker-compose.yml` | Ambiente Docker restrito, sem banco. |
| `project/` | Contexto do problema e da implementação. |
| `docs/runbook.md` | Procedimentos de reprodução da entrega. |

O conjunto de teste reservado (holdout) permanece intocado até a entrega final; até lá, métricas preditivas somente por validação cruzada no treino.
