# Benchmark de latence — ibm-hr-attrition, modèle v7

1000 appels par backend, après 10 appels de chauffe · x86_64 · Python 3.12.14

Charge au moment de la mesure : 4 CPU logiques · load average 1/5/15 min : 2.08 / 3.39 / 3.01 · mémoire disponible 3369 Mio · 5 conteneurs Docker actifs (dont le cluster kind)

| Backend | P50 (ms) | P95 (ms) | P99 (ms) |
|---|---|---|---|
| sklearn_pipeline | 11.473 | 16.517 | 20.323 |
| onnx_python | 0.227 | 0.567 | 0.931 |
| onnx_batch_100 | 0.662 | 1.200 | 1.518 |

Accélération ONNX vs scikit-learn (P50, 1 ligne) : x50.4
