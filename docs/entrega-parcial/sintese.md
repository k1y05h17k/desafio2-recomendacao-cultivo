# Entrega 1 — síntese acadêmica

2026-11-07 · Recomendação de cultivo inteligente · Escopo: problema, hipóteses, EDA e variáveis relevantes. Fonte dos números: [EDA do treino](../../reports/data/eda.json). Material completo: [notebook](../../notebooks/00_entrega_parcial.ipynb).

## Problema e objetivo

Investigar como sete medidas de solo/clima (`N`, `P`, `K`, `temperature`, `humidity`, `ph`, `rainfall`) diferenciam as culturas registradas em `label`, preparando uma classificação multiclasse. O público proposto são estudantes e analistas que avaliam um protótipo de triagem de culturas: a decisão nesta parcial é quais padrões e variáveis investigar. A análise descreve os rótulos do dataset; não comprova adequação agronômica, produtividade, rentabilidade ou generalização para outras regiões/safras. Não fornece prescrição de plantio ou adubação.

## Dados e metodologia

A fonte aprovada é o CSV GitHub `KrissshSaini/Crop-Recommendation-System`, commit `a90b2ed5365bc558baef1ad4e327d2715e53ea2a`. O treino verificado contém 1760 observações, sete entradas, 22 classes e 80 registros por classe, sem nulos ou duplicatas. Esse balanceamento descreve a amostra e não a população agrícola. Unidades, períodos e métodos de medição não estão confirmados; os números abaixo permanecem na escala original.

A EDA usa apenas o treino: descritivas, histogramas, boxplots por classe, correlação de Pearson e extremos por IQR de 1,5. O notebook exibe 16 gráficos e os agregados preparados pelo código; não recalcula ciência nem ajusta modelos. A política humana S8 conserva todas as observações, sem clipping/remoção. Extremos estatísticos não foram considerados erros agronômicos. O holdout não foi consultado, e o split não foi repetido.

## Hipóteses exploratórias e resultados preliminares

As hipóteses foram formuladas **nesta revisão, após a EDA inicial**. Organizam a investigação e são checadas descritivamente nos mesmos dados; não são pré-registradas, testes de significância ou confirmação independente. Em cada contraste, a ordem das medianas ou o sinal de Pearson é a regra verificável.

| Hipótese | Resultado no treino |
|---|---|
| H1: mediana de `N` em `cotton` > `orange`. | 115,00 > 19,00; sustentada descritivamente. |
| H2: mediana de `humidity` em `chickpea` < `rice`. | 16,64 < 82,16; sustentada descritivamente. |
| H3: mediana de `rainfall` em `rice` > `maize`. | 233,42 > 84,23; sustentada descritivamente. |
| H4: correlação linear P–K positiva. | Pearson = 0,7360; sustentada descritivamente, sem demonstrar equivalência. |

## Variáveis relevantes e interpretação

Cada entrada permanece candidata por apresentar contrastes entre culturas; a relevância é exploratória, sem ranking de importância preditiva. As mesmas visualizações mostram sobreposição entre outras classes.

| Variável | Justificativa e limite observado |
|---|---|
| `N` | Contraste de H1; `rice` e `maize` têm medianas 80 e 76, com intervalos centrais sobrepostos. |
| `P` | Mediana 137 em `apple`, frente a 16 em `orange`; `apple` e `grapes` se sobrepõem. |
| `K` | Mediana 200 em `apple`, frente a 19,50 em `maize`; `apple`/`grapes` têm o mesmo Q1–Q3, 197–203. |
| `temperature` | Medianas 18,89 em `chickpea` e 28,89 em `muskmelon`; `rice`/`cotton` têm intervalos centrais sobrepostos. |
| `humidity` | Contraste de H2; `apple`/`orange` têm medianas próximas, 92,33 e 91,96, e sobreposição. |
| `ph` | Medianas 5,75 em `kidneybeans` e 7,36 em `chickpea`; `apple`/`grapes` se sobrepõem. |
| `rainfall` | Contraste de H3, com faixas observadas disjuntas; `apple`/`orange` têm intervalos centrais sobrepostos. |

Os histogramas mostram amplitudes e assimetrias distintas. Os boxplots localizam padrões de grupos: há 160 candidatos globais IQR em `K`, mas seus valores altos também caracterizam culturas específicas. A correlação P–K indica informação compartilhada, sem justificar exclusão automática. Nenhuma entrada demonstrou separar todas as classes; `label` é o alvo e fica fora das features. Associação não comprova causalidade nem necessidade de insumos.

## Conclusão e próximos passos

A parcial entrega problema delimitado, hipóteses verificáveis, visualizações interpretadas e justificativas das sete variáveis. O [EXP-001](../../reports/experiments/EXP-001.md) comparou sete modelos por validação cruzada somente nos dados de treino, em cinco folds estratificados e embaralhados (seed 42), com transformações ajustadas por fold. O F1 macro (média ± desvio-padrão entre folds) foi de 0,0040 ± 0,0000 para o baseline Dummy, 0,9686 ± 0,0090 para a regressão logística e 0,9948 ± 0,0052 para a Random Forest. Confirmar unidades/origem e validar uso agronômico continuam necessários antes de aplicação real. O holdout permanece condicionado à H4.
