from dataclasses import dataclass
from typing import Optional
from frostline.analyzer.query import QueryProfile, Complexity
from frostline.router.warehouse import WarehouseRecommendation, WarehouseSize
from frostline.router.feedback import PerformanceRecord

BASELINE_SECONDS = {
    Complexity.SIMPLE: 2.0,
    Complexity.MODERATE: 5.0,
    Complexity.COMPLEX: 15.0,
    Complexity.HEAVY: 45.0,
}

MIN_BILLING_SECONDS = 60.0

@dataclass(frozen=True)
class CostEstimate:
    estimated_seconds: float
    estimated_credits: float
    warehouse_size: WarehouseSize
    credits_per_hour: float
    used_feedback: bool

def estimate_cost(
    profile: QueryProfile,
    recommendation: WarehouseRecommendation,
    warm: bool = True,
    feedback: Optional[PerformanceRecord] = None,
) -> CostEstimate:
    if feedback and feedback.sample_count >= 3:
        seconds = feedback.avg_latency_s
        used_feedback = True
    else:
        seconds = BASELINE_SECONDS[profile.complexity]
        used_feedback = False
    if not warm:
        seconds = max(seconds, MIN_BILLING_SECONDS)

    credits = (recommendation.credits_per_hour / 3600) * seconds

    return CostEstimate(
        estimated_seconds=seconds,
        estimated_credits=round(credits, 6),
        warehouse_size=recommendation.size,
        credits_per_hour=recommendation.credits_per_hour,
        used_feedback=used_feedback,
    )