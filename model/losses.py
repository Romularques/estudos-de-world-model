import torch.nn.functional as F

def baseline_loss(prediction, next_numeric, next_journey, reward, state_weight: float = 1.0, journey_weight: float = 1.0, reward_weight: float = 1.0, reward_loss: str = "mse", purchased=None, cancelled=None, purchase_weight: float = 0.0, cancellation_weight: float = 0.0):
    """Mixed target loss: MSE for numeric state/reward and CE for journey."""
    reward_error = F.huber_loss(prediction["reward"].squeeze(1), reward, delta=1.0) if reward_loss == "huber" else F.mse_loss(prediction["reward"].squeeze(1), reward)
    total = (state_weight * F.mse_loss(prediction["next_numeric"], next_numeric)
            + journey_weight * F.cross_entropy(prediction["next_journey"], next_journey)
            + reward_weight * reward_error)
    if purchased is not None and "purchase_logit" in prediction:
        total = total + purchase_weight * F.binary_cross_entropy_with_logits(prediction["purchase_logit"], purchased)
    if cancelled is not None and "cancellation_logit" in prediction:
        total = total + cancellation_weight * F.binary_cross_entropy_with_logits(prediction["cancellation_logit"], cancelled)
    return total
