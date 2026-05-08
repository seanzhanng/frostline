import click
import yaml
from frostline.executor import execute_routed_query
from frostline.orchestrator.dag import DAG, TaskNode
from frostline.orchestrator.runner import run_pipeline
from frostline.config import SnowflakeConfig
from frostline.connectors.snowflake import get_connection as sf_connect
from frostline.orchestrator.tasks import (
    create_task, create_stream_task, resume_task,
    suspend_task, drop_task, list_tasks
)

@click.group()
def cli():
    """Frostline — cost-aware Snowflake query router."""
    pass

@cli.command()
@click.argument("sql")
@click.option("--dry-run", is_flag=True)
@click.option("--warm/--cold", default=True)
def route(sql, dry_run, warm):
    """Analyze, route, and execute a single query."""
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

@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--dry-run", is_flag=True)
@click.option("--warm/--cold", default=True)
def run(filepath, dry_run, warm):
    """Run a pipeline from a YAML file."""
    with open(filepath) as f:
        config = yaml.safe_load(f)

    dag = DAG()
    for step in config["steps"]:
        deps = tuple(step.get("depends_on", []))
        dag.add_task(TaskNode(id=step["id"], sql=step["sql"], dependencies=deps))

    run_pipeline(dag, dry_run=dry_run, warm=warm)

@cli.group()
def tasks():
    """Manage Snowflake tasks."""
    pass

@tasks.command("list")
def tasks_list():
    """List all Snowflake tasks."""
    conn = sf_connect(SnowflakeConfig.from_env())
    results = list_tasks(conn)
    if results:
        for row in results:
            click.echo(row)
    else:
        click.echo("No tasks found.")
    conn.close()

@tasks.command("create")
@click.option("--name", required=True)
@click.option("--schedule", required=True)
@click.option("--sql", required=True)
@click.option("--stream", default=None, help="Stream name for triggered tasks.")
def tasks_create(name, schedule, sql, stream):
    """Create a Snowflake task."""
    conn = sf_connect(SnowflakeConfig.from_env())
    warehouse = SnowflakeConfig.from_env().warehouse

    if stream:
        create_stream_task(conn, name, warehouse, stream, schedule, sql)
        click.echo(f"Stream task {name} created (triggers on {stream}).")
    else:
        create_task(conn, name, warehouse, schedule, sql)
        click.echo(f"Task {name} created.")

    resume_task(conn, name)
    click.echo(f"Task {name} resumed.")
    conn.close()

@tasks.command("resume")
@click.option("--name", required=True)
def tasks_resume(name):
    """Resume a suspended task."""
    conn = sf_connect(SnowflakeConfig.from_env())
    resume_task(conn, name)
    click.echo(f"Task {name} resumed.")
    conn.close()

@tasks.command("suspend")
@click.option("--name", required=True)
def tasks_suspend(name):
    """Suspend a running task."""
    conn = sf_connect(SnowflakeConfig.from_env())
    suspend_task(conn, name)
    click.echo(f"Task {name} suspended.")
    conn.close()

@tasks.command("drop")
@click.option("--name", required=True)
def tasks_drop(name):
    """Drop a task."""
    conn = sf_connect(SnowflakeConfig.from_env())
    drop_task(conn, name)
    click.echo(f"Task {name} dropped.")
    conn.close()

if __name__ == "__main__":
    cli()