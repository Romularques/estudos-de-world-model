import torch
from data.generate_dataset import generate
from model.encoder import JOURNEY, build_action_preprocessor, build_preprocessor, build_state_preprocessor, customer_split, targets
from model.world_model import BaselineMLP, InsuranceWorldModel
from model.losses import baseline_loss
from training.optimize_world_model import _ranked

def test_customer_split_has_no_leakage_and_public_features(tmp_path):
    frame, _ = generate(24, 2, 7, tmp_path / "dataset.parquet")
    train, valid, test = customer_split(frame, 42)
    assert not (set(train.customer_id) & set(valid.customer_id))
    assert not (set(train.customer_id) & set(test.customer_id))
    assert "state_trust" not in frame.columns
    features = build_preprocessor().fit_transform(train)
    numeric, journey, reward = targets(train)
    assert features.shape[0] == numeric.shape[0] == journey.shape[0] == reward.shape[0]

def test_baseline_outputs_all_prediction_heads():
    model = BaselineMLP(12, 8, len(JOURNEY), 16)
    output = model(torch.zeros((3, 12)))
    assert output["next_numeric"].shape == (3, 8)
    assert output["next_journey"].shape == (3, len(JOURNEY))
    assert output["reward"].shape == (3, 1)

def test_world_model_has_separate_state_action_and_dynamics_path(tmp_path):
    frame, _ = generate(12, 2, 7, tmp_path / "world.parquet")
    state = build_state_preprocessor().fit_transform(frame).astype("float32")
    action = build_action_preprocessor().fit_transform(frame).astype("float32")
    model = InsuranceWorldModel(state.shape[1], action.shape[1], 8, len(JOURNEY), hidden_dim=16)
    output = model(torch.tensor(state[:2]), torch.tensor(action[:2]))
    assert output["next_numeric"].shape == (2, 8)
    assert output["next_journey"].shape == (2, len(JOURNEY))
    assert output["latent_state"].shape[0] == output["predicted_latent_state"].shape[0] == 2

def test_optimizer_ranks_mixed_metrics_without_combining_units():
    candidates = [
        {"name": "a", "validation_metrics": {"journey_accuracy": .9, "reward_mae": 3., "next_state_rmse": 8.}},
        {"name": "b", "validation_metrics": {"journey_accuracy": .8, "reward_mae": 2., "next_state_rmse": 7.}},
    ]
    assert _ranked(candidates)[0]["name"] == "b"

def test_world_model_residual_and_huber_reward_loss_are_supported():
    model = InsuranceWorldModel(10, 4, 8, len(JOURNEY), hidden_dim=16, residual_numeric=True)
    prediction = model(torch.zeros((2, 10)), torch.zeros((2, 4)))
    loss = baseline_loss(prediction, torch.zeros((2, 8)), torch.zeros(2, dtype=torch.long), torch.tensor([0.0, 8.0]), reward_loss="huber")
    assert model.state_skip is not None and torch.isfinite(loss)

def test_world_model_event_heads_are_outputs_not_inputs():
    model = InsuranceWorldModel(10, 4, 8, len(JOURNEY), hidden_dim=16, event_heads=True)
    prediction = model(torch.zeros((2, 10)), torch.zeros((2, 4)))
    loss = baseline_loss(prediction, torch.zeros((2, 8)), torch.zeros(2, dtype=torch.long), torch.zeros(2), purchased=torch.tensor([1.0, 0.0]), cancelled=torch.tensor([0.0, 1.0]), purchase_weight=.5, cancellation_weight=.5)
    assert prediction["purchase_logit"].shape == prediction["cancellation_logit"].shape == (2,)
    assert torch.isfinite(loss)
