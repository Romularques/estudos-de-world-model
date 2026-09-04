import pytest
from pydantic import ValidationError
from simulation.simulator import ProductStrategy, Scenario, WorldModelSimulator
from api.app import page

def test_closed_domain_rejects_invalid_scenario():
    with pytest.raises(ValidationError):
        Scenario(profile="UNKNOWN", strategy=ProductStrategy(product="HOME", price=55, channel="BROKER", discount=.1))
    with pytest.raises(ValidationError):
        ProductStrategy(product="BOAT", price=55, channel="BROKER", discount=.1)

def test_exp005_simulator_returns_bounded_scenario_summary():
    scenario = Scenario(profile="AUTO_CUSTOMER", strategy=ProductStrategy(product="HOME", price=55, channel="BROKER", discount=.1), horizon_months=1, simulations=10, seed=42)
    result = WorldModelSimulator().simulate(scenario)
    assert result["model"] == "EXP-005" and len(result["sample_trajectories"]) == 10
    summary = result["summary"]
    assert 0 <= summary["purchase_at_least_once"] <= 1
    assert 0 <= summary["cancellation_at_least_once"] <= 1
    assert 0 <= summary["purchase_monthly_rate"] <= 1
    assert 0 <= summary["cancellation_monthly_rate"] <= 1
    assert 0 <= summary["success_rate"] <= summary["purchase_at_least_once"]
    assert 0 <= summary["target_product_active_at_horizon"] <= 1
    for trajectory in result["sample_trajectories"]:
        purchased = False
        for index, step in enumerate(trajectory["steps"]):
            if purchased:
                assert not step["offered"]
            purchased = purchased or step["purchased"]
            if step["cancelled"]:
                assert index == len(trajectory["steps"]) - 1
                assert trajectory["terminated"]

def test_ui_keeps_submitted_values_and_has_loading_spinner():
    html = page(values={"profile": "DIGITAL_PROSPECT", "product": "LIFE", "channel": "APP", "price": "88.5", "discount": ".2", "cadence": "MONTHLY", "horizon_months": "6", "simulations": "25", "seed": "7"})
    assert 'option value="DIGITAL_PROSPECT" selected' in html
    assert 'value="88.5"' in html and 'value="25"' in html
    assert 'class="spinner"' in html and "Simulando..." in html

def test_ui_explains_incremental_business_metrics():
    scenario = Scenario(profile="DIGITAL_PROSPECT", strategy=ProductStrategy(product="LIFE", price=55, channel="APP", discount=.1), horizon_months=1, simulations=10, seed=42)
    html = page(WorldModelSimulator().simulate(scenario))
    assert "Índice de sucesso" in html
    assert "Exposição de prêmio projetada" in html
    assert "Recompensa (Reward)" in html
    assert 'class="help"' in html
    assert "por trajetória" in html
    assert "por cliente" not in html
    assert "Prêmio mensal ativo médio" not in html
    assert "tooltip.align-right" in html
    assert "getBoundingClientRect().right" in html

def test_simulation_does_not_create_policy_without_purchase():
    scenario = Scenario(profile="DIGITAL_PROSPECT", strategy=ProductStrategy(product="LIFE", price=55, channel="APP", discount=.1), horizon_months=2, simulations=10, seed=42)
    result = WorldModelSimulator().simulate(scenario)
    for trajectory in result["sample_trajectories"]:
        if not trajectory["any_purchase"]:
            assert not trajectory["target_product_active_at_horizon"]
