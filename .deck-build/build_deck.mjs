import fs from "node:fs/promises";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT = "C:/Users/t-gamer/OneDrive/Documentos/ChatGPT/Estudos de World Model/Insurance-World-Model-Apresentacao-Executiva-v2.pptx";
const RENDER = "C:/Users/t-gamer/OneDrive/Documentos/ChatGPT/Estudos de World Model/.deck-build/rendered";
const SRC = "C:/Users/t-gamer/Documents/Codex/2026-09-01/files-pasted-by-the-user-projeto/insurance-world-model";
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const C={ink:"#111318",muted:"#606772",panel:"#F0F2F4",rule:"#B8BCC4",blue:"#3D8DFF",light:"#D0EDFA",red:"#D94A4A",green:"#158466",white:"#FFFFFF"};

function box(slide,x,y,w,h,fill=C.panel,line="none",radius=false,name="box") { return slide.shapes.add({geometry:radius?"roundRect":"rect",name,position:{left:x,top:y,width:w,height:h},fill,line:{style:"solid",fill:line,width:line==="none"?0:1}}); }
function txt(slide,text,x,y,w,h,size=22,bold=false,color=C.ink,align="left",name="text") { const s=slide.shapes.add({geometry:"textbox",name,position:{left:x,top:y,width:w,height:h},fill:"none",line:{style:"solid",fill:"none",width:0}}); s.text=text; s.text.style={fontSize:size,bold,color,alignment:align,verticalAlignment:"middle",fontFamily:"Arial"}; return s; }
function line(slide,x,y,w,color=C.rule,width=2){ return box(slide,x,y,w,width,color,"none",false,"rule"); }
function base(title,num,eyebrow="INSURANCE WORLD MODEL • P&D") { const s=deck.slides.add(); s.background.fill=C.white; txt(s,eyebrow,42,26,650,28,15,true,C.muted); txt(s,title,42,62,1160,86,38,true); line(s,42,151,1196,C.rule,1); txt(s,String(num).padStart(2,"0"),1190,672,48,20,13,false,C.muted,"right"); return s; }
function notes(slide,paths,extra="") { slide.speakerNotes.textFrame.setText(`${extra}\n\n[Sources]\n${paths.map(p=>`- ${p}`).join("\n")}`); }
function pill(slide,label,x,y,w,fill=C.light,color=C.ink){box(slide,x,y,w,36,fill,"none",true);txt(slide,label,x+12,y,w-24,36,16,true,color,"center");}

// 1 — cover
{
 const s=deck.slides.add(); s.background.fill=C.white;
 txt(s,"P&D • WORLD MODEL PARA SEGUROS",42,36,620,30,16,true,C.muted);
 txt(s,"Do conceito à\nsimulação de futuros",42,145,570,190,58,true);
 txt(s,"O que construímos, como decidimos e onde o modelo ainda não pode ser usado",42,370,520,110,25,false,C.muted);
 box(s,690,42,548,586,C.panel,"none",true);
 txt(s,"Sₜ",744,130,100,70,50,true,C.ink,"center"); txt(s,"+",844,130,50,70,40,false,C.muted,"center"); txt(s,"Aₜ",894,130,100,70,50,true,C.blue,"center");
 txt(s,"↓",844,220,50,50,42,true,C.muted,"center");
 box(s,758,285,412,105,C.ink,"none",true);txt(s,"WORLD MODEL",758,285,412,105,32,true,C.white,"center");
 txt(s,"↓",844,405,50,50,42,true,C.muted,"center");
 txt(s,"Sₜ₊₁  +  Rₜ",740,472,440,70,44,true,C.blue,"center");
 txt(s,"02 SET 2026",42,650,220,22,14,false,C.muted);
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/README.md`]);
}

// 2 — executive thesis
{
 const s=base("A prova de conceito já percorre o ciclo completo — em ambiente sintético",2);
 txt(s,"A hipótese",42,185,330,35,20,true,C.muted); txt(s,"Aprender como o estado de um cliente evolui depois de uma ação da seguradora.",42,230,405,150,31,true);
 const stages=[["1","Mundo conhecido","Regras sintéticas + variáveis latentes"],["2","Aprendizado","Trajetórias → modelo de dinâmica"],["3","Imaginação","O modelo projeta futuros sem consultar o ambiente"],["4","Demonstração","Cenários fechados em uma interface local"]];
 stages.forEach((d,i)=>{const y=184+i*108; box(s,520,y,680,84,i===3?C.light:C.panel,"none",true);txt(s,d[0],540,y,45,84,24,true,C.blue,"center");txt(s,d[1],600,y+6,220,32,22,true);txt(s,d[2],600,y+38,560,36,18,false,C.muted);});
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/README.md`],"Mensagem: demonstramos o pipeline, não uma decisão de negócio pronta para produção.");
}

// 3 — classical prediction vs world model
{
 const s=base("Predizer um resultado e simular um mundo são problemas diferentes",3);
 txt(s,"ML PREDITIVO CLÁSSICO",42,180,530,34,18,true,C.muted);
 txt(s,"Uma pergunta,\numa resposta",42,225,470,92,34,true);
 txt(s,"Dados históricos + atributos",42,350,470,32,19,false,C.muted);
 txt(s,"↓",220,388,60,35,28,true,C.rule,"center");
 box(s,82,432,390,68,C.panel,"none",true);txt(s,"P(compra) = 16%",82,432,390,68,27,true,C.ink,"center");
 txt(s,"O algoritmo estima um alvo definido: propensão, fraude, churn, sinistro ou valor.",42,525,490,72,19,false,C.muted);
 line(s,620,180,2,C.rule,430);
 txt(s,"WORLD MODEL",690,180,490,34,18,true,C.blue);
 txt(s,"Uma ação,\nvários futuros",690,225,470,92,34,true);
 txt(s,"Estado atual + ação proposta",690,350,470,32,19,false,C.muted);
 txt(s,"↓",870,388,60,35,28,true,C.blue,"center");
 box(s,730,432,390,68,C.light,"none",true);txt(s,"Sₜ₊₁ + Rₜ → trajetória",730,432,390,68,25,true,C.ink,"center");
 txt(s,"O modelo aprende a dinâmica para encadear transições, comparar ações e projetar horizontes.",690,525,490,72,19,false,C.muted);
 box(s,255,625,770,42,C.ink,"none",true);txt(s,"Ambos são ML; muda a unidade de previsão e a finalidade da decisão.",275,625,730,42,19,true,C.white,"center");
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/model/world_model.py`],"Ponto de fala: um world model também é um algoritmo preditivo; ele não substitui automaticamente modelos clássicos. Ele amplia a unidade de análise de um alvo para a dinâmica state + action → next state + reward.");
}

// 4 — three evidence layers
{
 const s=base("Chat, projeto e repositório cumprem papéis diferentes na rastreabilidade",4);
 const cols=[
 ["CHAT","Raciocínio e decisões","Evolução conceitual; perguntas; correções semânticas; escolhas de escopo.",C.light],
 ["PROJETO","Contexto persistente","Especificação, metodologia, experimentos, artefatos e demo local.",C.panel],
 ["REPOSITÓRIO","Histórico verificável","O código entregue existe em uma pasta de trabalho; o repo aberto ainda está sem commits.","#FCE8E8"]];
 cols.forEach((d,i)=>{const x=42+i*400; box(s,x,205,360,340,d[3],"none",true);txt(s,d[0],x+24,226,310,30,16,true,i===2?C.red:C.blue);txt(s,d[1],x+24,280,310,70,28,true);txt(s,d[2],x+24,372,310,115,20,false,C.muted);});
 txt(s,"Implicação: conectar a pasta entregue ao repo permitirá transformar o histórico do chat em evidência versionada por etapa.",42,585,1160,55,21,true,C.red);
 notes(s,[`${SRC}/README.md`,"Codex task: Criar ambiente sintético de seguros","Local project status: master, no commits"]);
}

// 5 — timeline
{
 const s=base("O trabalho avançou por experimentos controlados, não por um único treinamento",5);
 line(s,90,335,1080,C.rule,3);
 const items=[
 ["S1–S2","Ambiente + dados","120 mil transições\ncom oracle separado"],
 ["EXP‑001","Baseline MLP","Referência simples\npara evitar complexidade gratuita"],
 ["EXP‑002","World Model v1","Separação explícita\nde estado, ação e dinâmica"],
 ["EXP‑003/004","Ajustes controlados","Seleção em validação;\nreward com Huber + residual"],
 ["EXP‑005","Eventos + demo","Heads de compra/cancelamento\ne simulador fechado"]];
 items.forEach((d,i)=>{const x=50+i*244; box(s,x+96,322,20,20,C.blue,"none",true);txt(s,d[0],x,205,210,34,18,true,C.blue,"center");txt(s,d[1],x,246,210,58,23,true,C.ink,"center");txt(s,d[2],x,372,210,100,17,false,C.muted,"center");});
 txt(s,"Cada etapa manteve dataset, seed, versões, métricas e artefatos de execução.",270,550,740,52,24,true,C.ink,"center");
 notes(s,[`${SRC}/README.md`,`${SRC}/EXPERIMENTS.md`,`${SRC}/artifacts/exp-005/run_metadata.json`]);
}

// 6 — methodology
{
 const s=base("A metodologia separa a verdade do simulador da previsão aprendida",6);
 const steps=[["01","Definir o mundo","Regras causais conhecidas + ruído controlado"],["02","Gerar trajetórias","Sₜ + Aₜ → Sₜ₊₁ + Rₜ em Parquet"],["03","Bloquear vazamento","Oracle fora do treino; split por cliente 70/15/15"],["04","Comparar modelos","Baseline antes do world model"],["05","Selecionar sem olhar o teste","Hiperparâmetros pela validação; teste uma vez"],["06","Simular e confrontar","Multi-step, contrafactuais e mudança de regime ainda a validar"]];
 steps.forEach((d,i)=>{const col=i%2,row=Math.floor(i/2),x=42+col*610,y=180+row*145;txt(s,d[0],x,y,55,40,18,true,C.blue);txt(s,d[1],x+70,y,490,40,23,true);txt(s,d[2],x+70,y+44,490,56,18,false,C.muted);line(s,x,y+112,550,C.rule,1);});
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/metodologia/preparacao-dataset-modelo.md`,`${SRC}/metodologia/treinamento-baseline-mlp.md`]);
}

// 7 — dataset preparation
{
 const s=base("Treinar o modelo exige reconstruir transições a partir dos dados transacionais",7);
 txt(s,"DADOS OPERACIONAIS",42,176,245,30,17,true,C.muted);
 txt(s,"Clientes",42,226,170,28,19,true);txt(s,"Apólices",42,268,170,28,19,true);txt(s,"Interações",42,310,170,28,19,true);txt(s,"Ofertas",42,352,170,28,19,true);txt(s,"Sinistros",42,394,170,28,19,true);
 line(s,235,240,120,C.rule,3);line(s,235,282,120,C.rule,3);line(s,235,324,120,C.rule,3);line(s,235,366,120,C.rule,3);line(s,235,408,120,C.rule,3);
 box(s,365,230,270,200,C.ink,"none",true);txt(s,"ORDENAR NO TEMPO\n+\nCONSTRUIR O ESTADO\n+\nASSOCIAR A AÇÃO",390,245,220,170,20,true,C.white,"center");
 txt(s,"↓",470,443,60,38,28,true,C.blue,"center");
 box(s,365,490,270,68,C.light,"none",true);txt(s,"Sₜ + Aₜ → Sₜ₊₁ + Rₜ",380,490,240,68,23,true,C.ink,"center");
 txt(s,"UMA LINHA DE TREINO",680,176,500,30,17,true,C.blue);
 const headers=["mês","Sₜ","Aₜ","produto / preço","Sₜ₊₁","Rₜ"];
 const widths=[60,110,100,120,110,60], startX=680, top=225;
 let x=startX; headers.forEach((h,i)=>{box(s,x,top,widths[i],45,C.ink,"none");txt(s,h,x+5,top,widths[i]-10,45,14,true,C.white,"center");x+=widths[i];});
 const rows=[
 ["jan","UNAWARE\nR$0","CONTACT\nBROKER","—","INTERESTED\nR$0","−5,00"],
 ["fev","INTERESTED\nR$0","OFFER\nPRODUCT","HOME\nR$55 • −17%","CUSTOMER\nR$45,65","+7,65"],
 ["mar","CUSTOMER\nR$45,65","SEND\nMESSAGE","—","INTERESTED\nR$45,65","−1,00"]];
 rows.forEach((row,r)=>{let xx=startX;row.forEach((v,i)=>{box(s,xx,top+45+r*78,widths[i],78,r===1?C.light:C.panel,C.white);txt(s,v,xx+5,top+45+r*78,widths[i]-10,78,14,i===0||i===5,C.ink,"center");xx+=widths[i];});});
 txt(s,"A linha completa preserva 32 campos: IDs, timestamp, estado observável, ação, probabilidades/eventos, próximo estado, reward e terminal.",680,520,520,62,17,false,C.muted);
 box(s,42,610,1158,42,C.panel,"none",true);txt(s,"Cuidados: usar apenas informação disponível em t • evitar vazamento • tratar categorias • normalizar números • dividir por cliente e/ou tempo",62,610,1118,42,17,true,C.ink,"center");
 notes(s,[`${SRC}/artifacts/insurance_trajectories.parquet`,`${SRC}/data/dataset.py`,`${SRC}/model/encoder.py`,`${SRC}/metodologia/preparacao-dataset-modelo.md`],"As três linhas exibidas são uma seleção de campos das três primeiras linhas reais do dataset sintético. O dataset original possui 32 colunas.");
}

// 8 — components architecture
{
 const s=base("O world model combina encoders separados, dinâmica latente e saídas especializadas",8);
 // connectors first
 line(s,205,310,110,C.blue,4); line(s,445,310,110,C.blue,4); line(s,685,310,110,C.blue,4); line(s,925,310,110,C.blue,4);
 const nodes=[
 [55,"Estado observável","idade • apólices • sinistros\nprêmio • engajamento • jornada"],
 [295,"State + Action\nEncoders","normalização + one-hot\nrepresentações separadas"],
 [535,"Dynamics Model","fusão dos latentes\ne transição aprendida"],
 [775,"Decoders","próximo estado • jornada\nreward • compra • cancelamento"],
 [1015,"Simulator","rollout mensal\n+ estatísticas agregadas"]];
 nodes.forEach((d,i)=>{box(s,d[0],220,190,180,i===2?C.ink:C.panel,"none",true);txt(s,d[1],d[0]+15,238,160,62,22,true,i===2?C.white:C.ink,"center");txt(s,d[2],d[0]+15,310,160,70,15,false,i===2?C.light:C.muted,"center");});
 pill(s,"PyTorch",110,465,130);pill(s,"scikit-learn",260,465,165);pill(s,"Pandas / Parquet",445,465,190);pill(s,"MLflow",655,465,125);pill(s,"FastAPI",800,465,130);pill(s,"pytest",950,465,110);
 txt(s,"O ambiente sintético gera a ground truth; o simulador da demo usa exclusivamente o checkpoint EXP‑005.",150,555,980,52,22,true,C.ink,"center");
 notes(s,[`${SRC}/model/world_model.py`,`${SRC}/model/encoder.py`,`${SRC}/simulation/simulator.py`,`${SRC}/api/app.py`,`${SRC}/requirements.txt`]);
}

// 9 — metrics chart
{
 const s=base("O EXP‑005 melhora transição, jornada e reward — mas a comparação exige nuance",9);
 s.charts.add("bar",{position:{left:45,top:190,width:690,height:410},categories:["Next-state RMSE\n(↓ melhor)","Reward MAE\n(↓ melhor)","Erro de jornada\n(↓ melhor)"],series:[{name:"Baseline EXP‑001",values:[6.806,2.845,13.039],fill:C.rule},{name:"World Model EXP‑005",values:[6.596,2.414,9.122],fill:C.blue}],hasLegend:true,legend:{position:"bottom",overlay:false,textStyle:{fontSize:14,fill:C.muted}},dataLabels:{showValue:true,position:"outEnd",textStyle:{fontSize:14,fill:C.ink,bold:true}},chartFill:C.white,chartLine:{style:"solid",width:0,fill:C.white},plotAreaFill:{type:"none"},plotAreaLine:{style:"solid",width:0,fill:C.white},xAxis:{textStyle:{fontSize:14,fill:C.muted},line:{style:"solid",width:1,fill:C.rule}},yAxis:{visible:false,majorGridlines:null},barOptions:{direction:"column",grouping:"clustered",gapWidth:85}});
 box(s,790,190,410,118,C.light,"none",true);txt(s,"+4,0 p.p.",815,205,360,50,32,true,C.blue);txt(s,"acurácia de jornada vs. baseline",815,253,360,34,17,false,C.muted);
 box(s,790,330,410,118,C.panel,"none",true);txt(s,"−15,1%",815,345,360,50,32,true,C.green);txt(s,"erro absoluto de reward vs. baseline",815,393,360,34,17,false,C.muted);
 txt(s,"Leitura correta",790,480,410,30,20,true,C.ink);txt(s,"Resultados held-out são promissores dentro do mesmo mundo sintético. Eles não demonstram desempenho com clientes reais nem robustez fora da distribuição.",790,520,410,105,19,false,C.muted);
 notes(s,[`${SRC}/artifacts/exp-001/test_metrics.json`,`${SRC}/artifacts/exp-005/test_metrics.json`],"Erro de jornada = 100% − acurácia. Valores calculados diretamente das métricas registradas.");
}

// 10 — decisions
{
 const s=base("As decisões tomadas reduziram risco de interpretação e de engenharia",10);
 const ds=[
 ["Baseline primeiro","Evita atribuir ao world model ganhos que uma MLP simples já entrega."],
 ["Oracle bloqueado","Variáveis latentes ficam disponíveis para ciência, não para treinar."],
 ["Split por cliente","A mesma trajetória individual não vaza entre treino, validação e teste."],
 ["Teste preservado","EXP‑003 escolhe candidatos pela validação e confirma apenas o vencedor."],
 ["Reward redefinido","Huber e maior peso reduziram erro sem declarar vitória total prematura."],
 ["Semântica da demo","“Trajetórias”, não “clientes impactados”; exposição, não receita realizada."],
 ["Métrica removida","Prêmio mensal ativo médio saiu porque induzia uma leitura de carteira."],
 ["Domínio fechado","Perfis, produtos, canais e preços limitados para evitar extrapolação silenciosa."]];
 ds.forEach((d,i)=>{const col=i%2,row=Math.floor(i/2),x=42+col*610,y=170+row*120;box(s,x,y,560,98,i===6?"#FCE8E8":C.panel,"none",true);txt(s,d[0],x+20,y+12,210,30,19,true,i===6?C.red:C.blue);txt(s,d[1],x+240,y+10,300,76,16,false,C.muted);});
 notes(s,[`${SRC}/README.md`,`${SRC}/artifacts/exp-003/optimization_report.json`,`${SRC}/api/app.py`,`Codex task: Criar ambiente sintético de seguros`]);
}

// 11 — overfitting
{
 const s=base("Overfitting aqui não é apenas memorizar linhas — é aprender o mundo que nós inventamos",11);
 txt(s,"Onde ele pode ocorrer",42,190,500,34,22,true,C.red);
 const risks=[["Ajuste ao dataset","Mesmo seed, regras e distribuição favorecem padrões repetidos."],["Ajuste à validação","Muitos ciclos de tuning transformam validação em teste informal."],["Ajuste ao simulador","Ótima fidelidade à v0.1 pode não transferir para o mundo real."],["Erro acumulado","Pequenos vieses one-step crescem em rollouts de 12–24 meses."]];
 risks.forEach((d,i)=>{const y=238+i*93;txt(s,"×",45,y,34,35,24,true,C.red,"center");txt(s,d[0],90,y,200,32,19,true);txt(s,d[1],295,y,275,58,16,false,C.muted);});
 box(s,650,190,550,390,C.ink,"none",true);txt(s,"Como controlar",685,220,470,40,24,true,C.white);
 const ctrls=["Holdout temporal e por coorte","Seeds, dinâmicas e populações novas","Teste de ações/preços não observados","Curvas de calibração por evento","Métrica por horizonte, não só one-step","Comparação contínua com baseline e oracle"];
 ctrls.forEach((d,i)=>{txt(s,String(i+1).padStart(2,"0"),685,282+i*44,42,30,15,true,C.light);txt(s,d,738,278+i*44,400,36,18,false,C.white);});
 txt(s,"Regra de decisão: nenhum resultado sintético deve ser traduzido diretamente em impacto comercial.",650,605,550,40,19,true,C.red,"center");
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/metodologia/treinamento-baseline-mlp.md`,`${SRC}/README.md`]);
}

// 12 — limitations
{
 const s=base("A demo é uma ferramenta de P&D; seus limites precisam acompanhar cada resultado",12);
 const left=["Sem dados reais ou validação externa","Sem causalidade comprovada no negócio","Sem incerteza epistemológica explícita","Sem sazonalidade robusta: apenas 12 meses","Sem teste concluído de mudança de regime","Reward sintético ≠ margem, receita ou LTV","Trajetórias ≠ número de clientes impactados"];
 txt(s,"O que não podemos afirmar",42,185,500,38,23,true,C.red);left.forEach((x,i)=>{txt(s,"—",45,240+i*48,30,30,18,true,C.red);txt(s,x,82,236+i*48,500,38,18,false,C.ink);});
 box(s,650,185,550,385,C.panel,"none",true);txt(s,"O que já podemos afirmar",685,215,480,38,23,true,C.blue);
 const right=["Pipeline reproduzível de ambiente → dados → treino → avaliação","Arquitetura explícita para estado, ação e dinâmica","Separação técnica entre ground truth e previsão","Métricas held-out e rastreamento de experimentos","Simulação multi-step fechada com checkpoint EXP‑005","Interface didática com linguagem e controles revisados"];
 right.forEach((x,i)=>{txt(s,"✓",685,272+i*47,30,30,18,true,C.green);txt(s,x,725,268+i*47,440,38,17,false,C.ink);});
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/README.md`,`${SRC}/simulation/README.md`]);
}

// 13 — ask / next steps
{
 const s=base("Próximo marco: transformar a prova técnica em evidência de generalização",13);
 const items=[["1","Versionar","Levar o código validado ao repo do projeto, com commits por experimento."],["2","Stress-test","Novas seeds, populações, preços e regras; medir degradação por horizonte."],["3","Contrafactuais","Mesmo estado inicial, ações alternativas, comparação com o oracle."],["4","Ponte para dados reais","Definir schema, governança, privacidade e protocolo de validação offline."]];
 items.forEach((d,i)=>{const y=180+i*100;txt(s,d[0],42,y,55,55,26,true,C.blue,"center");txt(s,d[1],115,y,230,40,23,true);txt(s,d[2],360,y,780,58,19,false,C.muted);line(s,115,y+75,1025,C.rule,1);});
 box(s,42,600,1158,52,C.light,"none",true);txt(s,"Decisão solicitada: aprovar o próximo ciclo de validação — não um uso produtivo do modelo.",65,600,1110,52,22,true,C.ink,"center");
 notes(s,[`${SRC}/PROJECT_SPEC.md`,`${SRC}/EXPERIMENTS.md`]);
}

await fs.mkdir(RENDER,{recursive:true});
for (const [i,slide] of deck.slides.items.entries()) {
  const png=await deck.export({slide,format:"png",scale:1});
  await fs.writeFile(`${RENDER}/slide-${String(i+1).padStart(2,"0")}.png`,new Uint8Array(await png.arrayBuffer()));
  const layout=await slide.export({format:"layout"});
  await fs.writeFile(`${RENDER}/slide-${String(i+1).padStart(2,"0")}.layout.json`,await layout.text());
}
const montage=await deck.export({format:"webp",montage:true,scale:1});
await fs.writeFile(`${RENDER}/montage.webp`,new Uint8Array(await montage.arrayBuffer()));
const pptx=await PresentationFile.exportPptx(deck); await pptx.save(OUT);
