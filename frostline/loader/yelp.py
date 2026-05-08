import os
from frostline.connectors.snowflake import get_connection, execute_query
from frostline.config import SnowflakeConfig

FILE_TO_TABLE = {
    "yelp_academic_dataset_business.json": "BUSINESS",
    "yelp_academic_dataset_review.json": "REVIEW",
    "yelp_academic_dataset_user.json": "USER_DATA",
    "yelp_academic_dataset_checkin.json": "CHECKIN",
    "yelp_academic_dataset_tip.json": "TIP",
}

def load_yelp_data(data_dir: str):
    config = SnowflakeConfig.from_env()
    conn = get_connection(config)
    cursor = conn.cursor()

    try:
        cursor.execute("USE DATABASE FROSTLINE")
        cursor.execute("USE SCHEMA RAW")

        cursor.execute("""CREATE FILE FORMAT IF NOT EXISTS json_format
                       TYPE = 'JSON'
                       STRIP_OUTER_ARRAY = FALSE;""")

        cursor.execute("""CREATE STAGE IF NOT EXISTS yelp_stage
        FILE_FORMAT = json_format;""")

        for filename, table in FILE_TO_TABLE.items():
            filepath = os.path.join(data_dir, filename)
            print(f"Uploading {filename}...")
            abs_path = os.path.abspath(filepath)
            cursor.execute(f"PUT 'file://{abs_path}' @yelp_stage/{table}")
            
            print(f"Loading into {table}...")
            cursor.execute(f"COPY INTO {table} FROM @yelp_stage/{table}")
            print(cursor.fetchall())

        for table in FILE_TO_TABLE.values():
            result = execute_query(conn, f"SELECT COUNT(*) FROM {table}")
            print(f"{table}: {result[0][0]} rows")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    load_yelp_data("data/Yelp JSON")