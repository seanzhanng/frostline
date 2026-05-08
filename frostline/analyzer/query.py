import re
from enum import Enum
from dataclasses import dataclass

class Complexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    HEAVY = "heavy"

@dataclass(frozen=True)
class QueryProfile:
    sql: str
    complexity: Complexity
    join_count: int
    table_count: int
    has_group_by: bool
    has_subquery: bool
    has_order_by: bool

def analyze_query(sql: str) -> QueryProfile:
    normalized = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
    normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
    upper = normalized.upper()

    join_count = len(re.findall(r'\bJOIN\b', upper))
    has_group_by = bool(re.search(r'\bGROUP\s+BY\b', upper))
    has_order_by = bool(re.search(r'\bORDER\s+BY\b', upper))
    has_subquery = bool(re.search(r'\(\s*SELECT\b', upper))

    tables = set()
    for match in re.finditer(r'\bJOIN\s+(\w+)', upper):
        tables.add(match.group(1))
    for match in re.finditer(
        r'\bFROM\s+([\w\s,]+?)(?:\bWHERE\b|\bJOIN\b|\bGROUP\b|\bORDER\b|\bHAVING\b|\bLIMIT\b|\bUNION\b|$)',
        upper
    ):
        for table in match.group(1).split(','):
            token = table.strip().split()[-1] 
            if token:
                tables.add(token)

    table_count = len(tables)

    if join_count >= 3 and has_subquery:
        complexity = Complexity.HEAVY
    elif table_count >= 5:
        complexity = Complexity.HEAVY
    elif join_count >= 3 or has_subquery:
        complexity = Complexity.COMPLEX
    elif join_count >= 1 or has_group_by:
        complexity = Complexity.MODERATE
    else:
        complexity = Complexity.SIMPLE

    return QueryProfile(
        sql=sql,
        complexity=complexity,
        join_count=join_count,
        table_count=table_count,
        has_group_by=has_group_by,
        has_subquery=has_subquery,
        has_order_by=has_order_by,
    )