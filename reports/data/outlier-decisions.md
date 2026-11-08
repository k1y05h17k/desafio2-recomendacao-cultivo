# Politica atual de outliers - decisao humana S8

2026-11-07: P-10 resolvida pelo humano: **manter integralmente as 1760 observacoes do treino**, sem clipping nem remocao para todas as sete features.

Treino vinculado pelo SHA256: e71eea516bec613930e37551cc20b71a75d68ffe7c548fb979d6ae6557e61fdf.
Registro autoritativo: [outlier-policy.json](outlier-policy.json). Fonte humana S8: [docs/status.md](../../docs/status.md).

| Feature | Decisao S8 | Justificativa e consequencias hipoteticas |
|---|---|---|
| N | Manter sem clipping/remocao | Nenhum candidato IQR observado; nao ha tratamento indicado pelo detector. S8 aprova preservar todas as 1760 observacoes. |
| P | Manter sem clipping/remocao | 108 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1652 registros e 22 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |
| K | Manter sem clipping/remocao | 160 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1600 registros e 20 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |
| temperature | Manter sem clipping/remocao | 72 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1688 registros e 22 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |
| humidity | Manter sem clipping/remocao | 24 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1736 registros e 22 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |
| ph | Manter sem clipping/remocao | 43 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1717 registros e 22 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |
| rainfall | Manter sem clipping/remocao | 82 candidatos estatisticos nao comprovam erro agronomico; unidades nao confirmadas. Remocao hipotetica deixaria 1678 registros e 22 classes; clipping altera valores sem erro de medicao demonstrado. S8 aprova preservar todas as 1760 observacoes. |

Comparacoes e limites continuam em [outliers.json](outliers.json), por feature, e em [eda.json](eda.json). Sao evidencia descritiva; nenhum calculo foi alterado por este registro.
Futuros run_eda geram ciencia e propostas descritivas; nao alteram nem revogam a politica humana separada outlier-policy.json. Mudanca da politica exige nova decisao humana.
Nao criar OutlierClipper/TASK-010 nesta politica. Limites de EDA nao viram parametros globais de CV.

---

## Snapshot historico de propostas, anterior ao aceite S8

As mencoes a P-10 pendente abaixo pertencem ao snapshot anterior; a decisao atual esta acima.

# Propostas de outliers somente no treino

P-10 pendente: nenhuma alternativa abaixo esta aprovada ou aplicada.
Extremo estatistico nao demonstra erro agronomico; unidades nao confirmadas.

| Feature | Candidatos IQR1.5 | Proposta | Evidencia |
|---|---:|---|---|
| N | 0 | Manter ate decisao P-10 | outliers.json/features/N; ../figures/eda/N-distribution.png |
| P | 108 | Manter ate decisao P-10 | outliers.json/features/P; ../figures/eda/P-distribution.png |
| K | 160 | Manter ate decisao P-10 | outliers.json/features/K; ../figures/eda/K-distribution.png |
| temperature | 72 | Manter ate decisao P-10 | outliers.json/features/temperature; ../figures/eda/temperature-distribution.png |
| humidity | 24 | Manter ate decisao P-10 | outliers.json/features/humidity; ../figures/eda/humidity-distribution.png |
| ph | 43 | Manter ate decisao P-10 | outliers.json/features/ph; ../figures/eda/ph-distribution.png |
| rainfall | 82 | Manter ate decisao P-10 | outliers.json/features/rainfall; ../figures/eda/rainfall-distribution.png |

Limites estritos e interpolacao linear detalhados em outliers.json.
Comparacoes manter/clipping/remover sao hipoteticas; preservam dados em disco.
Nenhum limite desta EDA e parametro pre-ajustado para CV.
