# Como preparar um dataset para treinar um modelo de comportamento

## Objetivo metodológico

Um dataset para treinamento de modelo não nasce pronto. Ele é construído a partir de registros operacionais — os **fatos** — e de uma definição clara do comportamento que se deseja explicar, prever ou simular.

Em seguros, fatos são eventos observados no relacionamento entre cliente e seguradora: contratação de apólice, emissão de cotação, pagamento, inadimplência, abertura de sinistro, renovação, cancelamento, contato por corretor, abertura de e-mail, acesso ao aplicativo e recebimento de uma oferta. Esses fatos geralmente estão distribuídos entre sistemas diferentes, com datas, chaves e níveis de qualidade variados.

O processo começa pela pergunta de negócio. Exemplos:

- Qual cliente provavelmente aceitará uma oferta de seguro residencial?
- Qual cliente tem risco de cancelar nos próximos 90 dias?
- Qual será o efeito de reduzir o preço ou de acionar um corretor?
- Como o estado de relacionamento do cliente deve evoluir após determinada ação?

A pergunta determina a unidade de análise. Em um modelo de propensão, a unidade pode ser “cliente em uma data de referência”. Em um modelo de cancelamento, pode ser “apólice em cada mês de vigência”. Em um World Model, a unidade mais adequada é uma transição temporal:

```text
estado do cliente no tempo t
+ ação da seguradora no tempo t
→ estado do cliente no tempo t+1
+ resultado observado
```

Essa escolha transforma fatos dispersos em sequências de decisão e consequência.

## 1. Consolidar os fatos

O primeiro trabalho consiste em reunir fontes confiáveis em uma camada analítica. Em um caso real de seguros, as fontes comuns seriam:

- Cadastro de clientes: idade, localização, perfil, data de entrada e canais preferenciais.
- Apólices: produtos contratados, coberturas, prêmios, vigência, renovação e cancelamento.
- Cotações e ofertas: produto ofertado, preço, desconto, canal, data e resultado.
- Sinistros: abertura, pagamento, frequência, severidade e situação.
- Cobrança: pagamentos, atrasos, inadimplência e recuperação.
- Interações: ligações, contatos de corretor, e-mails, campanhas, aplicativo e atendimento.
- Dados digitais: logins, sessões, abertura de mensagens e navegação, quando houver base legal para uso.
- Dados externos autorizados: região, perfil socioeconômico agregado ou indicadores de mercado, quando juridicamente apropriado.

Cada fato deve conter, idealmente, uma chave de cliente ou apólice, uma data/hora, o tipo de evento, valores associados e sua origem. Sem chaves e carimbos de tempo confiáveis, não é possível reconstruir a história do cliente com segurança.

## 2. Construir uma linha do tempo

Depois da consolidação, os fatos são organizados em ordem temporal. É comum definir uma periodicidade, por exemplo semanal ou mensal, para criar fotografias sucessivas do cliente.

Em uma fotografia mensal, o dataset poderia informar que, em 31 de março, o cliente possui seguro auto, tem 28 meses de relacionamento, pagou os últimos prêmios em dia, teve um sinistro nos últimos 12 meses, abriu dois e-mails no período, não possui seguro residencial e recebeu uma oferta residencial via aplicativo.

No mês seguinte, observa-se o resultado: contratou ou não o seguro, alterou seu nível de engajamento, abriu um sinistro, renovou ou cancelou uma apólice e gerou margem, custo ou perda econômica.

O cuidado metodológico central é garantir que cada variável do estado seja calculada apenas com informações disponíveis até aquele instante. Uma compra ocorrida em abril não pode ser usada para descrever o estado de março. Esse erro é chamado de **vazamento de informação** e produz modelos aparentemente excelentes, mas inúteis em produção.

## 3. Transformar fatos em variáveis de comportamento

Registros brutos raramente são usados diretamente pelo modelo. Eles são transformados em variáveis — também chamadas de atributos ou *features* — que sintetizam padrões relevantes.

Por exemplo, a variável “engajamento digital” pode ser derivada de número de logins nos últimos 30 dias, abertura de e-mails, cliques em campanhas, simulações feitas no aplicativo e atendimentos iniciados por canais digitais.

Ela não precisa ser uma única medida verdadeira. Pode ser uma composição documentada de vários fatos observáveis. O mesmo vale para outras dimensões:

```text
sensibilidade a preço:
    resposta histórica a descontos;
    frequência de comparação de cotações;
    cancelamentos após reajustes;
    aceitação de propostas com menor preço.

afinidade com seguros:
    quantidade e diversidade de produtos;
    histórico de cotações;
    propensão histórica a cross-sell;
    relacionamento e permanência.

confiança ou qualidade do relacionamento:
    resolução de reclamações;
    satisfação, quando disponível;
    histórico de sinistros e indenizações;
    frequência de contato;
    pagamentos e renovações.
```

Em dados reais, é importante diferenciar três tipos de variável:

- **Observáveis diretamente:** idade, apólice ativa, prêmio, sinistro, pagamento e ação de campanha.
- **Derivadas:** frequência de uso, recência de contato, taxa de abertura e tendência de pagamento.
- **Latentes:** confiança, intenção de compra e sensibilidade a preço. Elas não são observadas diretamente; são aproximadas por indicadores, questionários, segmentações ou estimadas por modelos auxiliares.

Diferentemente do ambiente sintético, no mundo real não se conhece o valor exato de `trust` ou `insurance_affinity`. O que existe são sinais imperfeitos. Esse é um dos principais desafios científicos do projeto.

## 4. Definir a ação e o resultado

Para avaliar decisões da seguradora, a ação precisa ser registrada com precisão. Não basta saber que um cliente comprou; é necessário saber o que recebeu antes da compra.

Uma ação pode conter tipo de ação, produto ofertado, preço, desconto, canal, data e horário, campanha, corretor responsável — quando aplicável — e motivo ou regra de elegibilidade.

O resultado também precisa ser definido antes da modelagem. Pode ser contratação em 30 dias, renovação em 90 dias, cancelamento no mês seguinte, margem esperada ou receita líquida.

É essencial registrar também quem não recebeu ação. Clientes sem oferta formam o grupo de referência. Sem essa informação, um modelo pode confundir correlação com efeito causal. Por exemplo, clientes que receberam contato de corretor podem converter mais não porque o contato causou a compra, mas porque já eram os clientes mais propensos e foram priorizados pelo time comercial.

## 5. Construir o dataset de treinamento

A estrutura final depende do objetivo. Para um World Model, cada linha deve conter:

```text
identificador do cliente;
instante t;
estado observado no instante t;
ação tomada no instante t;
estado observado no instante t+1;
resultado econômico ou operacional;
indicador de fim de trajetória.
```

Em notação:

```text
S_t + A_t → S_t+1 + R_t
```

Onde:

```text
S_t     estado do cliente no período atual;
A_t     ação comercial ou operacional;
S_t+1   estado futuro;
R_t     resultado, como margem, conversão ou custo.
```

As colunas devem permanecer estruturadas. Estados anteriores recebem um prefixo, como `state_`; estados posteriores, `next_state_`; e ações, `action_`. Essa convenção torna a auditoria e o treinamento mais claros.

## 6. Controlar qualidade, ética e governança

Antes do treinamento, o dataset precisa passar por validações técnicas e de negócio:

- Ausência de datas impossíveis, chaves duplicadas e valores inválidos.
- Verificação de valores ausentes e sua causa.
- Controle de mudanças nas definições de variáveis ao longo do tempo.
- Comparação de distribuições entre períodos, regiões, produtos e canais.
- Revisão de representatividade dos segmentos.
- Separação de dados pessoais e aplicação de minimização, pseudonimização e controles de acesso.
- Avaliação de possíveis vieses contra grupos protegidos.
- Registro da origem, definição e responsável por cada variável.

No caso de seguros, o uso de dados deve observar a LGPD, as finalidades informadas aos titulares, a necessidade de cada atributo e as regras internas de governança e risco de modelo. Dados sensíveis não devem ser usados apenas por estarem disponíveis; é necessário justificar finalidade, base legal, proporcionalidade e impacto.

## 7. Separar treino, validação e teste no tempo

Dados comportamentais são temporais. Portanto, a separação não deve ser totalmente aleatória. Uma abordagem mais realista seria:

```text
Janeiro a setembro: treinamento
Outubro a novembro: validação
Dezembro: teste final
```

Assim, o modelo é avaliado em um período futuro, como acontecerá em produção. Também é importante garantir que trajetórias do mesmo cliente não sejam divididas de forma inadequada entre treino e teste, especialmente quando o objetivo envolve prever sua evolução temporal.

## 8. Medir mais do que precisão

Em modelos de comportamento, não basta perguntar se a previsão está certa. É preciso avaliar:

- Se o próximo estado foi previsto com qualidade.
- Se probabilidades previstas correspondem às frequências reais.
- Se a previsão é estável entre segmentos e períodos.
- Se o modelo responde de forma plausível às ações.
- Se uma mudança de preço, canal ou desconto produz efeitos coerentes.
- Se o ganho econômico estimado aparece em dados futuros.
- Se há vieses, vazamento de informação ou degradação ao longo do tempo.

Para um World Model, a avaliação pode comparar trajetórias simuladas com trajetórias reais: distribuição de produtos, conversão, cancelamento, prêmio, engajamento e reward ao longo dos meses.

## 9. Exemplo prático: eventos raros como tarefas auxiliares

No experimento sintético, compras e cancelamentos são pouco frequentes, mas podem causar mudanças grandes no prêmio mensal e no reward. Quando um único decoder tenta prever diretamente o reward, ele precisa aprender ao mesmo tempo se o evento ocorrerá e qual será sua consequência econômica. Isso tende a produzir alguns erros grandes, visíveis no RMSE.

Uma adequação metodológica é usar **aprendizado multi-task**. O input continua sendo exclusivamente o que se sabe no instante da decisão:

```text
state_t + action_t
```

O resultado observado após a ação passa a supervisionar várias cabeças em paralelo:

```text
state_t + action_t
        ↓
    World Model
        ├── próximo estado numérico
        ├── próxima etapa da jornada
        ├── reward
        ├── probabilidade de compra
        └── probabilidade de cancelamento
```

Compra e cancelamento são **targets**, não features. Portanto, `purchased` e `cancelled` jamais entram no encoder do estado ou da ação; eles apenas informam a perda após a predição. Essa regra evita vazamento de informação: no momento de decidir uma oferta, ainda não sabemos se ela será aceita.

Na implementação, as cabeças de compra e cancelamento retornam logits e são treinadas com `binary_cross_entropy_with_logits`. A perda total combina as tarefas:

```text
loss total =
    loss de próximo estado
  + loss de jornada
  + loss de reward
  + peso_compra × loss de compra
  + peso_cancelamento × loss de cancelamento
```

Os pesos devem ser experimentais, não arbitrários. Um ponto de partida moderado é `0,5` para compra e `0,5` para cancelamento, preservando as perdas principais. A avaliação deve reportar, além de MAE/RMSE do reward, acurácia e Brier Score das probabilidades dos eventos. O Brier Score verifica se a probabilidade prevista é coerente com a frequência observada.

Em dados reais, a mesma estrutura só deve ser usada se a definição temporal dos eventos estiver auditada e disponível após `t`. Eventos ainda em processamento, informações obtidas depois do horizonte ou variáveis derivadas do resultado não podem ser incluídos no estado atual.

## 10. Adequação e calibração progressiva do modelo

A qualidade de um World Model não depende apenas de aumentar a rede. A prática recomendada é começar com uma referência simples, identificar qual tipo de erro limita a utilidade do modelo e alterar somente os componentes relacionados a esse erro. Cada alteração deve ser medida no mesmo split de clientes, com seed e dataset versionados.

No P&D sintético, a sequência de decisão foi:

```text
Baseline MLP
    ↓
World Model com estado e ação separados
    ↓
Latente maior + dinâmica residual + Huber Loss
    ↓
Heads auxiliares para compra e cancelamento
```

### Escolhas realizadas

O modelo selecionado, EXP-005, adota as seguintes escolhas:

- **Estado latente com 64 dimensões:** aumenta a capacidade de resumir as relações entre estado, ação e transição sem utilizar variáveis latentes verdadeiras do simulador como entrada.
- **Encoder de estado separado do encoder de ação:** preserva a diferença conceitual entre “quem é o cliente agora” e “o que a seguradora fez”.
- **Dinâmica latente:** aprende a transformação do estado sob uma ação antes de decodificar os resultados observáveis.
- **Conexão residual para o próximo estado numérico:** permite que variáveis que mudam pouco de um período para outro preservem informação do estado atual, enquanto a dinâmica aprende o delta causado por ação e contexto.
- **Huber Loss com peso moderado para reward:** melhora o erro típico de reward sem deixar poucos eventos extremos dominarem todo o treino.
- **Heads auxiliares de compra e cancelamento:** ensinam o modelo a identificar eventos raros que explicam mudanças abruptas de prêmio e reward. Esses eventos são alvos pós-ação, nunca variáveis de entrada.
- **Scheduler de learning rate:** reduz a taxa de aprendizado durante o treino para refinar os parâmetros após as primeiras épocas.

### Possibilidades avaliadas e quando usá-las

- **Aumentar a dimensão latente** (`32 → 48 → 64 → 96`): usar quando a validação indicar falta de capacidade. Aumentar somente se houver ganho no teste; dimensões maiores podem memorizar o treino.
- **Adicionar heads auxiliares:** usar quando um evento observável explica uma parte relevante do reward ou do próximo estado. Exemplos: compra, cancelamento, inadimplência ou renovação.
- **Mudar a perda de reward:** MSE prioriza erros grandes; Huber prioriza o erro típico; uma combinação ponderada pode equilibrar ambos. A escolha deve seguir MAE e RMSE na escala econômica original.
- **Ponderar eventos raros ou estratificar batches:** usar quando os eventos críticos são pouco frequentes e o modelo deixa de aprendê-los. Os pesos devem ser avaliados contra métricas por evento, para evitar degradar a população geral.
- **Regularização (dropout ou weight decay):** usar apenas se houver indício de overfitting, como erro de treino caindo enquanto a validação piora.
- **Scheduler e early stopping:** usar para evitar treinamento excessivo e selecionar o melhor checkpoint pela validação, não pelo teste.
- **Transformação de reward:** `asinh` ou Yeo-Johnson aceitam valores negativos; só adotar se melhorarem MAE e RMSE após a inversão para a escala original. Log simples não é apropriado quando há rewards negativos.

### Boas práticas de seleção

1. Comparar candidatos usando validação; usar o teste isolado uma única vez para confirmar a escolha final.
2. Nunca comparar somente uma métrica. Para o reward, acompanhar MAE e RMSE; para eventos, acompanhar Brier Score, taxa-base e, quando necessário, precisão/recall.
3. Separar métricas por segmento e por tipo de evento. Uma acurácia alta para cancelamento pode ser enganosa quando a taxa-base é muito baixa.
4. Repetir o candidato selecionado com múltiplas seeds antes de afirmar robustez estatística.
5. Registrar arquitetura, dimensão latente, pesos das perdas, scheduler, seed, versão de dados e versão do ambiente em MLflow.
6. Preservar a separação entre ground truth, dados públicos e oracle. O oracle é exclusivo para avaliação científica.

### Decisão de avanço

O EXP-005 foi selecionado como candidato de referência para a próxima fase porque melhorou o MAE de reward (`2,4142` contra `2,8446` do baseline), manteve ganhos de jornada (`90,88%` contra `86,96%`) e preservou a qualidade do próximo estado. O RMSE de reward ainda merece acompanhamento por representar eventos econômicos extremos, mas não impede o avanço experimental para simulação, desde que a fase seguinte reporte esse limite de forma explícita.

## Síntese

Em um caso real, o dataset não é apenas uma planilha de clientes. Ele é uma reconstrução temporal, auditável e governada da relação entre cliente, contexto, decisão e consequência.

O ambiente sintético da Fase 1 simplifica esse processo: ele cria os estados, as variáveis latentes, as ações e os resultados sob regras conhecidas. Na transição para dados reais, a principal mudança será sair de variáveis arbitradas e observações completas para registros imperfeitos, fontes heterogêneas, variáveis latentes aproximadas e necessidade de validação causal, regulatória e operacional.
