# Experimentos

## EXP-001 — baseline-mlp-v1

- Ambiente/dataset: `v0.1`, `insurance_trajectories.parquet` (120.000 transições)
- Dados de treino: exclusivamente o dataset público; nenhum campo oracle/latente é aceito.
- Split: clientes inteiros, 70% treino / 15% validação / 15% teste.
- Seed: 42
- Configuração executada: MLP com duas camadas ocultas de 64 unidades, Adam (`1e-3`), batch 1024, 2 épocas.

### Resultado no teste isolado

| Métrica | Valor |
| --- | ---: |
| RMSE do próximo estado (agregado) | 6,8063 |
| Acurácia da jornada | 86,96% |
| MAE do reward | 2,8446 |
| RMSE do reward | 5,3136 |
| MAE do premium mensal | 11,8842 |
| MAE do engagement digital | 0,0400 |

Os artefatos reprodutíveis estão em `artifacts/exp-001/`: checkpoint PyTorch, pré-processadores, banco local MLflow, metadados da execução e métricas de teste. Esse resultado é uma referência de baseline; a próxima implementação deverá compará-lo com a arquitetura de World Model propriamente dita.

## EXP-002 — world-model-v1

- Arquitetura: encoder de estado + encoder de ação + dinâmica no espaço latente + decoders de próximo estado/jornada e reward head.
- Dados, split, seed e restrição de dados oracle: idênticos ao EXP-001.
- Configuração executada: 2 épocas, batch 1024, Adam (`1e-3`).

### Resultado no teste isolado

- RMSE do próximo estado: `8,0709`
- Acurácia da jornada: `85,39%`
- MAE do reward: `2,9773`
- RMSE do reward: `5,3913`

Neste primeiro ensaio, o World Model v1 ficou abaixo do baseline (`86,96%` de acurácia da jornada e `2,8446` de MAE do reward). Esse é um resultado científico válido: a arquitetura foi implementada e medida, mas **ainda não satisfaz o critério de superar o baseline**. O próximo experimento dentro do Sprint 4 deve ajustar épocas, dimensão latente e pesos de perda antes de qualquer avanço para simulação multi-step.

## EXP-003 — otimização controlada

Foram triados quatro candidatos por quatro épocas, sempre com o mesmo dataset público, split por cliente e seed. A seleção usou ranking separado — e de mesmo peso — de acurácia de jornada, MAE de reward e RMSE de próximo estado na validação. Isso evita somar métricas de unidades incompatíveis.

O candidato confirmado foi `latent64-equal` (dimensão latente 64 e pesos de perda 1:1:1), retreinado por oito épocas. No teste isolado, ele alcançou 91,08% de acurácia da jornada e RMSE de próximo estado de 6,7401: melhorias contra o baseline de 4,12 pontos percentuais e 0,0662, respectivamente. Porém, o MAE de reward foi 3,0878, pior que os 2,8446 do baseline.

**Decisão:** o World Model v1 é melhor para a dinâmica de estado e jornada, mas não substitui o baseline para reward. A próxima otimização deve focar reward (normalização/transformação do alvo, scheduler de learning rate e pesos de perda), preservando a avaliação separada no teste. O relatório completo está em `artifacts/exp-003/optimization_report.json`.

## EXP-004 — dinâmica residual e Huber Loss

Configuração: dimensão latente 64, conexão residual do estado atual para a predição numérica, Huber Loss para reward com peso 1,25 e scheduler `StepLR` (redução do learning rate pela metade após quatro épocas). Foram usadas oito épocas, o dataset público v0.1, seed 42 e o mesmo split por cliente.

No teste isolado, o modelo obteve:

- Acurácia da jornada: `91,07%` — superior ao baseline (`86,96%`).
- RMSE do próximo estado: `6,5951` — superior ao baseline (`6,8063`).
- MAE do reward: `2,8223` — superior ao baseline (`2,8446`).
- RMSE do reward: `5,8406` — inferior ao baseline (`5,3136`).

**Decisão:** EXP-004 passa a ser o melhor World Model v1 para os erros típicos de reward, estado e jornada. O RMSE de reward indica que continuam existindo erros grandes e raros; isso deve ser investigado antes de afirmar robustez econômica em eventos extremos. Os artefatos estão em `artifacts/exp-004/`.

## EXP-005 — World Model multi-task com eventos

Além das cabeças de próximo estado, jornada e reward, este experimento adiciona heads auxiliares de compra e cancelamento. Os dois indicadores são resultados pós-ação e entram somente na perda; eles não são inputs do modelo. A configuração preserva o EXP-004 e adiciona pesos `0,5` para compra e `0,5` para cancelamento.

Resultado no teste isolado:

- MAE do reward: `2,4142` — melhor resultado até agora; baseline: `2,8446`; EXP-004: `2,8223`.
- RMSE do reward: `5,5524` — ainda acima do baseline (`5,3136`), mas melhor que EXP-004 (`5,8406`).
- RMSE do próximo estado: `6,5958` — praticamente igual ao EXP-004.
- Acurácia da jornada: `90,88%` — acima do baseline (`86,96%`).
- Compra: acurácia `91,62%`, Brier Score `0,0534`, taxa observada `15,14%`.
- Cancelamento: acurácia `99,39%`, Brier Score `0,0048`, taxa observada `0,65%`.

**Decisão:** EXP-005 é o melhor candidato para MAE de reward e mantém ganhos na jornada/estado. A acurácia de cancelamento não deve ser interpretada isoladamente, porque o evento é raro; o Brier Score e, em uma próxima rodada, métricas de precisão/recall são mais informativos. O principal ponto de pesquisa restante é reduzir o RMSE de reward nos impactos econômicos extremos.

**Modelo selecionado:** EXP-005 é a referência do projeto para o Sprint 5, mantendo a ressalva explícita sobre o RMSE de reward em eventos extremos.
