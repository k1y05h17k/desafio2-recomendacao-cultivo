# Visão geral — Recomendação de cultivo (Desafio 2)

> Dono: `business-analyst`. Última atualização: 2026-11-07.
> Requisitos detalhados: `project/requirements.md`. Restrições: `project/constraints.md`.

## Problema

Investigar como sete características registradas de solo e clima se relacionam com a cultura indicada no dataset e estruturar uma tarefa de **classificação multiclasse**. Cada observação tem as entradas `N`, `P`, `K`, `temperature`, `humidity`, `ph` e `rainfall`; a saída pretendida é uma das categorias de `label` observadas no treino.

O público proposto nesta etapa é formado por estudantes e avaliadores do desafio, que precisam compreender e reproduzir a relação entre as medições e os rótulos. A decisão apoiada pelo estudo é quais características e padrões merecem investigação na futura classificação de culturas. A Entrega 1 documenta essa investigação exploratória; ainda não entrega uma decisão automatizada de plantio.

O alcance é reproduzir e analisar os rótulos do dataset de referência. O estudo não demonstra que a classe registrada seja a cultura de maior produtividade ou rentabilidade, nem estabelece recomendação agronômica validada em campo. Unidades, métodos e períodos de medição não confirmados limitam o uso fora dessa base; não se afirma causalidade ou generalização para novas regiões e safras.

## Objetivo

Na Entrega 1, definir o problema, registrar hipóteses exploratórias testáveis, analisar as distribuições e relações entre entradas e culturas e justificar a relevância das variáveis a partir do treino. Os quatro critérios oficiais e seus aceites estão em [rubrica da Entrega 1](../Modulo4_Rubricas_Avaliacao%20%281%29.pdf).

No projeto completo, construir e comparar classificadores por métricas macro e weighted e interpretar o modelo escolhido com SHAP quando aplicável (REQ-001, REQ-007, REQ-008). Essa meta posterior permanece preservada e não é condição adicional de pontuação da Entrega 1.

## Contexto

- Projeto acadêmico de pós-graduação (*projectDataChallenge*, Desafio 2).
- Execução **local** em Jupyter (não Colab).
- Rubrica oficial disponível: [Modulo4_Rubricas_Avaliacao (1).pdf](../Modulo4_Rubricas_Avaliacao%20%281%29.pdf), página 1, seção **Entrega 1 — Parcial (40%)**; extração verificada em registro interno.
- O enunciado completo do desafio e informações não fornecidas pela rubrica permanecem pendentes; esta revisão não presume seu conteúdo.

## Dataset e evidência disponível

- Fonte aprovada: GitHub `KrissshSaini/Crop-Recommendation-System`, arquivo `Crop_recommendation.csv`, commit `a90b2ed5365bc558baef1ad4e327d2715e53ea2a`; ADR-0009 (registro interno) e C-005. A referência antiga ao Hugging Face foi substituída, sem fallback.
- O QA da auditoria (registro interno; resultados no [notebook da Entrega 1](../notebooks/00_entrega_parcial.ipynb) e na [EDA do treino](../reports/data/eda.json)) executou a carga autorizada de **treino**: 1760 observações, sete entradas numéricas e 22 classes, com 80 observações por classe, zero nulos e zero duplicatas. Reproduziu os cálculos descritivos e gerou 16 gráficos. Esses números descrevem apenas o treino verificado; não resultam de nova leitura do bruto ou do holdout.
- O significado documental das colunas e as unidades desconhecidas estão separados das regras técnicas no [notebook da Entrega 1](../notebooks/00_entrega_parcial.ipynb). As faixas observadas não comprovam plausibilidade agronômica.
- Hipóteses de nomes/tipos de colunas são expectativas de schema; não substituem hipóteses de pesquisa sobre a relação solo/clima–cultura. A revisão acadêmica deve declarar quando essas hipóteses de pesquisa foram formuladas, sem atribuir caráter prévio às elaboradas depois da EDA inicial.

## Entregas

| Entrega | Marco | Conteúdo | Prazo | Fonte |
|---|---|---|---|---|
| Entrega 1 — parcial | M3.5 | Quatro critérios oficiais: problema, hipóteses iniciais, EDA/visualizações e variáveis relevantes. Pacote solicitado pelo humano: notebook executado e síntese de 1–2 páginas; resultados descritivos reais, sem inventar experimento ainda não executado. | **2026-11-08** | rubrica oficial; instruções humanas de 2026-11-06 e revisão de 2026-11-07 |
| Entrega final | M5 | **PENDENTE** (P-1) | **PENDENTE** (P-3) | — |

## Escopo

**Nesta adequação da Entrega 1:** contexto do problema, hipóteses específicas com cronologia transparente, interpretação da EDA já verificada no treino, justificativa das sete entradas, notebook executado e síntese. A avaliação usa somente os quatro critérios da rubrica da Entrega 1.

**No projeto completo:** ingestão, verificação de dados, EDA, pré-processamento sem leakage, comparação de modelos por CV, avaliação única no holdout (depois da H4), interpretação com SHAP, notebook e síntese. Os requisitos internos mais amplos continuam em `requirements.md`; não são convertidos em critérios oficiais extras desta auditoria.

**Preservação:** o split existente não é refeito. Bruto e holdout permanecem fechados nesta revisão. Resultados exploratórios vêm exclusivamente do treino; qualquer métrica preditiva futura, até H4, deve vir somente de CV no treino.

**Fora** (até haver requisito): API, interface web, deploy, banco de dados servidor (ver ADR-0002),
coleta de dados novos, tuning no holdout.

## Glossário

| Termo | Significado aqui |
|---|---|
| Holdout | conjunto de teste separado uma única vez no split; intocado até a H4 |
| CV | validação cruzada aplicada **somente** ao conjunto de treino |
| Macro | média das métricas por classe, com peso igual para cada classe |
| Weighted | média das métricas por classe, ponderada pelo suporte (nº de amostras) de cada classe |
| Marco (M0–M5) / Gate (G0–G6) | etapa do projeto / etapa do ciclo de uma TASK (ver `.claude/workflows/gates.md`) |
