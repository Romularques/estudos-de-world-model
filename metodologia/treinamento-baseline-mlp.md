# Como treinar e avaliar um baseline MLP para o Insurance World Model

## Objetivo metodológico

A Fase 2 inicia o aprendizado da dinâmica criada na Fase 1. O primeiro modelo será um **baseline MLP** (*Multi-Layer Perceptron*): uma rede neural de camadas densas que recebe o estado atual de um cliente e uma ação da seguradora para prever o estado seguinte e seus resultados.

O problema é representado por:

```text
[S_t, A_t, C_t] → [S_t+1, R_t]
```

Onde `S_t` é o estado observável atual, `A_t` é a ação, `C_t` é o contexto temporal conhecido, `S_t+1` é o próximo estado e `R_t` representa resultados como reward, compra ou cancelamento.

O objetivo não é construir imediatamente o World Model mais sofisticado. O MLP estabelece uma referência clara, reproduzível e auditável para responder: **um modelo neural simples consegue aprender parte relevante da dinâmica sintética?** Se um modelo futuro não o superar de modo consistente, sua maior complexidade não estará justificada.

## 1. Definir o contrato de entrada e saída

O dataset da Fase 1 registra transições no formato:

```text
state_... + action_... → next_state_... + reward
```

As entradas devem conter apenas informações disponíveis no instante da decisão:

```text
estado atual:
    age, tenure_months, políticas ativas, claims_12m;
    premium_monthly, digital_engagement e journey_stage.

ação:
    action_type, action_product, action_price;
    action_channel e action_discount.
```

Os alvos representam o que ocorre depois da ação:

```text
próximo estado numérico:
    prêmio, engajamento, sinistros e tempo de relacionamento.

próximo estado categórico ou binário:
    políticas ativas e estágio da jornada.

resultados:
    reward, purchased e cancelled.
```

As variáveis latentes do Oracle — `trust`, `insurance_affinity` e `price_sensitivity` — não entram no treino padrão. Elas permanecem como referência científica para diagnósticos de erro e avaliação da hipótese do projeto.

## 2. Incluir contexto temporal e sazonalidade

Separar treino e teste no tempo não significa ignorar sazonalidade. Significa usar apenas o passado para prever o futuro. Em dados reais, o contexto disponível no momento da decisão deve incluir, quando relevante:

- mês do ano e trimestre;
- proximidade da renovação e do vencimento;
- feriados e campanhas comerciais conhecidos;
- indicadores externos aprovados para uso.

O dataset sintético atual contém apenas 12 meses e não possui sazonalidade anual explícita. Portanto, ele permite validar o pipeline, mas não uma avaliação sazonal robusta. Essa avaliação exigirá trajetórias de múltiplos anos, para que o modelo observe mais de um ciclo completo antes de prever o mesmo período em um ano futuro.

## 3. Preparar as variáveis para a rede neural

Uma MLP recebe números em escalas comparáveis. O dataset tabular precisa ser convertido em uma matriz de entrada e em conjuntos de alvos.

Variáveis numéricas, como idade, prêmio e engajamento, devem ser normalizadas com parâmetros calculados exclusivamente sobre o conjunto de treinamento. Variáveis categóricas, como estágio da jornada, tipo de ação, produto e canal, devem ser codificadas inicialmente por *one-hot encoding*. Booleanos devem ser convertidos explicitamente para `0` e `1`.

Valores ausentes precisam ser tratados e registrados antes do treinamento; nunca devem ser silenciosamente convertidos em zero sem justificativa.

```text
colunas selecionadas
        ↓
codificação de categorias e booleanos
        ↓
normalização de variáveis numéricas
        ↓
matriz X_t e alvos Y_t
```

## 4. Separar treino, validação e teste

A divisão deve respeitar o tempo. Em dados reais com histórico de vários anos, uma estrutura recomendada é:

```text
Treino:     anos iniciais completos
Validação:  ano seguinte
Teste:      ano futuro, mantido intocado até a decisão final
```

Também deve ser usada validação com janelas móveis:

```text
treina até 2022 → valida 2023;
treina até 2023 → valida 2024;
treina até 2024 → testa 2025.
```

Essa estratégia preserva causalidade temporal e permite verificar estabilidade em diferentes ciclos. Para a base sintética atual, a divisão será uma validação de conceito e suas limitações sazonais deverão ser reportadas.

## 5. Construir o baseline MLP

O baseline será implementado com PyTorch e uma arquitetura pequena, deliberadamente simples:

```text
vetor de entrada
    ↓
Linear → ReLU → Dropout
    ↓
Linear → ReLU
    ↓
cabeças de saída especializadas
```

As cabeças permitem compartilhar uma representação do cliente e usar a função adequada para cada tipo de previsão:

```text
regressão:
    prêmio, engajamento, sinistros e reward.

classificação binária:
    contratação, cancelamento e posse de produto.

classificação multiclasse:
    próximo estágio da jornada.
```

O racional é aprender tarefas relacionadas em conjunto. A compra, por exemplo, está ligada à mudança de produto, prêmio, jornada e reward. O tamanho da rede, *dropout*, taxa de aprendizado, lote e épocas devem ser hiperparâmetros rastreados, e não escolhas ocultas no código.

## 6. Definir funções de perda e treinamento

Cada saída usa uma perda compatível:

```text
saídas numéricas:       MSE ou MAE;
saídas binárias:        entropia cruzada binária;
saída multiclasse:      entropia cruzada multiclasse.
```

A perda total combina as perdas das cabeças com pesos documentados. Isso é necessário porque alvos com escalas ou frequências diferentes podem dominar o treinamento. Eventos raros, como cancelamento, podem requerer ponderação de classe e métricas específicas.

O treino usa minibatches e AdamW. A validação seleciona hiperparâmetros, permite *early stopping* e escolhe o melhor *checkpoint*. O teste só é consultado após todas as decisões de modelagem.

## 7. Medir a qualidade do baseline

Não existe uma métrica única para transições de estado. A avaliação deve separar cada tipo de saída:

- Para variáveis numéricas: MAE, RMSE e viés médio.
- Para compra e cancelamento: precisão, revocação, AUC quando aplicável e calibração de probabilidade.
- Para jornada: acurácia, matriz de confusão e métricas por classe.

Além das métricas por linha, devem ser comparadas propriedades agregadas das trajetórias:

- Distribuição de produtos prevista versus ground truth.
- Conversão e cancelamento por mês, ação, produto e canal.
- Evolução média de engajamento e prêmio.
- Distribuição e média do reward.
- Coerência das transições de jornada.

Uma perda média baixa não é suficiente. O modelo deve reproduzir relações relevantes do ambiente. O Oracle poderá apoiar esse diagnóstico, mas não fará parte do treino padrão.

## 8. Comparar com referências simples

O MLP deve ser comparado com baselines ainda mais simples:

- Persistência: usar o estado atual como previsão do próximo estado.
- Média ou frequência histórica: prever a média numérica ou a classe mais frequente.
- Modelo linear ou árvore simples, quando apropriado.

O MLP só se torna uma referência útil se superar essas alternativas em métricas relevantes e justificar sua complexidade adicional.

## 9. Ferramentas e reprodutibilidade

As ferramentas desta fase têm funções específicas:

```text
Pandas e PyArrow:       leitura dos Parquet e preparação tabular.
NumPy:                  operações numéricas auxiliares.
scikit-learn:           codificação, normalização e divisões temporais.
PyTorch:                definição, treino e inferência da MLP.
MLflow:                 registro de parâmetros, métricas e artefatos.
pytest:                 validação automatizada do pipeline.
matplotlib:             gráficos de treino e avaliação.
```

Cada experimento deve registrar versão e filtros do dataset, seed, entradas e alvos, transformações, arquitetura, hiperparâmetros, métricas, *checkpoint* e gráficos. O objetivo é permitir reprodução e auditoria do resultado.

## 10. Resultados esperados e critérios de passagem

Ao final desta etapa, devem existir:

- Pipeline reproduzível de preparação de dados para a MLP.
- Divisão temporal explicitamente documentada.
- Baselines simples e MLP treinados na mesma base de avaliação.
- Métricas por tipo de saída e por segmento relevante.
- Avaliação agregada de trajetórias contra o ground truth.
- Experimentos registrados em MLflow.
- Testes para formato de entrada, ausência de vazamento e reprodutibilidade básica.
- Relatório de limitações, em especial sobre sazonalidade no ambiente atual.

A evolução para modelos de sequência ou World Models mais avançados dependerá de evidência de que o MLP capturou parte da dinâmica, mas deixou erros estruturais relevantes que uma arquitetura com memória ou incerteza explícita pode resolver.

## Síntese

O baseline MLP é um instrumento de aprendizado e comparação, não o ponto final do projeto. Ele estabelece uma medida honesta do que pode ser aprendido com estado agregado, ação e contexto disponível.

Seu valor está na simplicidade: torna possível detectar problemas de dados, vazamento temporal, alvos mal definidos e métricas inadequadas antes que a complexidade de um World Model mais sofisticado esconda esses problemas. A próxima evolução do projeto será guiada pelos limites observados nesse baseline.
