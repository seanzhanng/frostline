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

def recommend_warehouse(profile: QueryProfile) -> WarehouseRecommendation:
    size = SIZE_MAP[profile.complexity]

    parts = [profile.complexity.value.upper()]
    if profile.join_count:
        parts.append(f"{profile.join_count} join(s)")
    if profile.has_group_by:
        parts.append("GROUP BY")
    if profile.has_subquery:
        parts.append("subquery")
    parts.append(f"{profile.table_count} table(s)")

    return WarehouseRecommendation(
        size=size,
        name="FROSTLINE_WH",
        credits_per_hour=CREDITS[size],
        reason=", ".join(parts),
    )