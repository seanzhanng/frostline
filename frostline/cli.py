import click
from frostline.executor import execute_routed_query

@click.command()
@click.argument("sql")
@click.option("--dry-run", is_flag=True)
@click.option("--warm/--cold", default=True)
def route(sql, dry_run, warm):
    result = execute_routed_query(sql, dry_run=dry_run, warm=warm)

    click.echo(f"\n--- Analysis ---")
    click.echo(f"Complexity : {result.profile.complexity.value}")
    click.echo(f"Warehouse  : {result.recommendation.size.value}")
    click.echo(f"Reason     : {result.recommendation.reason}")
    click.echo(f"Est. cost  : {result.estimate.estimated_credits} credits")

    if result.status == "dry_run":
        click.echo("\n[dry run]")
        return

    if result.status == "error":
        click.echo(f"\n[error] {result.error_message}")
        return

    click.echo(f"\n--- Results ---")
    click.echo(f"Rows       : {result.rows_returned}")
    click.echo(f"Latency    : {result.latency_ms}ms")
    click.echo(f"Act. cost  : {result.actual_credits} credits")

if __name__ == "__main__":
    route()