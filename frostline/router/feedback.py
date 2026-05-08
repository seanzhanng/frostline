from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional
from frostline.connectors.postgres import get_connection
from frostline.config import PostgresConfig

logger = logging.getLogger(__name__)

DEFAULT_ALPHA = 0.3

@dataclass(frozen=True)
class PerformanceRecord:
    query_hash: str
    warehouse_size: str
    avg_latency_s: float
    avg_cost: float
    sample_count: int

class FeedbackStore:
    def __init__(self, alpha: float = DEFAULT_ALPHA):
        self.alpha = alpha
        self._pg_cfg = PostgresConfig.from_env()

    def lookup(self, query_hash: str, warehouse_size: str) -> Optional[PerformanceRecord]:
        conn = get_connection(self._pg_cfg)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT query_hash, warehouse_size, avg_latency_s,
                           avg_cost, sample_count
                    FROM query_performance_history
                    WHERE query_hash = %s AND warehouse_size = %s
                    """,
                    (query_hash, warehouse_size),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return PerformanceRecord(
                    query_hash=row[0],
                    warehouse_size=row[1],
                    avg_latency_s=row[2],
                    avg_cost=row[3],
                    sample_count=row[4],
                )
        finally:
            conn.close()

    def update(
        self,
        query_hash: str,
        warehouse_size: str,
        actual_latency_s: float,
        actual_cost: float,
    ) -> None:
        existing = self.lookup(query_hash, warehouse_size)
        conn = get_connection(self._pg_cfg)
        try:
            with conn.cursor() as cur:
                if existing is None:
                    cur.execute(
                        """
                        INSERT INTO query_performance_history
                            (query_hash, warehouse_size, avg_latency_s,
                             avg_cost, sample_count, last_updated)
                        VALUES (%s, %s, %s, %s, 1, NOW())
                        """,
                        (query_hash, warehouse_size,
                         actual_latency_s, actual_cost),
                    )
                else:
                    new_latency = (
                        self.alpha * actual_latency_s
                        + (1 - self.alpha) * existing.avg_latency_s
                    )
                    new_cost = (
                        self.alpha * actual_cost
                        + (1 - self.alpha) * existing.avg_cost
                    )
                    cur.execute(
                        """
                        UPDATE query_performance_history
                        SET avg_latency_s = %s,
                            avg_cost      = %s,
                            sample_count  = sample_count + 1,
                            last_updated  = NOW()
                        WHERE query_hash = %s AND warehouse_size = %s
                        """,
                        (new_latency, new_cost,
                         query_hash, warehouse_size),
                    )
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()