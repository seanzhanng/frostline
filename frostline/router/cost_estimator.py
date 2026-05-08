from dataclasses import dataclass
from frostline.analyzer.query import QueryProfile, Complexity
from frostline.router.warehouse import WarehouseRecommendation, WarehouseSize

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

def estimate_cost(
    profile: QueryProfile,
    recommendation: WarehouseRecommendation,
    warm: bool = True,
) -> CostEstimate:
    seconds = BASELINE_SECONDS[profile.complexity]
    if not warm:
        seconds = max(seconds, MIN_BILLING_SECONDS)

    credits = (recommendation.credits_per_hour / 3600) * seconds

    return CostEstimate(
        estimated_seconds=seconds,
        estimated_credits=round(credits, 6),
        warehouse_size=recommendation.size,
        credits_per_hour=recommendation.credits_per_hour,
    )