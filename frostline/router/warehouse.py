from enum import Enum
from dataclasses import dataclass
from frostline.analyzer.query import QueryProfile, Complexity

class WarehouseSize(Enum):
    XSMALL = "XSMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"

@dataclass(frozen=True)
class WarehouseRecommendation:
    size: WarehouseSize
    name: str
    credits_per_hour: float
    reason: str

CREDITS = {
    WarehouseSize.XSMALL: 1.0,
    WarehouseSize.SMALL: 2.0,
    WarehouseSize.MEDIUM: 4.0,
    WarehouseSize.LARGE: 8.0,
}

SIZE_MAP = {
    Complexity.SIMPLE: WarehouseSize.XSMALL,
    Complexity.MODERATE: WarehouseSize.SMALL,
    Complexity.COMPLEX: WarehouseSize.MEDIUM,
    Complexity.HEAVY: WarehouseSize.LARGE,
}

SIZE_ORDER = [WarehouseSize.XSMALL, WarehouseSize.SMALL,
              WarehouseSize.MEDIUM, WarehouseSize.LARGE]

DOWNSIZE_LATENCY_THRESHOLD = 3.0
DOWNSIZE_MIN_SAMPLES = 5


def _one_size_down(size: WarehouseSize):
    idx = SIZE_ORDER.index(size)
    return SIZE_ORDER[idx - 1] if idx > 0 else None

def recommend_warehouse(profile: QueryProfile, feedback=None) -> WarehouseRecommendation:
    size = SIZE_MAP[profile.complexity]
    downsized = False

    if feedback and feedback.sample_count >= DOWNSIZE_MIN_SAMPLES:
        if feedback.avg_latency_s < DOWNSIZE_LATENCY_THRESHOLD:
            smaller = _one_size_down(size)
            if smaller is not None:
                size = smaller
                downsized = True

    parts = [profile.complexity.value.upper()]
    if profile.join_count:
        parts.append(f"{profile.join_count} join(s)")
    if profile.has_group_by:
        parts.append("GROUP BY")
    if profile.has_subquery:
        parts.append("subquery")
    parts.append(f"{profile.table_count} table(s)")
    if downsized:
        parts.append("downsized via feedback")

    return WarehouseRecommendation(
        size=size,
        name="FROSTLINE_WH",
        credits_per_hour=CREDITS[size],
        reason=", ".join(parts),
    )