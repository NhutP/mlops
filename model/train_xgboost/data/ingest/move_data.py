import psycopg2
from airflow.hooks.base import BaseHook

# def move_data_to_processed_table(source_table: str = "Record", destination_table: str = "ProcessedRecord"):
#     # Get Airflow connection
#     conn = BaseHook.get_connection("postgres_conn")

#     # Connect to PostgreSQL using credentials from the Airflow connection
#     conn_string = f"host={conn.host} dbname={conn.schema} user={conn.login} password={conn.password} port={conn.port}"
#     with psycopg2.connect(conn_string) as pg_conn:
#         with pg_conn.cursor() as cursor:
#             sql = f'''
#                 INSERT INTO "{destination_table}" SELECT * FROM "{source_table}";
                
#             '''
#             cursor.execute(sql)
#         pg_conn.commit()

def move_data_to_processed_table(
    host: str = "192.168.1.110",
    port: int = "5000",
    dbname: str = "rossman",
    user: str = "postgres",
    password: str = "qaz123",
    source_table: str = "Record",
    destination_table: str = "ProcessedRecord"
):
    # Build connection string
    conn_string = f"host={host} port={port} dbname={dbname} user={user} password={password}"

    # Execute data move
    with psycopg2.connect(conn_string) as pg_conn:
        with pg_conn.cursor() as cursor:
            sql = f'''
                INSERT INTO "{destination_table}" SELECT * FROM "{source_table}";
            '''
            cursor.execute(sql)
        pg_conn.commit()
        
# TRUNCATE TABLE "{source_table}";