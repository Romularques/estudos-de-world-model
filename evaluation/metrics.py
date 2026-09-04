from __future__ import annotations
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score
from model.encoder import JOURNEY, NEXT_NUMERIC

def evaluate_predictions(actual_numeric, predicted_numeric, actual_journey, predicted_journey, actual_reward, predicted_reward) -> dict:
    metrics = {"next_state_rmse": float(mean_squared_error(actual_numeric, predicted_numeric) ** .5),
               "journey_accuracy": float(accuracy_score(actual_journey, predicted_journey)),
               "reward_mae": float(mean_absolute_error(actual_reward, predicted_reward)),
               "reward_rmse": float(mean_squared_error(actual_reward, predicted_reward) ** .5)}
    for index, column in enumerate(NEXT_NUMERIC):
        metrics[f"mae_{column.removeprefix('next_state_')}"] = float(mean_absolute_error(actual_numeric[:, index], predicted_numeric[:, index]))
    return metrics


def event_metrics(actual, probabilities, prefix: str) -> dict:
    labels = (probabilities >= .5).astype(int)
    return {f"{prefix}_accuracy": float(accuracy_score(actual, labels)),
            f"{prefix}_brier": float(np.mean((probabilities - actual) ** 2)),
            f"{prefix}_rate": float(np.mean(actual))}
