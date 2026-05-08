from frostline.connectors.snowflake import execute_query

def create_task(conn, name: str, warehouse: str, schedule: str, sql: str):
    return execute_query(conn, f"""
        CREATE OR REPLACE TASK {name}
        WAREHOUSE = {warehouse}
        SCHEDULE = '{schedule}'
        AS
        {sql}
    """)

def create_stream_task(conn, name: str, warehouse: str, stream: str, schedule: str, sql: str):
    return execute_query(conn, f"""
        CREATE OR REPLACE TASK {name}
        WAREHOUSE = {warehouse}
        SCHEDULE = '{schedule}'
        WHEN SYSTEM$STREAM_HAS_DATA('{stream}')
        AS
        {sql}
    """)

def resume_task(conn, name: str):
    return execute_query(conn, f"ALTER TASK {name} RESUME")

def suspend_task(conn, name: str):
    return execute_query(conn, f"ALTER TASK {name} SUSPEND")

def drop_task(conn, name: str):
    return execute_query(conn, f"DROP TASK IF EXISTS {name}")

def list_tasks(conn):
    return execute_query(conn, "SHOW TASKS")