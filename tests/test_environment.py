import math
from environment import Action, ActionType, Channel, InsuranceEnvironment, JourneyStage, Product

def test_initial_state_is_valid():
    state = InsuranceEnvironment(42).initial_state()
    assert state.age >= 18 and 0 <= state.trust <= 1

def test_offer_requires_fields():
    try: Action(action_type=ActionType.OFFER_PRODUCT)
    except ValueError: return
    assert False, "invalid offer must fail"

def test_step_is_valid_and_numeric():
    env = InsuranceEnvironment(42); state = env.initial_state()
    nxt, reward, info = env.step(state, Action(action_type=ActionType.OFFER_PRODUCT, product=Product.HOME, price=50, channel=Channel.APP, discount=.1))
    assert math.isfinite(reward) and nxt.journey_stage in JourneyStage and 0 <= info["purchase_probability"] <= 1

def test_latent_fields_are_hidden_by_default():
    state = InsuranceEnvironment(1).initial_state()
    assert "trust" not in state.observable() and "trust" in state.observable(True)
