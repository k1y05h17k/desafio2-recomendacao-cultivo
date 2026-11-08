# Restrições do projeto

> Dono: `orchestrator`. **Alterações só com aprovação humana registrada em `docs/status.md`.** Última atualização: 2026-11-07.
> Restrições são inegociáveis. Violação de C-001 a C-004 é sempre **BLOCKER** na revisão.

## C-001 — Isolamento do holdout

O conjunto de teste (`data/holdout/`) é separado **uma única vez** e fica intocado até a aprovação humana **H4** (marco M4).
Até lá, as métricas vêm **somente de validação cruzada no treino**. Decisão: ADR-0001. Regra operacional: `.claude/rules/data-integrity.md`.

## C-002 — Fluxo obrigatório contra data leakage

Obrigatório:

```text
split
↓
train preprocessing fit
↓
model fit
↓
test transform
↓
predict
```

Proibido:

```text
full dataset
↓
scaler.fit
↓
split
```

Aplicação:

- Na **validação cruzada**, o mesmo fluxo vale dentro de cada fold: fit do pré-processamento e do modelo no fold de treino, transform e predict no fold de validação.
  Isso é garantido por `sklearn.pipeline.Pipeline` passado a `cross_validate`.
- No **holdout** (só depois da H4): fit do `Pipeline` no treino inteiro → transform/predict no holdout, **uma vez**.
- Vale para todo pré-processamento aprendido: escalonamento, imputação, encoding, seleção de features, balanceamento (ex.: oversampling).

## C-003 — Verificações de dados: o que roda antes e depois do split

| Antes do split (dataset completo): só integridade e estrutura | Depois do split (só treino): estatísticas que podem influenciar a modelagem |
|---|---|
| quantidade de registros, tipos, nulos, duplicatas, schema esperado vs. real, lista de classes e contagem por classe (necessária para estratificar e medir o balanceamento) | distribuição das features, outliers, correlações, gráficos da EDA |

Nenhuma decisão de tratamento (remoção de outliers, imputação) usa estatísticas do holdout.

## C-004 — Não presumir características dos dados

As colunas esperadas (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`, `label`) são **hipótese**.
Contagens, classes, balanceamento, tipos e faixas só são afirmados depois de verificados por execução, com evidência em `reports/data/`.
Nenhum documento, notebook ou síntese afirma uma característica do dataset sem essa evidência.

## C-005 - Fonte de dados fixada e segura

- Fonte aprovada pelo humano na retomada do Prompt14 (2026-11-07): CSV do GitHub KrissshSaini/Crop-Recommendation-System, arquivo Crop_recommendation.csv, revisão a90b2ed5365bc558baef1ad4e327d2715e53ea2a, registrada em data/raw/MANIFEST.json.
- A escolha substitui a referência anterior Hugging Face srikanta28/Crop_Recommendation, inacessível publicamente na pré-checagem TASK031. Não há fallback automático entre fontes.
- Integridade da origem e SHA256 do bruto são verificados/registrados conforme o mecanismo formalizado na ADR0009 e sua reconciliação para Prompt14; data/raw é imutável após ingestão.
- Proibido trust_remote_code=True. Nenhum dado bruto é versionado ou redistribuído; somente manifests/relatórios de integridade permitidos pelas regras do projeto.
## C-006 — Reprodutibilidade

- Seed única, definida em `src/cultivo/config.py` e propagada a todo componente aleatório.
- Ambiente gerenciado por `uv`, com lockfile versionado (`project/technology-stack.md`).
- Métricas sempre com média ± dp, seed e nº de folds.

## C-007 — Execução e entregas

- Execução **local** (Jupyter local, não Colab).
- Entrega parcial (M3.5): **2026-11-08**. Métricas só de CV (C-001).
- Documentação em pt-BR.

## C-008 — Escopo de infraestrutura

Sem serviço de banco, API ou deploy, salvo ADR aceita. A persistência segue a ADR-0002.
