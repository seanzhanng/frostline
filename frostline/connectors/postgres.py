import psycopg2
from frostline.config import PostgresConfig

def get_connection(config: PostgresConfig):
    return psycopg2.connect(
        host=config.host,
        port=config.port,
        user=config.user,
        password=config.password,
        dbname=config.database
    )

def execute_query(conn, sql: str, params: tuple = None):
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        if cursor.description:
            return cursor.fetchall()
        conn.commit()
        return None
    finally:
        cursor.close()