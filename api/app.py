"""Local closed-domain UI for inspecting EXP-005 scenario simulations."""
from __future__ import annotations
from functools import lru_cache
from html import escape
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from simulation.simulator import CADENCES, CHANNELS, CLOSED_PROFILES, PRODUCTS, ProductStrategy, Scenario, WorldModelSimulator

app = FastAPI(title="Insurance World Simulator", version="0.1")

@lru_cache
def simulator() -> WorldModelSimulator:
    return WorldModelSimulator("artifacts/exp-005")

def options(values, selected=None):
    return "".join(f'<option value="{escape(value)}" {"selected" if value == selected else ""}>{escape(value.replace("_", " "))}</option>' for value in values)

def help_tip(text: str) -> str:
    return f'<span class="help-wrap"><button type="button" class="help" aria-label="Explicação" aria-expanded="false">?</button><span class="tooltip" role="tooltip">{escape(text)}</span></span>'

def metric(value: str, title: str, explanation: str) -> str:
    return f'<article><strong>{value}</strong><span>{escape(title)} {help_tip(explanation)}</span></article>'

def page(result: dict | None = None, error: str | None = None, values: dict | None = None) -> str:
    defaults = {"profile": "AUTO_CUSTOMER", "product": "HOME", "channel": "BROKER", "price": "55", "discount": "0.10", "cadence": "ONCE", "horizon_months": "12", "simulations": "100", "seed": "42"}
    values = {**defaults, **(values or {})}
    results = ""
    if result:
        summary = result["summary"]
        rows = "".join(f"<tr><td>{item['simulation_id'] + 1}</td><td>{item['total_reward']:.2f}</td><td>{item['final_state']['journey_stage']}</td><td>R$ {item['final_state']['premium_monthly']:.2f}</td><td>{'Sim' if item['terminated'] else 'Não'}</td></tr>" for item in result["sample_trajectories"])
        cards = "".join((
            metric(f'{summary["success_rate"]:.1%}', "Índice de sucesso — por trajetória no período", "Percentual de trajetórias em que o perfil aderiu ao produto ofertado e permaneceu com esse produto ativo ao final do período."),
            metric(f'{summary["purchase_at_least_once"]:.1%}', "Adesão ao produto — por trajetória no período", "Percentual de trajetórias em que houve adesão ao produto ofertado pelo menos uma vez no horizonte."),
            metric(f'{summary["target_product_active_at_horizon"]:.1%}', "Produto ativo ao final — por trajetória", "Percentual de trajetórias que terminou o período com o produto configurado ativo."),
            metric(f'{summary["cancellation_at_least_once"]:.1%}', "Cancelamento — por trajetória no período", "Percentual de trajetórias que teve um cancelamento de apólice em algum mês do horizonte."),
            metric(f'{summary["active_months_mean"]:.1f}', "Meses ativos médios — por trajetória no período", "Número médio de meses em que a trajetória permaneceu com alguma apólice ativa durante o horizonte."),
            metric(f'R$ {summary["premium_exposure"]:.2f}', "Exposição de prêmio projetada — por trajetória no período", "Soma do prêmio mensal previsto nos meses ativos de cada trajetória. É uma projeção de exposição, não receita realizada nem quantidade de clientes."),
            metric(f'{summary["expected_total_reward"]:.2f}', "Recompensa (Reward) — por trajetória no período", "Indicador sintético do ambiente: prêmio efetivo da oferta menos custo sintético do produto e custo de aquisição; ações sem conversão e cancelamentos recebem penalidades. Não representa receita, margem ou LTV real."),
        ))
        results = f'''<section class="results"><h2>Resultado do cenário — {result["model"]}</h2><p class="sub">Cada simulação é uma trajetória futura possível do mesmo perfil configurado; não representa um cliente adicional ou o tamanho de uma carteira. O índice de sucesso resume adesão seguida de permanência do produto ao fim do horizonte.</p><div class="metrics">{cards}</div>
<p class="note">Após adesão, o produto deixa de receber novas ofertas. Cancelamento encerra a trajetória. Resultados amostrados pelo World Model EXP-005; não são a ground truth do ambiente.</p><h3>Amostra de trajetórias (1 a {len(result["sample_trajectories"])})</h3><table><thead><tr><th>Simulação</th><th>Recompensa (Reward)</th><th>Jornada final</th><th>Prêmio final</th><th>Encerrada</th></tr></thead><tbody>{rows}</tbody></table></section>'''
    message = f'<p class="error">{escape(error)}</p>' if error else ""
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Insurance World Simulator</title><style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;background:#f7f8fa;color:#20242a}}h1{{margin-bottom:4px}}h3{{margin:24px 0 10px}}.sub,.note{{color:#5b6572}}form{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;background:white;padding:22px;border:1px solid #dce1e7;border-radius:8px}}label{{display:grid;gap:6px;font-size:14px;font-weight:600}}.label-title{{display:flex;align-items:center;gap:5px}}input,select,button{{padding:9px;border:1px solid #aeb8c4;border-radius:5px;font:inherit}}button{{background:#1455a3;color:white;border:0;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;min-height:40px}}button:disabled{{opacity:.75;cursor:wait}}.help-wrap{{position:relative;display:inline-flex}}button.help{{display:inline-flex;min-height:18px;width:18px;padding:0;border:1px solid #607184;border-radius:50%;background:white;color:#314356;font-size:12px;line-height:1;cursor:pointer}}.tooltip{{display:none;position:absolute;z-index:2;top:24px;left:-8px;width:240px;max-width:calc(100vw - 24px);padding:10px;border:1px solid #aeb8c4;border-radius:6px;background:#263746;color:white;font-size:12px;font-weight:400;line-height:1.35;box-shadow:0 3px 10px #0003}}.tooltip.align-right{{left:auto;right:-8px}}.tooltip.visible{{display:block}}.spinner{{display:none;width:14px;height:14px;border:2px solid rgba(255,255,255,.45);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite}}button.loading .spinner{{display:inline-block}}@keyframes spin{{to{{transform:rotate(360deg)}}}}.results{{margin-top:24px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}article{{background:white;border:1px solid #dce1e7;border-radius:8px;padding:14px;display:grid;gap:6px}}article strong{{font-size:19px}}article span{{font-size:12px;color:#5b6572;display:flex;align-items:center;gap:4px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #dce1e7}}.error{{color:#a41e22;font-weight:600}}@media(max-width:800px){{form,.metrics{{grid-template-columns:1fr 1fr}}}}</style></head><body>
<h1>Insurance World Simulator</h1><p class="sub">Cenários de produto por parâmetros fechados — modelo selecionado: EXP-005.</p>{message}
<form action="/simulate" method="get" id="scenario-form"><label><span class="label-title">Perfil do cliente {help_tip("Perfil fechado que representa o ponto de partida da trajetória simulada.")}</span><select name="profile">{options(CLOSED_PROFILES.keys(), values["profile"])}</select></label><label><span class="label-title">Produto {help_tip("Produto de seguro que será ofertado ao perfil escolhido.")}</span><select name="product">{options(PRODUCTS, values["product"])}</select></label><label><span class="label-title">Canal {help_tip("Canal utilizado para realizar a oferta: aplicativo, e-mail, corretor ou central de atendimento.")}</span><select name="channel">{options(CHANNELS, values["channel"])}</select></label><label><span class="label-title">Preço (R$) {help_tip("Prêmio mensal proposto para o produto, antes de aplicar o desconto configurado.")}</span><input name="price" type="number" min="20" max="250" step="0.01" value="{escape(str(values["price"]))}"></label><label><span class="label-title">Desconto (0 a 0,50) {help_tip("Redução aplicada ao preço. Exemplo: 0,15 representa 15% de desconto.")}</span><input name="discount" type="number" min="0" max="0.5" step="0.01" value="{escape(str(values["discount"]))}"></label><label><span class="label-title">Cadência {help_tip("ONCE faz uma oferta no primeiro mês. MONTHLY pode repetir a oferta mensalmente até a adesão.")}</span><select name="cadence">{options(CADENCES, values["cadence"])}</select></label><label><span class="label-title">Horizonte (meses) {help_tip("Quantidade de meses projetados em cada trajetória.")}</span><input name="horizon_months" type="number" min="1" max="24" value="{escape(str(values["horizon_months"]))}"></label><label><span class="label-title">Simulações {help_tip("Número de trajetórias futuras possíveis do mesmo perfil. Não representa número de clientes. Mais trajetórias reduzem a variação amostral, mas levam mais tempo.")}</span><input name="simulations" type="number" min="10" max="1000" value="{escape(str(values["simulations"]))}"></label><label><span class="label-title">Seed {help_tip("Número que controla a aleatoriedade. Com a mesma seed e configuração, o resultado se repete.")}</span><input name="seed" type="number" value="{escape(str(values["seed"]))}"></label><button type="submit" id="simulate-button"><span class="spinner" aria-hidden="true"></span><span class="button-label">Simular cenário</span></button></form>{results}<script>document.getElementById('scenario-form').addEventListener('submit', function() {{ const button=document.getElementById('simulate-button'); button.classList.add('loading'); button.disabled=true; button.querySelector('.button-label').textContent='Simulando...'; }}); document.querySelectorAll('.help').forEach(function(button) {{ button.addEventListener('click', function(event) {{ event.preventDefault(); const tooltip=button.nextElementSibling; const open=!tooltip.classList.contains('visible'); document.querySelectorAll('.tooltip.visible').forEach(function(item) {{ item.classList.remove('visible'); item.classList.remove('align-right'); }}); document.querySelectorAll('.help[aria-expanded="true"]').forEach(function(item) {{ item.setAttribute('aria-expanded', 'false'); }}); if (open) {{ tooltip.classList.add('visible'); if (tooltip.getBoundingClientRect().right > window.innerWidth - 12) {{ tooltip.classList.add('align-right'); }} button.setAttribute('aria-expanded', 'true'); }} }}); }});</script></body></html>'''

@app.get("/", response_class=HTMLResponse)
def home(): return page()

@app.get("/simulate", response_class=HTMLResponse)
def simulate(profile: str, product: str, price: float, channel: str, discount: float, cadence: str, horizon_months: int, simulations: int, seed: int = 42):
    values = {"profile": profile, "product": product, "price": price, "channel": channel, "discount": discount, "cadence": cadence, "horizon_months": horizon_months, "simulations": simulations, "seed": seed}
    try:
        scenario = Scenario(profile=profile, strategy=ProductStrategy(product=product, price=price, channel=channel, discount=discount, cadence=cadence), horizon_months=horizon_months, simulations=simulations, seed=seed)
        return page(simulator().simulate(scenario), values=values)
    except Exception as exc:
        return page(error=str(exc), values=values)

@app.get("/health")
def health(): return {"status": "ok", "model": "EXP-005", "profiles": list(CLOSED_PROFILES)}
