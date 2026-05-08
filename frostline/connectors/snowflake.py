import snowflake.connector
from frostline.config import SnowflakeConfig

def get_connection(config: SnowflakeConfig):
    return snowflake.connector.connect(
        account=config.account,
        user=config.user,
        password=config.password,
        warehouse=config.warehouse,
        database=config.database,
        schema=config.schema,
    )

def execute_query(conn, sql: str):
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()