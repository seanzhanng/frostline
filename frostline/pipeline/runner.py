from frostline.pipeline.dag import DAG
from frostline.executor import execute_routed_query, ExecutionResult

def run_pipeline(dag: DAG, dry_run: bool = False, warm: bool = True) -> list[ExecutionResult]:
    order = dag.execution_order()
    results = []

    for task_id in order:
        node = dag.nodes[task_id]
        print(f"\n=== Step: {task_id} ===")

        result = execute_routed_query(node.sql, dry_run=dry_run, warm=warm)
        results.append(result)

        print(f"Complexity : {result.profile.complexity.value}")
        print(f"Warehouse  : {result.recommendation.size.value}")
        print(f"Est. cost  : {result.estimate.estimated_credits} credits")

        if result.status == "error":
            print(f"FAILED: {result.error_message}")
            print("Pipeline stopped.")
            break

    total_estimated = sum(r.estimate.estimated_credits for r in results)
    total_actual = sum(r.actual_credits for r in results)

    print(f"\n=== Pipeline Summary ===")
    print(f"Steps run  : {len(results)}/{len(order)}")
    print(f"Est. total : {round(total_estimated, 6)} credits")
    if not dry_run:
        print(f"Act. total : {round(total_actual, 6)} credits")

    return results