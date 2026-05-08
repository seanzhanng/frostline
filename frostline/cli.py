import click
import time
import hashlib
from frostline.config import SnowflakeConfig, PostgresConfig
from frostline.analyzer.query import analyze_query
from frostline.router.warehouse import recommend_warehouse
from frostline.router.cost_estimator import estimate_cost
from frostline.connectors.snowflake import get_connection as sf_connect, execute_query as sf_execute
from frostline.connectors.postgres import get_connection as pg_connect, execute_query as pg_execute

@click.command()
@click.argument("sql")
@click.option("--dry-run", is_flag=True, help="Analyze and estimate only, no execution.")
@click.option("--warm/--cold", default=True, help="Warehouse warm/cold for cost estimate.")
def route(sql, dry_run, warm):
    """Analyze, route, estimate, and optionally execute a SQL query."""

    profile = analyze_query(sql)
    click.echo(f"\n--- Query Analysis ---")
    click.echo(f"Complexity: {profile.complexity.value}")
    click.echo(f"Tables: {profile.table_count}")
    click.echo(f"Joins: {profile.join_count}")
    click.echo(f"Group By: {profile.has_group_by}")
    click.echo(f"Subquery: {profile.has_subquery}")

    rec = recommend_warehouse(profile)
    click.echo(f"\n--- Warehouse ---")
    click.echo(f"Size: {rec.size.value}")
    click.echo(f"Credits/hr: {rec.credits_per_hour}")
    click.echo(f"Reason: {rec.reason}")

    est = estimate_cost(profile, rec, warm=warm)
    click.echo(f"\n--- Cost Estimate ---")
    click.echo(f"Est. time: {est.estimated_seconds}s")
    click.echo(f"Est. cost: {est.estimated_credits} credits")

    if dry_run:
        click.echo("\n[dry run — skipping execution]")
        return

    if not click.confirm("\nExecute?"):
        return

    query_hash = hashlib.md5(sql.encode()).hexdigest()
    sf_cfg = SnowflakeConfig.from_env()
    pg_cfg = PostgresConfig.from_env()

    status = "success"
    error_message = None
    rows_returned = 0
    actual_credits = 0.0
    latency_ms = 0.0

    try:
        conn = sf_connect(sf_cfg)

        sf_execute(conn, f"ALTER WAREHOUSE {rec.name} SET WAREHOUSE_SIZE = '{rec.size.value}'")

        start = time.perf_counter()
        results = sf_execute(conn, sql)
        elapsed = time.perf_counter() - start

        latency_ms = round(elapsed * 1000, 2)
        rows_returned = len(results) if results else 0
        actual_credits = round((rec.credits_per_hour / 3600) * elapsed, 6)

        click.echo(f"\n--- Results ---")
        click.echo(f"Rows       : {rows_returned}")
        click.echo(f"Latency    : {latency_ms}ms")
        click.echo(f"Act. cost  : {actual_credits} credits")
        click.echo(f"Est. cost  : {est.estimated_credits} credits")

        conn.close()
    except Exception as e:
        status = "error"
        error_message = str(e)
        click.echo(f"\n[error] {error_message}")

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
        click.echo("[logged to postgres]")
    except Exception as e:
        click.echo(f"[logging failed] {e}")

if __name__ == "__main__":
    route()