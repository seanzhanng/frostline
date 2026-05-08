import time
import hashlib
from dataclasses import dataclass
from typing import Optional
from frostline.config import SnowflakeConfig, PostgresConfig
from frostline.analyzer.query import analyze_query, QueryProfile
from frostline.router.warehouse import recommend_warehouse, WarehouseRecommendation
from frostline.router.cost_estimator import estimate_cost, CostEstimate
from frostline.router.feedback import FeedbackStore
from frostline.connectors.snowflake import get_connection as sf_connect, execute_query as sf_execute
from frostline.connectors.postgres import get_connection as pg_connect, execute_query as pg_execute

feedback_store = FeedbackStore()

@dataclass(frozen=True)
class ExecutionResult:
    profile: QueryProfile
    recommendation: WarehouseRecommendation
    estimate: CostEstimate
    rows_returned: int
    latency_ms: float
    actual_credits: float
    status: str
    error_message: Optional[str]

def execute_routed_query(sql: str, dry_run: bool = False, warm: bool = True) -> ExecutionResult:
    profile = analyze_query(sql)
    query_hash = hashlib.md5(sql.encode()).hexdigest()

    from frostline.router.warehouse import SIZE_MAP
    default_size = SIZE_MAP[profile.complexity]
    feedback = feedback_store.lookup(query_hash, default_size.value)
    rec = recommend_warehouse(profile, feedback=feedback)
    cost_feedback = feedback
    if rec.size != default_size:
        cost_feedback = feedback_store.lookup(query_hash, rec.size.value)
    est = estimate_cost(profile, rec, warm=warm, feedback=cost_feedback)

    if dry_run:
        return ExecutionResult(
            profile=profile,
            recommendation=rec,
            estimate=est,
            rows_returned=0,
            latency_ms=0.0,
            actual_credits=0.0,
            status="dry_run",
            error_message=None,
        )

    sf_cfg = SnowflakeConfig.from_env()
    pg_cfg = PostgresConfig.from_env()

    status = "success"
    error_message = None
    rows_returned = 0
    latency_ms = 0.0
    actual_credits = 0.0

    try:
        conn = sf_connect(sf_cfg)
        sf_execute(conn, f"ALTER WAREHOUSE {rec.name} SET WAREHOUSE_SIZE = '{rec.size.value}'")
        start = time.perf_counter()
        results = sf_execute(conn, sql)
        elapsed = time.perf_counter() - start
        latency_ms = round(elapsed * 1000, 2)
        rows_returned = len(results) if results else 0
        actual_credits = round((rec.credits_per_hour / 3600) * elapsed, 6)
        conn.close()
    except Exception as e:
        status = "error"
        error_message = str(e)

    try:
        pg_conn = pg_connect(pg_cfg)
        pg_execute(pg_conn, """
            INSERT INTO query_log (
                query_text, query_hash, complexity, warehouse_used,
                warehouse_size, estimated_cost, actual_cost,
                latency_ms, rows_returned, status, error_message
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, params=(
            sql, query_hash, profile.complexity.value, rec.name,
            rec.size.value, est.estimated_credits, actual_credits,
            latency_ms, rows_returned, status, error_message,
        ))
        pg_conn.close()
    except Exception:
        pass

    if status == "success":
        try:
            feedback_store.update(
                query_hash=query_hash,
                warehouse_size=rec.size.value,
                actual_latency_s=latency_ms / 1000,
                actual_cost=actual_credits,
            )
        except Exception:
            pass

    return ExecutionResult(
        profile=profile,
        recommendation=rec,
        estimate=est,
        rows_returned=rows_returned,
        latency_ms=latency_ms,
        actual_credits=actual_credits,
        status=status,
        error_message=error_message,
    )