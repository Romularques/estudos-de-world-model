# Como implementar e calibrar o World Model v1

## Objetivo metodológico

O **World Model v1** é a primeira versão operacional de um modelo que aprende a dinâmica do ambiente de seguros. Seu objetivo é prever como o estado de um cliente evolui após uma ação da seguradora, além dos resultados associados a essa transição.

O problema é representado por:

```text
[S_t, A_t, C_t] → [S_t+1, R_t]
```

Onde:

```text
S_t     estado observável do cliente no instante t;
A_t     ação comercial ou operacional aplicada no instante t;
C_t     contexto temporal conhecido, como mês e proximidade de renovação;
S_t+1   próximo estado esperado do cliente;
R_t     resultado econômico e comportamental da transição.
```

O objetivo não é apenas obter boas métricas em uma linha isolada do dataset. O modelo deve reproduzir de modo útil a relação entre **estado, ação e consequência**, permitindo posteriormente simular cenários como ofertas diferentes, descontos, canais ou contatos de corretor.

O World Model v1 deve ser comparado com o baseline MLP. A passagem de baseline para World Model só é justificada se houver ganho mensurável, estável e relevante na previsão das transições ou na qualidade das trajetórias simuladas.

## 1. Escopo do World Model v1

O baseline MLP trata cada transição como uma previsão direta. O World Model v1 amplia essa visão ao introduzir uma representação latente aprendida do estado e uma função explícita de dinâmica condicionada pela ação. Nesta primeira implementação, ainda não há codificador sequencial: o modelo opera uma transição por vez. Memória de múltiplos passos e incerteza explícita ficam como extensões futuras, que deverão ser justificadas por evidência experimental.

O escopo inicial recomendado é:

- Receber o estado observável e a ação atuais do cliente.
- Produzir previsões do próximo estado, compra, cancelamento, jornada e reward.
- Preservar o uso exclusivo das variáveis observáveis no treino padrão.
- Usar o Oracle apenas para diagnóstico científico e análise de limitações.
- Simular uma etapa à frente com qualidade antes de avaliar simulações de múltiplas etapas.

Na implementação atual, a formulação é:

```text
[S_t, A_t, C_t] → [S_t+1, R_t]
```

Uma versão futura poderá usar uma janela histórica `k`, permitindo diferenciar clientes com o mesmo estado atual aparente, mas histórias recentes diferentes. Essa extensão só deve ser adotada após comparação justa com a arquitetura atual.

## 2. Arquitetura inicial e racional

O World Model v1 implementado usa uma arquitetura de **encoder, dinâmica e decoder**, em PyTorch:

```text
estado observável S_t
        ↓
state_encoder → estado latente z_t
        ↓
ação A_t → action_encoder
        ↓
concatenação [z_t, ação latente] → dynamics
        ↓
próximo estado latente z_t+1
        ↓
numeric_decoder, journey_decoder e reward_head
```

As cabeças podem ter funções distintas:

```text
regressão:
    próximo prêmio, engajamento, sinistros e reward.

classificação binária:
    contratação, cancelamento e posse de produto.

classificação multiclasse:
    próximo estágio da jornada.
```

O objetivo da representação latente não é revelar diretamente os valores do Oracle. Ela deve resumir, a partir do estado observável, informações úteis para prever comportamento futuro. As variáveis `trust`, `insurance_affinity` e `price_sensitivity` do simulador continuam proibidas como entradas de treino.

## 2.1. Exemplos dos experimentos realizados

Os experimentos reais registrados no projeto confirmam que o tamanho do estado latente é um hiperparâmetro relevante. O **EXP-002** treinou o World Model v1 com `latent_dim=32`, `hidden_dim=64`, seed `42`, dataset de 120.000 transições e oito épocas.

O **EXP-003** aplicou uma busca controlada. Todos os candidatos foram avaliados com a mesma versão do dataset, a mesma seed e quatro épocas de triagem. A seleção combinou, com o mesmo peso por ranking, três métricas de validação: acurácia da jornada — maior é melhor —, MAE de reward e RMSE do próximo estado — menores são melhores.

```text
candidato              dimensão latente    pesos (estado, jornada, reward)
control-l32-equal      32                  (1, 1, 1)
latent64-equal         64                  (1, 1, 1)
latent64-state2        64                  (2, 1, 1)
latent64-reward2       64                  (1, 1, 2)
```

Os resultados de validação da triagem foram:

```text
candidato              jornada     MAE reward    RMSE próximo estado
control-l32-equal      0,88917     3,12205       6,67056
latent64-equal         0,90089     3,01284       6,83579
latent64-state2        0,88872     2,95190       6,60949
latent64-reward2       0,88917     2,88238       6,89424
```

O candidato `latent64-equal` venceu a triagem pelo critério definido antes do teste final. Ele foi então treinado por oito épocas e avaliado uma única vez no conjunto de teste. Obteve acurácia de jornada de `0,91083`, MAE de reward de `3,08781` e RMSE de próximo estado de `6,74015`.

Comparado ao baseline MLP, o vencedor melhorou a acurácia de jornada de `0,86961` para `0,91083` e reduziu o RMSE do próximo estado de `6,80631` para `6,74015`. Porém, piorou o MAE de reward de `2,84465` para `3,08781`. A conclusão registrada é correta e deve ser preservada: **o World Model v1 ainda não substitui integralmente o baseline**; ele é melhor para jornada e estado, mas ainda não para o resultado econômico.

Esses exemplos mostram por que ajustar a dimensão latente não é uma escolha estética. Uma dimensão de 32 pode restringir a capacidade de representar relações entre estado e ação; uma dimensão de 64 pode melhorar algumas saídas, mas também elevar o risco de capacidade excessiva ou deslocar o equilíbrio entre objetivos. A escolha deve ser feita por protocolo de validação, não pela métrica de teste isolada.

## 3. Preparação das transições e prevenção de vazamento

Cada cliente deve ter seus eventos ordenados por tempo. No v1, a entrada é a transição atual e a saída é sempre o período futuro seguinte. Em uma extensão sequencial, as janelas de entrada deverão ser construídas apenas com períodos anteriores ou com o período atual.

```text
v1:       [S_t, A_t, C_t]
alvo:     [S_t+1, R_t]

extensão sequencial futura:
entrada:  meses t-5 até t
alvo:     mês t+1
```

O cuidado principal é evitar vazamento temporal. Não podem entrar na transição ou futura janela variáveis geradas depois da ação analisada, nem transformações calculadas com estatísticas do futuro. Normalizadores, codificadores e imputadores devem ser ajustados somente sobre o conjunto de treino.

Também é necessário definir como lidar com o início de uma trajetória. As opções devem ser documentadas: descartar janelas incompletas, aplicar preenchimento com máscara ou usar uma sequência de tamanho variável. A estratégia escolhida deve ser a mesma em treino, validação e inferência.

## 4. Separação temporal e sazonalidade

A avaliação precisa representar o uso futuro do modelo. A separação aleatória de linhas não é apropriada para esse objetivo.

Em um cenário real com múltiplos anos, a divisão deve usar blocos temporais completos:

```text
Treino:     anos históricos iniciais
Validação:  período posterior usado para calibragem
Teste:      período futuro mantido intocado
```

Para testar estabilidade, recomenda-se validação de origem móvel:

```text
treina até 2022 → valida 2023;
treina até 2023 → valida 2024;
treina até 2024 → testa 2025.
```

Mês, trimestre, renovação, vencimento, feriados e campanhas conhecidas devem integrar o contexto quando forem disponíveis no instante da decisão. O modelo deve aprender sazonalidade por observações históricas, não por acesso a informação futura.

O ambiente sintético atual ainda não tem múltiplos ciclos anuais. Essa limitação deve aparecer no relatório de resultados: as métricas atuais validam a dinâmica criada, mas não comprovam robustez sazonal.

## 5. Função de perda e previsão probabilística

Como o World Model prevê diversos tipos de alvo, a perda total deve combinar termos específicos:

```text
L_total =
    w_estado_numérico × L_regressão
  + w_eventos_binários × L_binária
  + w_jornada × L_multiclasse
  + w_reward × L_reward
```

Os pesos `w` são hiperparâmetros e devem ser registrados. Sem esse controle, uma saída frequente ou em grande escala pode dominar o treinamento e esconder mau desempenho em eventos importantes, como cancelamento.

Quando o objetivo for simular trajetórias, o modelo deve evoluir além de previsões pontuais. Uma mesma ação pode produzir futuros diferentes para clientes semelhantes. O v1 pode começar por probabilidades calibradas para eventos binários e distribuições simples para saídas numéricas, como média e variância. Versões posteriores podem explorar modelos de mistura, quantis ou variáveis latentes probabilísticas.

## 6. Protocolo de comparação com o baseline

Comparações de experimentos devem ser justas. O World Model v1 e o baseline precisam usar a mesma versão do dataset, as mesmas variáveis observáveis, a mesma divisão temporal e o mesmo conjunto de métricas.

Cada experimento deve registrar:

```text
identificador do experimento;
versão do ambiente e do dataset;
período de treino, validação e teste;
seed ou conjunto de seeds;
lista de entradas e alvos;
transformações de dados;
arquitetura e hiperparâmetros;
checkpoint selecionado;
métricas por saída, segmento e horizonte;
artefatos de avaliação.
```

Boas práticas de comparação incluem:

- Alterar uma hipótese relevante por vez, como arquitetura, janela histórica ou peso de perda.
- Repetir o mesmo experimento com múltiplas seeds e comparar média e dispersão das métricas.
- Não ajustar hiperparâmetros olhando o conjunto de teste.
- Fixar o orçamento de treino quando a comparação buscar eficiência, por exemplo número de épocas, passos ou parâmetros.
- Informar custo computacional, tempo de treino e tamanho do modelo.
- Comparar erros absolutos e ganhos relativos, não somente uma métrica agregada.
- Avaliar segmentos, ações, produtos, canais e eventos raros separadamente.
- Manter um experimento de controle que reproduza o baseline publicado.
- Salvar predições e não apenas métricas, permitindo auditoria posterior.

O MLflow deve concentrar os parâmetros, métricas, gráficos, *checkpoints* e referências da versão de dados. O resultado deve ser rastreável do relatório até a execução que o produziu.

## 7. Como calibrar o modelo para superar o baseline

Superar o baseline não deve significar escolher o maior modelo disponível. A calibragem deve seguir um ciclo disciplinado:

```text
medir o baseline
        ↓
identificar erros estruturais
        ↓
formular uma hipótese de melhoria
        ↓
alterar uma variável relevante
        ↓
validar no período de validação
        ↓
confirmar uma única vez no teste final
```

Exemplos de hipóteses de melhoria:

- Se o erro aumenta para clientes com eventos recentes, testar uma janela histórica maior.
- Se compra e cancelamento têm baixa qualidade, ajustar pesos de classe, calibração ou representação de ação.
- Se o modelo erra após mudanças de preço, revisar a codificação de preço, desconto e produto.
- Se há degradação em meses específicos, acrescentar contexto de calendário e expandir o histórico para ciclos completos.
- Se o modelo reproduz médias, mas falha em trajetórias, aumentar a ênfase em métricas de rollout e em previsão probabilística.

Hiperparâmetros a explorar de forma controlada incluem tamanho da janela, dimensão oculta, número de camadas, dropout, taxa de aprendizado, *weight decay*, tamanho do lote, pesos das perdas e estratégia de *early stopping*.

Uma melhoria deve ser aceita quando for consistente em múltiplas seeds, aparecer na validação e manter-se no teste final. Ganhos muito pequenos, instáveis ou limitados a uma métrica devem ser tratados como inconclusivos.

## 8. Métricas de uma etapa e de múltiplas etapas

O primeiro marco é a previsão de uma etapa:

```text
S_t + A_t → S_t+1 + R_t
```

Para isso, devem ser avaliados MAE, RMSE e viés para variáveis numéricas; acurácia, precisão, revocação e calibração para eventos; e matriz de confusão para a jornada.

O segundo marco é o *rollout*: usar a saída prevista como parte da entrada do passo seguinte para simular vários meses. Esse teste é mais difícil porque pequenos erros se acumulam.

Em rollouts, devem ser comparados com o ground truth:

- distribuição de produtos ativos;
- conversão e cancelamento por período;
- evolução de prêmio, engajamento e jornada;
- distribuição e média do reward;
- estabilidade e plausibilidade de trajetórias.

O modelo deve ser julgado tanto pela precisão local quanto pela coerência global da população simulada.

## 9. Critérios de sucesso e resultados esperados

Ao final do World Model v1, são esperados:

- Pipeline de construção de sequências reproduzível e testado.
- Treino do baseline e do World Model com protocolo comparável.
- Registro completo dos experimentos em MLflow.
- Métricas por saída, por segmento e por horizonte temporal.
- Relatório de ganhos e perdas em relação ao baseline.
- Análise de estabilidade entre seeds e períodos.
- Avaliação de rollout de múltiplas etapas contra o ground truth.
- Diagnóstico com o Oracle, sem usar suas variáveis latentes como entrada de treino.
- Documentação de limitações e próximos experimentos recomendados.

O sucesso não é definido por uma métrica isolada. O v1 deve demonstrar melhora relevante, estável e auditável sobre o baseline, especialmente em situações em que a memória histórica é teoricamente útil. Se isso não ocorrer, o resultado ainda é valioso: indica que o estado agregado atual já captura a maior parte da dinâmica ou que a qualidade e extensão das sequências precisam ser melhoradas antes de aumentar a complexidade do modelo.

## Síntese

O World Model v1 transforma previsões de transição isoladas em uma representação temporal do comportamento do cliente. Seu propósito é aprender como decisões comerciais interagem com histórico, contexto e incerteza para produzir estados futuros e resultados econômicos.

O avanço científico depende de disciplina experimental: dados temporais bem separados, comparações justas, múltiplas seeds, métricas locais e de rollout, rastreabilidade completa e aceitação de ganhos apenas quando forem estáveis. Dessa forma, superar o baseline deixa de ser uma busca por uma métrica maior e passa a ser evidência de que o modelo aprendeu dinâmica adicional relevante.
