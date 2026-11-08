# Atualizacao aprovada do Prompt 14 - 2026-11-07

S5: instrucao humana corrente registrada em docs/status.md, Retomada aprovada do Prompt 14. Preservar cultivo/config.py; Pydantic v2; GitHub fixado; seed42/teste20% estratificado. H2 parcial; sem H4 ou Prompt15. Detalhes, dicionario e criterios P14-01..08: docs/requirements/prompt-14-reconciliation.md. Este bloco prevalece sobre referencias historicas HF abaixo.

# Requisitos

> Dono: `business-analyst`. Última atualização: 2026-11-07.
> Formato dos critérios: `.claude/templates/acceptance-criteria.md`. Todo REQ tem fonte. Sem fonte → `PENDENTE`.

## Fontes

| ID | Fonte | Data |
|---|---|---|
| S1 | Instrução do humano: "Configure as regras específicas deste projeto acadêmico de recomendação de cultivo" (objetivo, dataset, verificações, leakage, modelos, métricas, SHAP, persistência) | 2026-11-07 |
| S2 | Decisão do humano sobre a entrega parcial (notebook local + síntese de 1–2 páginas; métricas só de CV; baselines Dummy, LogReg, DecisionTree, RandomForest) | 2026-11-06 |
| S3 | Enunciado oficial do desafio | **PENDENTE** (P-1) |
| S4 | Instrução do humano, Prompt 11 (GATE 0): EDA, tratamento de outliers, normalização ou padronização, validação cruzada, comparação de modelos, Precision/Recall/F1 macro e weighted; separar o holdout antes de análises que orientem a modelagem | 2026-11-07 |
| S9 | Decisão humana no topo de `docs/status.md`: GATE 3B aprovado; Prompt16/GATE 4A autorizado só com CV no treino; P-4 = `f1_macro`; P-5 = `StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED=42)`; busca = `RandomizedSearchCV` com `n_iter` e seed fixos | 2026-11-07 |
| S10 | Decisão humana no topo de `docs/status.md` (bloco S10): P-14 (texto do Prompt16 anexado em `docs/tasks/TASK-044.md`), P-15 (sem limiar) e P-16 (top 3, desempate dp/tempo) | 2026-11-07 |

## Requisitos

| ID | Requisito | Fonte | Prioridade | Marco |
|---|---|---|---|---|
| REQ-001 | Classificação **multiclasse** que recomenda uma cultura a partir de características de solo e clima | S1 | alta | M3.5 |
| REQ-002 | Dataset: GitHub KrissshSaini/Crop-Recommendation-System, arquivo Crop_recommendation.csv, commit a90b2ed5365bc558baef1ad4e327d2715e53ea2a; sem fallback HF | S5 | alta | M1 |
| REQ-003 | Verificar por execução: quantidade de registros, classes, distribuição, balanceamento, duplicatas, nulos, tipos, outliers | S1 | alta | M1/M2 |
| REQ-004 | Não presumir características do dataset: colunas esperadas são hipótese, validada contra o dado real | S1 | alta | M1 |
| REQ-005 | Fluxo sem leakage: split → fit do pré-processamento no treino → fit do modelo → transform do teste → predict. Nunca `fit` no dataset completo antes do split | S1 | crítica | M3 |
| REQ-006 | Modelos candidatos: DummyClassifier, Logistic Regression, Decision Tree, Random Forest, XGBoost, LightGBM, MLP. Remoção só com justificativa registrada | S1 | alta | M3.5/M4 |
| REQ-007 | Comparar: precision, recall e F1, nas versões macro e weighted | S1 | alta | M3.5 |
| REQ-008 | Interpretação com SHAP, quando aplicável: global, por classe e individual | S1 | média | M4/M5 |
| REQ-009 | Decidir a persistência por ADR, comparando PostgreSQL, SQLite, Parquet, arquivos locais e nenhuma persistência. Não presumir PostgreSQL | S1 | média | M0 |
| REQ-010 | Entrega parcial: notebook executado localmente + síntese de 1–2 páginas; métricas só de CV; baselines Dummy, LogReg, DecisionTree, RandomForest | S2 | crítica | M3.5 |
| REQ-011 | Holdout intocado até a aprovação H4 | S1 (leakage), S2 | crítica | todos |
| REQ-012 | EDA descritiva **só no treino**: distribuições das features, relação feature × classe, correlações | S4 | alta | M2 |
| REQ-013 | Tratamento de outliers: detecção no treino e decisão registrada (manter / limitar / remover) | S4 | alta | M2/M3 |
| REQ-014 | Normalização ou padronização das features, ajustada por fold dentro do `Pipeline` | S4 | alta | M3 |
| REQ-015 | Validação cruzada no treino, com protocolo registrado | S4 | crítica | M3 |
| REQ-016 | Comparação dos modelos com escolha justificada pela métrica principal | S4 | alta | M3.5/M4 |

## Critérios de aceite

| ID | REQ | Critério | Verificação | Resultado esperado |
|---|---|---|---|---|
| AC-REQ001-1 | 001 | O pipeline final prediz, para cada amostra, exatamente uma das classes do alvo observadas no treino | teste de contrato | `set(pred) ⊆ classes_treino` |
| AC-REQ002-1 | 002 | Dado bruto em `data/raw/` com SHA-256, revisão do dataset e data de download registrados | artefato `data/raw/MANIFEST.json` | campos `source`, `revision`, `downloaded_at`, `sha256`, `n_rows` presentes |
| AC-REQ003-1 | 003 | Relatório de qualidade com os 8 itens verificados | artefato `reports/data/quality.json` | chaves `n_rows`, `classes`, `class_distribution`, `balance`, `duplicates`, `nulls`, `dtypes`, `outliers`, todas preenchidas por execução |
| AC-REQ003-2 | 003 | Distribuições das features e outliers calculados só sobre o treino | revisão + artefato | `quality.json` indica `scope: train` nesses itens |
| AC-REQ004-1 | 004 | Validação de schema compara o esperado com o real e reporta as diferenças | teste de contrato + artefato | `schema_diff` em `quality.json` (vazio ou listado) |
| AC-REQ005-1 | 005 | Todo pré-processamento aprendido está dentro de `sklearn.pipeline.Pipeline` avaliado por CV | revisão (reviewer) + teste | nenhum `fit`/`fit_transform` fora de `Pipeline` em `src/` e `notebooks/` |
| AC-REQ006-1 | 006 | Cada candidato foi avaliado ou tem a remoção justificada no EXP | artefato `reports/experiments/EXP-*.md` | 7 modelos com status `avaliado` ou `removido: <justificativa>` |
| AC-REQ007-1 | 007 | As 6 métricas reportadas por modelo, com média ± dp por fold | artefato `reports/metrics/*.json` | `precision_macro`, `recall_macro`, `f1_macro`, `precision_weighted`, `recall_weighted`, `f1_weighted` com `mean`, `std`, `folds` |
| AC-REQ008-1 | 008 | SHAP global, por classe e individual para o modelo escolhido, ou justificativa de não aplicabilidade | artefato `reports/figures/models/shap_*` + EXP | 3 níveis presentes ou justificativa |
| AC-REQ009-1 | 009 | ADR de persistência com as 5 opções comparadas e aceita pelo humano | artefato `docs/adr/ADR-0002-*.md` | `Status: Aceita` |
| AC-REQ010-1 | 010 | Notebook executa do início ao fim localmente | `uv run jupyter nbconvert --to notebook --execute notebooks/00_entrega_parcial.ipynb` | exit 0 |
| AC-REQ010-2 | 010 | Síntese com no máximo 2 páginas, com as seções exigidas | artefato `docs/entrega-parcial/sintese.md` + revisão | 5 seções: problema, EDA, metodologia, primeiro experimento, próximos passos |
| AC-REQ011-1 | 011 | Nenhum acesso ao holdout fora da função de split antes da H4 | `grep -rn holdout src tests notebooks` | ocorrências só na função de split e nos testes de proteção |
| AC-REQ012-1 | 012 | Artefatos de EDA calculados só sobre o treino | artefato `reports/data/eda.json` + revisão | `scope: train` em todos os itens |
| AC-REQ013-1 | 013 | Método, limites e decisão sobre outliers registrados; transformação, se houver, dentro do `Pipeline` | artefato + revisão | seção `outliers` em `eda.json` + decisão no handoff |
| AC-REQ014-1 | 014 | Escalonador declarado por modelo e ajustado por fold | teste unitário de `build_pipeline` + revisão | etapa de escalonamento presente nos modelos que a exigem |
| AC-REQ015-1 | 015 | Protocolo de CV registrado no JSON de métricas | teste de contrato | bloco `cv` com `strategy`, `n_splits`, `shuffle`, `seed` |
| AC-REQ016-1 | 016 | Tabela comparativa candidatos × 6 métricas; métrica principal fixada antes dos resultados | artefato `reports/experiments/EXP-*.md` + revisão | tabela completa; data da escolha da métrica anterior à do experimento |

## Pendências

| ID | Pendência | Bloqueia | Proposta (não decidida) | Decide |
|---|---|---|---|---|
| P-1 | Enunciado oficial do desafio | escopo da entrega final (M5) | — | humano (H1) |
| P-2 | Critérios de avaliação do curso | priorização | — | humano |
| P-3 | Data da entrega final | planejamento do M4/M5 | — | humano |
| P-4 | RESOLVIDA por S9 (2026-11-07): métrica principal = **`f1_macro`**; as 6 métricas continuam reportadas | - | decisão humana explícita no topo de `docs/status.md` | humano (H2) |
| P-5 | RESOLVIDA por S9 (2026-11-07): `StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED=42)` | - | decisão humana explícita no topo de `docs/status.md` | humano (H2) |
| P-6 | RESOLVIDA parcialmente em H2: seed 42, test_size 0.2, split estratificado; CV e metrica principal continuam pendentes | - | decisao humana S5 | humano |
| P-7 | RESOLVIDA: nenhuma exclusao automatica e nenhuma duplicata identica entre particoes; interromper split se houver duplicatas sem agrupamento aprovado/implementado | split quando aplicavel | decisao humana S5 | humano |
| P-8 | Ação se o schema real divergir das colunas esperadas | M1 | parar e reportar o `schema_diff` | humano |
| P-9 | RESOLVIDA: fonte GitHub fixada aprovada; HF401 preservado somente como historico; sem fallback automatico | - | decisao humana S5; mecanismo formalizado pelo arquiteto | humano |
| P-10 | RESOLVIDA por S8: manter todas as 1760 observacoes do treino e as 7 features, sem clipping nem remocao | Politica decidida; entregas ainda exigem verificacao/aceite | decisao humana explicita em docs/status.md, 2026-11-07; TASK-010 nao necessaria | humano com evidencia EDA |
| P-11 | RESOLVIDA por S7: StandardScaler para LogisticRegression e MLP; sem escalonamento para Dummy, DecisionTree, RandomForest, XGBoost e LightGBM; fit por fold | Implementacao/verificacao de REQ-014 NOT_RUN | decisao humana explicita em docs/status.md, 2026-11-07 | humano (H2) |
| P-12 | Classificação obrigatório / opcional / bônus sem o enunciado | priorização | tratar S1/S2/S4 como obrigatórios; nenhum bônus até o enunciado | humano (P-1) |
| P-13 | O "Como verificar" da ADR-0001 e AC-REQ011-1 dizem que `holdout` só aparece "na função de split e nos testes de proteção". O próprio plano exige o termo em mais arquivos (`config.py`, `report.py`, `src/cultivo/evaluation/holdout.py`) | critério da TASK-008 | adotar a lista fechada de `docs/tasks.md` § Convenções como leitura do critério, sem editar a ADR-0001 (Aceita) | humano |
| P-14 | RESOLVIDA por S10 (2026-11-07): texto do Prompt16 anexado em `docs/tasks/TASK-044.md`; Tópicos 1 Contratos, 2 Modelos, 3 Validação cruzada, 4 Métricas, 5 Ajuste, 6 Testes | - | decisão S10 no topo de `docs/status.md` | orchestrator (texto fornecido pelo humano) |
| P-15 | RESOLVIDA por S10 (2026-11-07): sucesso do GATE 4A é metodológico; sem limiar numérico de F1 nem margem obrigatória sobre o Dummy; modelos abaixo do Dummy são reportados, não omitidos | - | decisão humana explícita S10 no topo de `docs/status.md` ("Sem limiar (Recomendado)") | humano |
| P-16 | RESOLVIDA por S10 (2026-11-07): os 3 primeiros por média de `f1_macro` na CV (EXP-001) vão para o `RandomizedSearchCV`; desempate por menor dp e depois menor tempo de treino; Dummy fora da busca. ADR-0012 D7 alinhada a S10 em 2026-11-07 | - | decisão humana explícita S10 no topo de `docs/status.md` ("Top 3, desempate dp/tempo (Recomendado)") | humano |

## Reconciliacao corrente do Prompt15 (TASK-036, 2026-11-07)

S6: pedido humano Prompt15/GATE3B reproduzido em docs/tasks/TASK-036.md; inicio autorizado em docs/status.md apos GATE3A PASS. Complementa S1/S4/S5. A frase historica acima 'sem ... Prompt15' limita S5/Prompt14; o inicio15 agora esta autorizado. Nao concede H4 nem escolhe CV, metrica ou tratamento.

Criterios detalhados e obrigatorios: [aceite Prompt15](../docs/requirements/prompt-15-acceptance.md), topicos1a5, limites e perguntas. REQ-003/004/012: EDA verificavel somente treino; REQ-013: decisao por variavel com plausibilidade/erro, alternativas e consequencias, sem remocao automatica; REQ-005/014: avaliar transformacoes e compor Pipeline compativel, fit aprendido por fold; REQ-011/015: nenhum RAW/HOLDOUT/refazer split/modelo real nesta etapa, protocolo real permanece pendente. As justificativas de nao aplicabilidade nao dispensam analise de cada item obrigatorio.

P-10 permanece PENDENTE para tratamento definitivo: o Prompt15 autoriza detectar, comparar e propor, nao aprova clipping/remocao antecipadamente. P-11 permanece PENDENTE para escolha definitiva por familia; StandardScaler e proposta, nao decisao. P-4/P-5 continuam PENDENTES para experimento real; nao bloqueiam EDA nem testes sinteticos. Perguntas concretas e limites no aceite Prompt15. Nenhum REQ recebe concluido por esta reconciliacao.

## Decisao humana corrente S7 (TASK-041, 2026-11-07)

S7: duas respostas humanas explicitas registradas no topo de docs/status.md: 'Aprovar ADR-0011 (recomendado)' e 'Aprovar escalonamento por familia (recomendado)'. A primeira aceita o contrato do helper independente (registro arquitetural TASK-040); a segunda resolve P-11: StandardScaler para LogisticRegression/MLP e nenhum escalonamento para Dummy, DecisionTree, RandomForest, XGBoost e LightGBM, com fit aprendido por fold. Sao aprovacoes distintas; a ADR aceita isoladamente nao escolheria a familia.

Implementacao e verificacao do helper/pre-processamento continuam NOT_RUN: decisao nao comprova REQ-014 nem GATE3B. Referencias anteriores a P-11 pendente/proposta, inclusive na reconciliacao S6, sao historicas e superadas apenas nesse ponto por S7. P-10 continua pendente apos relatorio EDA; P-4/P-5 pendentes antes do experimento real; H4 nao concedida. Sem novos defaults, treinamento de classificadores reais ou acesso a dados.

## Decisao humana corrente S8 (TASK-042, 2026-11-07)

S8: resposta explicita 'Manter todas as observacoes (recomendado)', registrada no topo de docs/status.md apos apresentacao da EDA. P-10 RESOLVIDA: manter integralmente as1760observacoes do treino para todas as7features, sem clipping nem remocao. Extremos estatisticos nao comprovam erro agronomico. Comparacoes/limites da EDA permanecem descritivos e hipoteticos; nao sao parametros globais deCV nem autorizacao futura de clipping. TASK-010/OutlierClipper nao necessaria nesta politica.

S7/P-11 e aceiteADR11 permanecem validos. Trechos S6/S7 anteriores sobre P-10 pendente retratam o momento anterior e sao superados por S8 nesse ponto. A decisao humana nao presume implementacao, QA, revisao, REQ concluido ou GATE3B PASS; entregas dependem de evidencias/aceite. Estados NOT_RUN do helper em S7 sao historicos e sua execucao corrente deve ser conferida na TASK-038, sem deducao por esta aprovacao. P-4/P-5 continuam pendentes e H4 nao concedida. NenhumCSV deve ser alterado nem EDA repetida por este aceite.

## Decisão humana corrente S9 (TASK-044, 2026-11-07)

S9: resposta explícita "Aprovar e iniciar (Recomendado)", registrada no topo de `docs/status.md`. Aprova o GATE 3B e autoriza o Prompt16/GATE 4A só com CV no treino.
P-4 RESOLVIDA: métrica principal `f1_macro`. P-5 RESOLVIDA: `StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED=42)`.
A busca de hiperparâmetros do Tópico 5 usa `RandomizedSearchCV` com `n_iter` e seed fixos. O espaço de busca é proposto pelo ml-engineer no PLAN_READY.

As menções anteriores a P-4/P-5 pendentes, inclusive a frase "CV e metrica principal continuam pendentes" em P-6 e os trechos S6/S7/S8, retratam o momento anterior e são superadas por S9 só nesse ponto.
O registro formal em ADR (ADR-0012, TASK-045) e o `config.py` (TASK-046) pertencem aos seus donos. Esta decisão não comprova implementação nem conclui nenhum REQ.
H4 não foi concedida. Critérios do experimento e mapeamento para os REQ-005, 006, 007, 010, 011, 014, 015 e 016: [aceite Prompt16](../docs/requirements/prompt-16-acceptance.md). Novas pendências: P-14, P-15 e P-16.

## Decisão humana corrente S10 (TASK-044, 2026-11-07)

S10, no topo de `docs/status.md`: P-14, P-15 e P-16 RESOLVIDAS (texto na tabela de Pendências). A menção "Novas pendências: P-14, P-15 e P-16" na seção S9 retrata o momento anterior e é superada por S10.
A regra D7 da ADR-0012 foi alinhada a P-16 pelo software-architect (TASK-045) em 2026-11-07; a versão anterior (top 2 + 3º condicional) foi substituída. Critérios atualizados: [aceite Prompt16](../docs/requirements/prompt-16-acceptance.md). Esta decisão não comprova implementação nem conclui nenhum REQ. H4 não foi concedida.
