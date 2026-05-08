from dataclasses import dataclass
from collections import deque

@dataclass(frozen=True)
class TaskNode:
    id: str
    sql: str
    dependencies: tuple = ()

class DAG:
    def __init__(self):
        self.nodes = {}

    def add_task(self, node: TaskNode):
        if node.id in self.nodes:
            raise ValueError(f"duplicate task: {node.id}")
        for dep in node.dependencies:
            if dep not in self.nodes:
                raise ValueError(f"missing dependency: {dep}")
        self.nodes[node.id] = node
    
    def execution_order(self) -> list[str]:
        in_degree = {}
        dependents = {}

        for node_id, node in self.nodes.items():
            in_degree[node_id] = len(node.dependencies)
            dependents[node_id] = []

        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                dependents[dep].append(node_id)

        queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)
            for child in dependents[current]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(result) != len(self.nodes):
            raise ValueError("cycle detected in DAG")

        return result
    
    def validate(self):
        for node_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"task {node_id} references missing dependency: {dep}")
        self.execution_order()