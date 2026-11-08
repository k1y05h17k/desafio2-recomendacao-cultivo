# Recomendação de cultivo (Desafio 2)

Projeto acadêmico de classificação multiclasse: investigar padrões de solo e clima associados às culturas rotuladas no dataset. As sete entradas são `N`, `P`, `K`, `temperature`, `humidity`, `ph` e `rainfall`; a saída futura é uma categoria `label`. Nesta parcial, a entrega efetiva é a análise exploratória que fundamenta essa tarefa.

O público proposto são estudantes e analistas de um protótipo de triagem de culturas. O estudo apoia a investigação de padrões entre medições e rótulos; não comprova adequação agronômica, produtividade ou generalização para outras regiões/safras e não prescreve plantio. Unidades, métodos e períodos de medição permanecem desconhecidos. Problema e limites: [visão geral](project/overview.md).

## Entrega 1 — parcial (40%)

- [Notebook acadêmico](notebooks/00_entrega_parcial.ipynb): problema delimitado, hipóteses exploratórias com cronologia explícita, interpretação dos 16 gráficos e justificativa das sete variáveis.
- [Síntese acadêmica](docs/entrega-parcial/sintese.md): resultados descritivos e limites em formato conciso.
- [Rubrica oficial](<Modulo4_Rubricas_Avaliacao (1).pdf>).

**Estado em 2026-11-07:** a [EDA do treino](reports/data/eda.json) registra 1760 observações, sete entradas, 22 classes e 80 registros por classe. A revisão narrativa mantém as hipóteses identificadas como formuladas após a EDA inicial, sem apresentá-las como testes confirmatórios. O notebook lê JSONs e PNGs preparados; não treina modelos.

A fonte aprovada é o GitHub `KrissshSaini/Crop-Recommendation-System`, CSV fixado no commit `a90b2ed5365bc558baef1ad4e327d2715e53ea2a`. O CSV não é redistribuído: a fonte não declara licença. O split único está preservado. A [política S8](reports/data/outlier-policy.json) mantém todas as observações e sete entradas, sem clipping/remoção; S7 define StandardScaler para LogReg/MLP e `none` para as demais famílias.

S9 aprovou `f1_macro` e `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`. Isso não comprova execução de experimentos, que não fazem parte deste notebook nem são exigidos pelos quatro critérios da Entrega 1. H4 não foi concedida.

## Configuração e execução

### Preparação comum

1. Baixe e extraia o projeto ou clone o repositório pelo endereço fornecido pelo autor.
2. Abra um terminal na raiz do projeto: a pasta que contém `pyproject.toml` e `docker-compose.yml`.
3. Escolha **um** dos caminhos abaixo. Ambos usam a porta `8888`; encerre o ambiente anterior antes de trocar de caminho. Se o Docker já estiver rodando, use `docker compose down` antes de iniciar o Jupyter sem Docker.

| Caminho | Pré-requisitos |
|---|---|
| [Sem Docker](#sem-docker) | uv instalado; Python 3.11 gerenciado pelo uv, sem exigir Python no PATH. |
| [Com Docker](#com-docker) | Docker Desktop ou Docker Engine Linux com Compose ativo; dispensa Python e uv no computador. |

A primeira instalação de dependências ou construção da imagem pode exigir internet. O notebook distribuído já contém outputs salvos. Executá-lo exibe JSONs e PNGs preparados: não recalcula a EDA, não treina modelos e não acessa datasets. Não é necessário repetir ingestão ou split. Detalhes: [runbook](docs/runbook.md), seções 6 e 11.

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
| `notebooks/00_entrega_parcial.ipynb` | Interface acadêmica da EDA, com narrativa e outputs salvos. |
| `docs/entrega-parcial/sintese.md` | Síntese da Entrega 1. |
| `reports/data/`, `reports/figures/eda/` | Agregados descritivos, política de extremos e gráficos do treino. |
| `pyproject.toml`, `uv.lock`, `.python-version` | Dependências e versões do ambiente. |
| `docker/Dockerfile`, `docker-compose.yml` | Ambiente Docker restrito, sem banco. |
| `project/` | Contexto do problema e da implementação. |
| `docs/runbook.md` | Procedimentos de reprodução da entrega. |

O holdout permanece intocado até H4; até lá, métricas preditivas somente por validação cruzada no treino.
