# Insurance World Model

## Especificação Geral do Projeto — P&D

**Versão:** 0.1
**Status:** P&D / Proof of Concept
**Objetivo:** investigar a viabilidade de um World Model aplicado à simulação de comportamento de clientes de seguros.

---

# 1. Visão do projeto

O projeto investiga a hipótese de que um modelo de aprendizado de máquina pode aprender a dinâmica de evolução de clientes de seguros a partir de trajetórias sintéticas e, posteriormente, utilizar essa representação para simular futuros possíveis diante de diferentes ações da seguradora.

A hipótese central é:

> Dado o estado de um cliente e uma ação da seguradora, é possível aprender uma função que estime o próximo estado do cliente e os resultados associados.

Formalmente:

```text
S_t + A_t → S_t+1 + R_t
```

onde:

* `S_t` = estado do cliente no instante `t`
* `A_t` = ação executada pela seguradora
* `S_t+1` = próximo estado do cliente
* `R_t` = resultado/recompensa associado à transição

O objetivo final não é construir inicialmente um sistema de decisão autônoma, mas demonstrar que um modelo consegue aprender uma dinâmica de mundo e utilizá-la para realizar simulações e análises contrafactuais.

---

# 2. Motivação

Modelos preditivos tradicionais normalmente respondem perguntas como:

```text
Qual a probabilidade deste cliente comprar?
```

O projeto pretende investigar uma pergunta diferente:

```text
O que provavelmente acontecerá se fizermos X com este cliente?
```

E posteriormente:

```text
O que provavelmente aconteceria se fizéssemos X,
Y ou Z?
```

Isso permite evoluir de:

```text
PREDICTION
```

para:

```text
SIMULATION
```

e posteriormente:

```text
DECISION SUPPORT
```

---

# 3. Escopo do P&D

O projeto será desenvolvido incrementalmente.

## Fase 1 — Ambiente sintético

Construir um ambiente artificial de clientes de seguros com dinâmica conhecida.

Entrega:

```text
Insurance Environment
```

---

## Fase 2 — Dataset sintético

Executar o ambiente e gerar trajetórias de clientes.

Formato fundamental:

```text
S_t + A_t → S_t+1 + R_t
```

Entrega:

```text
Insurance Trajectory Dataset
```

---

## Fase 3 — World Model

Treinar uma rede neural para aprender a dinâmica do ambiente.

Entrada:

```text
state + action
```

Saída:

```text
predicted next_state
predicted reward
```

Entrega:

```text
Insurance World Model v1
```

---

## Fase 4 — Simulator

Utilizar o World Model para gerar trajetórias futuras sem executar o ambiente original.

Entrega:

```text
Insurance World Simulator
```

---

## Fase 5 — Contrafactuais

Comparar diferentes ações partindo do mesmo estado inicial.

Exemplo:

```text
Cliente X

          ┌── Oferta A → futuro A
Estado ───┼── Oferta B → futuro B
          └── Oferta C → futuro C
```

Entrega:

```text
Counterfactual Scenario Analysis
```

---

## Fase 6 — Decision Support

Criar uma interface simples para comparar estratégias comerciais.

Exemplo:

```text
Produto
Preço
Canal
Segmento
Horizonte
Número de simulações
```

Resultado:

```text
Adesão esperada
LTV esperado
Margem esperada
Distribuição dos resultados
```

Esta fase é opcional no primeiro ciclo do P&D.

---

# 4. Fora do escopo inicial

Não implementar inicialmente:

* integração com dados reais de clientes;
* tomada de decisão automática em produção;
* reinforcement learning completo;
* agente autônomo;
* fine-tuning de modelos gigantes;
* integração com sistemas corporativos;
* modelos regulatórios reais;
* previsão real de sinistralidade;
* utilização do World Model como ferramenta de underwriting;
* deployment produtivo.

Esses elementos podem ser avaliados posteriormente.

---

# 5. Conceito de World Model adotado

Neste projeto, World Model será definido como:

> Um modelo que aprende uma representação do estado de um ambiente e sua dinâmica, permitindo estimar como o ambiente evolui diante de diferentes ações.

A implementação inicial deve ser baseada em:

```text
STATE
  +
ACTION
  ↓
WORLD MODEL
  ↓
NEXT STATE
  +
REWARD
```

O modelo não deve simplesmente classificar clientes.

Ele deve aprender transições.

---

# 6. Ambiente sintético

O ambiente representa uma população artificial de clientes de seguros.

Cada cliente possui características observáveis e características latentes.

## Variáveis observáveis

```text
age
tenure_months
auto_policy
home_policy
life_policy
claims_12m
premium_monthly
digital_engagement
journey_stage
```

## Variáveis latentes

```text
price_sensitivity
insurance_affinity
trust
```

As variáveis latentes representam características internas do cliente que influenciam seu comportamento.

Elas são conhecidas pelo simulador, mas não devem necessariamente ser disponibilizadas ao World Model durante o treinamento.

Isso permite avaliar se o modelo consegue aprender representações úteis a partir de dados observáveis.

---

# 7. Produtos

Inicialmente:

```text
AUTO
HOME
LIFE
```

O produto HOME deverá ser particularmente relevante para os experimentos de cross-sell.

---

# 8. Canais

Inicialmente:

```text
APP
EMAIL
BROKER
CALL_CENTER
```

---

# 9. Ações

O espaço inicial de ações será:

```text
NO_ACTION
OFFER_PRODUCT
SEND_MESSAGE
CONTACT_BROKER
CHANGE_PRICE
```

Uma ação `OFFER_PRODUCT` deve possuir:

```text
product
price
channel
discount
```

Exemplo:

```json
{
  "type": "OFFER_PRODUCT",
  "product": "HOME",
  "price": 39.90,
  "channel": "BROKER",
  "discount": 0
}
```

---

# 10. Jornada do cliente

O cliente poderá estar em um dos estados:

```text
UNAWARE
AWARE
INTERESTED
QUOTING
CONSIDERING
CUSTOMER
CANCELLED
```

As transições deverão depender do estado atual, da ação realizada e das características do cliente.

---

# 11. Dinâmica do ambiente

A dinâmica deve ser sintética, mas não trivial.

Deve conter relações controladas como:

```text
menor preço
→ maior probabilidade de interesse

maior price_sensitivity
→ maior resposta a desconto

maior digital_engagement
→ maior resposta a APP

maior trust
→ maior probabilidade de contratação

contact_broker
→ aumento de conversão para determinados perfis

excesso de contatos
→ redução de engagement

cliente com AUTO
→ maior afinidade inicial com HOME

contratação
→ alteração do estado de relacionamento

cancelamento
→ redução de relacionamento
```

O ambiente deverá conter ruído estocástico controlado.

A seed deve ser configurável.

---

# 12. Ground Truth

O ambiente sintético representa a verdade do mundo.

Portanto:

```text
Environment
    ↓
Ground Truth
```

O World Model deverá tentar aprender essa dinâmica sem acessar diretamente as regras internas.

Isso permite avaliar:

```text
World Model prediction
        VS
Environment ground truth
```

O projeto deverá preservar uma versão "oracle" dos dados contendo as variáveis latentes e informações internas necessárias para avaliação.

---

# 13. Dataset

Cada trajetória deve representar uma sequência temporal:

```text
S0
 ↓
A0
 ↓
S1
 ↓
A1
 ↓
S2
 ↓
A2
 ↓
S3
```

Cada transição deve conter:

```text
trajectory_id
customer_id
timestamp
step
state
action
next_state
reward
done
```

Formato lógico:

```text
S_t + A_t → S_t+1 + R_t
```

O dataset deve ser armazenado em formato apropriado para treinamento posterior, preferencialmente Parquet.

---

# 14. Geração do dataset

O projeto deverá permitir gerar datasets parametrizados.

Exemplo:

```bash
python -m data.generate_dataset \
    --customers 10000 \
    --months 12 \
    --seed 42 \
    --output artifacts/insurance_trajectories.parquet
```

Deve ser possível gerar datasets maiores sem alteração do código.

---

# 15. Dataset Oracle

Uma segunda versão deverá preservar informações internas do simulador.

Exemplo:

```text
artifacts/
├── insurance_trajectories.parquet
└── insurance_oracle.parquet
```

O dataset Oracle será utilizado exclusivamente para avaliação.

Não utilizar informações Oracle durante o treinamento do World Model, salvo quando explicitamente definido em um experimento.

---

# 16. World Model

A primeira versão do World Model não deve utilizar um modelo gigante.

A primeira implementação deve priorizar:

```text
PyTorch
+
MLP / Transformer pequeno
```

Arquitetura inicial conceitual:

```text
State
  ↓
State Encoder
  ↓
Latent State
  +
Action Encoder
  ↓
Dynamics Model
  ↓
Predicted Latent State
  ↓
Decoder
  ↓
Predicted Next State
```

Em paralelo:

```text
Latent State
  ↓
Reward Head
  ↓
Predicted Reward
```

---

# 17. Objetivo do treinamento

O World Model deverá minimizar o erro entre suas previsões e a ground truth.

Conceitualmente:

```text
prediction = model(state, action)

state_loss =
    difference(predicted_next_state, next_state)

reward_loss =
    difference(predicted_reward, reward)

total_loss =
    state_loss + reward_loss
```

A função de perda deverá ser adequada aos tipos das variáveis.

Não assumir que todas as variáveis são contínuas.

Variáveis categóricas devem possuir tratamento apropriado.

---

# 18. Treinamento

O treinamento deverá possuir:

```text
train
validation
test
```

O split deve ser feito de forma a evitar vazamento de informação entre trajetórias do mesmo cliente.

Sempre que possível:

```text
clientes de treinamento
≠
clientes de validação
≠
clientes de teste
```

Registrar:

```text
loss
epoch
learning rate
dataset version
model version
seed
```

Utilizar MLflow para tracking dos experimentos.

---

# 19. Métricas do World Model

A avaliação deverá medir separadamente:

### State prediction

Precisão na previsão do próximo estado.

### Reward prediction

Precisão na previsão do reward.

### Probabilistic calibration

Quando houver probabilidades, avaliar se as probabilidades previstas são calibradas.

### One-step prediction

```text
S_t + A_t → S_t+1
```

### Multi-step prediction

```text
S_t
 ↓
A_t
 ↓
S_t+1
 ↓
A_t+1
 ↓
S_t+2
 ↓
...
```

Avaliar degradação da previsão conforme o horizonte aumenta.

---

# 20. Simulator

O Simulator deverá utilizar o World Model para gerar futuros.

Entrada:

```text
initial_state
strategy
horizon
number_of_simulations
```

Exemplo:

```json
{
  "initial_state": "...",
  "strategy": {
    "product": "HOME",
    "price": 39.90,
    "channel": "BROKER"
  },
  "horizon_months": 12,
  "simulations": 1000
}
```

Saída:

```text
trajectories
outcomes
statistics
```

---

# 21. Contrafactuais

O Simulator deverá permitir manter o mesmo estado inicial e alterar apenas a ação ou estratégia.

Exemplo:

```text
Estado inicial
      │
      ├── Strategy A
      │
      ├── Strategy B
      │
      └── Strategy C
```

Isso permitirá comparar:

```text
adoption
LTV
margin
reward
retention
```

entre estratégias.

---

# 22. Long-horizon simulation

O projeto deverá testar diferentes horizontes:

```text
1 step
5 steps
12 steps
24 steps
```

O objetivo é descobrir quanto tempo o World Model consegue simular antes que os erros acumulados comprometam a utilidade da previsão.

---

# 23. Teste de generalização

Um dos experimentos principais será apresentar ao World Model situações diferentes das utilizadas no treinamento.

Exemplos:

```text
novo preço
novo canal
nova combinação de produto
novo segmento
nova estratégia comercial
```

A pergunta experimental é:

> O World Model consegue prever resultados de cenários que não estavam explicitamente presentes no dataset de treinamento?

---

# 24. Teste de mudança de regime

Criar posteriormente mudanças no ambiente:

```text
mudança econômica
mudança de comportamento
novo concorrente
mudança de preço
mudança de canal
```

O objetivo é avaliar:

> Como o World Model se comporta quando a dinâmica do ambiente muda?

Esse experimento será a base para uma futura investigação de continual learning.

---

# 25. Comparação com modelo tradicional

O projeto deverá, em uma fase posterior, comparar:

```text
Modelo tradicional de propensity
VS
World Model
```

O modelo tradicional responderá:

```text
P(compra)
```

O World Model deverá permitir:

```text
State + Action
→
Future State + Outcome
```

A comparação deverá avaliar se a segunda abordagem fornece informação adicional para decisão e simulação.

---

# 26. Interface final do P&D

A interface não precisa ser inicialmente sofisticada.

O conceito desejado é:

```text
┌─────────────────────────────────────────┐
│       INSURANCE WORLD SIMULATOR         │
│                                         │
│ Segmento:     Auto Customers            │
│ Produto:      HOME                      │
│ Preço:        R$ 39,90                  │
│ Canal:        BROKER                    │
│ Horizonte:    12 meses                  │
│ Simulações:   1.000                     │
│                                         │
│              [ SIMULAR ]                │
│                                         │
│ Adesão esperada       16,3%             │
│ LTV esperado          R$ 156             │
│ Margem esperada       R$ 103             │
│                                         │
│ Intervalo 90%         14,5%–18,1%       │
└─────────────────────────────────────────┘
```

A interface é apenas uma camada de demonstração.

O núcleo do projeto deverá estar disponível por API Python.

---

# 27. API conceitual

A interface principal deverá permitir:

```python
result = world_model.predict(
    state=state,
    action=action
)
```

Retornando:

```python
{
    "next_state": ...,
    "outcome": ...,
    "reward": ...
}
```

O Simulator deverá permitir:

```python
result = simulator.simulate(
    initial_state=state,
    strategy=strategy,
    horizon=12,
    simulations=1000
)
```

Retornando estatísticas agregadas e, opcionalmente, as trajetórias individuais.

---

# 28. Arquitetura tecnológica inicial

Utilizar inicialmente:

```text
Python
PyTorch
NumPy
Pandas
scikit-learn
Pydantic
pytest
MLflow
FastAPI
Matplotlib
```

Persistência inicial:

```text
Parquet
```

Não introduzir inicialmente:

```text
Kafka
Kubernetes
Kubeflow
Feature Store
Cloud infrastructure
```

Esses componentes poderão ser avaliados posteriormente.

---

# 29. Estrutura do repositório

```text
insurance-world-model/
│
├── environment/
│   ├── __init__.py
│   ├── models.py
│   └── insurance_env.py
│
├── data/
│   ├── __init__.py
│   ├── generate_dataset.py
│   └── dataset.py
│
├── model/
│   ├── __init__.py
│   ├── encoder.py
│   ├── world_model.py
│   └── losses.py
│
├── training/
│   ├── __init__.py
│   ├── train.py
│   └── config.py
│
├── simulation/
│   ├── __init__.py
│   └── simulator.py
│
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py
│   └── evaluate.py
│
├── api/
│   └── app.py
│
├── tests/
│
├── notebooks/
│
├── artifacts/
│
├── README.md
├── PROJECT_SPEC.md
├── requirements.txt
└── pyproject.toml
```

A estrutura poderá evoluir conforme os experimentos demonstrarem necessidade.

---

# 30. Roadmap do P&D

## Sprint 1 — Environment

Entregar:

```text
Insurance Environment
State Model
Action Model
Transition Logic
Reward Logic
Tests
```

Critério de sucesso:

```text
environment.step()
```

funciona de forma consistente e reproduzível.

---

## Sprint 2 — Synthetic Dataset

Entregar:

```text
Trajectory Generator
Dataset
Oracle Dataset
Visualization
```

Critério de sucesso:

```text
S_t + A_t → S_t+1 + R_t
```

pode ser gerado em escala.

---

## Sprint 3 — Baseline Model

Antes do World Model, implementar um baseline simples.

Exemplo:

```text
MLP
```

para:

```text
state + action → next_state
```

Objetivo:

estabelecer uma referência de desempenho.

---

## Sprint 4 — World Model

Implementar:

```text
State Encoder
Action Encoder
Dynamics Model
Reward Model
Decoder
Training Pipeline
```

Critério de sucesso:

superar o baseline em métricas relevantes.

---

## Sprint 5 — Imagination / Simulation

Implementar:

```text
one-step prediction
multi-step prediction
trajectory generation
```

Critério de sucesso:

gerar trajetórias coerentes por múltiplos passos.

---

## Sprint 6 — Counterfactuals

Implementar:

```text
same state
different actions
different futures
```

Comparar previsões com a ground truth do ambiente.

---

## Sprint 7 — Demo

Construir uma interface mínima:

```text
State
+
Strategy
+
Horizon
+
Simulations
```

→

```text
Adoption
LTV
Margin
Reward
Confidence interval
```

---

# 31. Critérios de sucesso do P&D

O projeto será considerado tecnicamente bem-sucedido se demonstrar:

### Critério 1

O modelo aprende a prever o próximo estado melhor que um baseline simples.

### Critério 2

O modelo consegue prever rewards com erro aceitável.

### Critério 3

O modelo consegue gerar trajetórias multi-step coerentes.

### Critério 4

O modelo consegue avaliar ações diferentes a partir do mesmo estado.

### Critério 5

O modelo consegue generalizar parcialmente para combinações de ações não observadas no treinamento.

### Critério 6

A simulação apresenta valor adicional em relação a uma previsão simples de propensity.

---

# 32. Princípio científico do projeto

O projeto deverá preservar uma separação rigorosa entre:

```text
GROUND TRUTH
```

e:

```text
MODEL PREDICTION
```

O simulador sabe como o mundo funciona.

O World Model precisa descobrir como o mundo funciona a partir das trajetórias.

Não alterar as regras do ambiente para melhorar artificialmente o desempenho do World Model.

Toda alteração da dinâmica do ambiente deve gerar uma nova versão do experimento.

---

# 33. Versionamento dos experimentos

Cada experimento deve registrar:

```text
experiment_id
dataset_version
environment_version
model_version
random_seed
hyperparameters
training_metrics
evaluation_metrics
```

Exemplo:

```text
EXP-001

Environment: v0.1
Dataset:     v0.1
Model:       baseline-mlp-v1
Seed:        42
```

---

# 34. Reprodutibilidade

Todos os experimentos devem ser reproduzíveis sempre que possível.

Registrar:

```text
random seed
Python version
PyTorch version
dependencies
dataset version
model configuration
```

Evitar valores mágicos espalhados pelo código.

Configurações devem estar centralizadas.

---

# 35. Princípios de implementação

O Codex deverá:

1. Implementar incrementalmente.
2. Não antecipar fases futuras sem necessidade.
3. Manter o projeto executável ao final de cada etapa.
4. Criar testes antes ou junto das funcionalidades.
5. Evitar dependências desnecessárias.
6. Documentar decisões técnicas relevantes.
7. Não substituir uma implementação funcional por uma arquitetura mais complexa sem justificativa experimental.
8. Priorizar experimentação mensurável sobre complexidade.
9. Manter separação entre ambiente, dataset, modelo, treinamento, simulação e avaliação.
10. Não utilizar dados reais durante o P&D inicial.

---

# 36. Regra de atuação do Codex

O Codex deve trabalhar de forma incremental.

Antes de implementar uma nova fase:

1. verificar o estado atual do repositório;
2. ler `PROJECT_SPEC.md`;
3. identificar a fase atual;
4. verificar testes existentes;
5. implementar somente o necessário;
6. executar testes;
7. executar o experimento;
8. registrar resultados;
9. atualizar documentação;
10. somente então avançar.

Não implementar todas as fases de uma vez.

---

# 37. Estado inicial do projeto

O projeto começa em:

```text
PHASE 1 — ENVIRONMENT
```

Próxima tarefa:

```text
Construir o Insurance Environment
```

Não implementar ainda:

```text
World Model
Simulator
Agent
Reinforcement Learning
API de produção
```

Esses componentes serão construídos somente depois que a fase anterior estiver validada.

---

# 38. Visão futura

A arquitetura futura poderá evoluir para:

```text
                    REAL WORLD
                         │
                       EVENTS
                         ↓
                  STATE REPRESENTATION
                         ↓
                   WORLD MODEL
                         ↓
                    SIMULATOR
                         ↓
                     POLICY
                         ↓
                      ACTION
                         ↓
                    REAL WORLD
                         │
                         └───────────────↺
```

Em uma aplicação real de seguros:

```text
clientes
produtos
preços
canais
campanhas
mercado
contexto econômico
        ↓
Insurance World Model
        ↓
futuros possíveis
        ↓
estratégias
        ↓
decisão
        ↓
resultado real
        ↓
novos dados
        ↓
atualização do modelo
```

Essa arquitetura é uma hipótese de evolução e não faz parte do escopo obrigatório do primeiro P&D.

---

# 39. Resultado esperado ao final do primeiro ciclo

Ao final do P&D, deverá ser possível demonstrar:

```text
1. Criamos um mundo sintético de clientes de seguros.

2. Geramos trajetórias nesse mundo.

3. Treinamos um modelo somente com essas trajetórias.

4. O modelo aprendeu a prever transições.

5. Utilizamos o modelo para imaginar futuros.

6. Comparamos diferentes ações sobre o mesmo estado.

7. Medimos a qualidade das previsões contra a ground truth.

8. Demonstramos uma interface simples para exploração dos cenários.
```

A demonstração final deverá ser capaz de responder:

> **"Dado um estado de cliente e diferentes estratégias comerciais, o World Model consegue simular os futuros prováveis e comparar seus resultados?"**

Essa é a pergunta central do P&D.


