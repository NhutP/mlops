from kafka_consume import KafkaAvroConsumer
from ingest_data import data_ingester
from sql_bulk_inserter import PostgresBulkInserter
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from move_data import move_data_to_processed_table


def run_ingest_for_topic(
    topic: str,
    kafka_brokers: str = "192.168.1.110:9092,192.168.1.111:9092",
    schema_registry_url: str = "http://192.168.1.110:8081",
    group_id: str = "2503-4",
    schema_subject: str = None,
    table_name: str = None,
    batch_size: int = 2000,
    db_host: str = "192.168.1.110",
    db_port: str = "5000",
    db_name: str = "rossman",
    db_user: str = "postgres",
    db_password: str = "qaz123"
):
    """
    Ingest data from a Kafka topic into a PostgreSQL table using the provided parameters.
    All parameters have default values but can be overridden.
    """
    if schema_subject is None:
        schema_subject = topic + "-value"

    if table_name is None:
        table_name = topic

    consumer = KafkaAvroConsumer(
        kafka_brokers,
        schema_registry_url,
        topic,
        group_id,
        schema_subject
    )

    inserter = PostgresBulkInserter(
        db_host=db_host,
        db_port=db_port,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password
    )

    ingester = data_ingester(consumer, inserter)
    ingester.ingest_data(table_name=table_name, batch_size=batch_size)
    
    
    
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
    "start_date": datetime(2024, 1, 1),
    "catchup": False,
}

topics = ["Weather", "Store", "Record"]


with DAG(
    dag_id="kafka_to_postgres_dag",
    description="Ingest Kafka Avro messages into Postgres using COPY",
    default_args=default_args,
    schedule_interval=None,
    tags=["kafka", "postgres", "etl"],
) as dag:
    ingest_tasks = []
    for topic in topics:
        task = PythonOperator(
            task_id=f"ingest_{topic.lower()}",
            python_callable=run_ingest_for_topic,
            op_kwargs={
                "topic": topic,
                "kafka_brokers": "192.168.1.110:9092,192.168.1.111:9092",
                "schema_registry_url": "http://192.168.1.110:8081",
                "group_id": "2503-4",
                "db_host": "192.168.1.110",
                "db_port": "5000",
                "db_name": "rossman",
                "db_user": "postgres",
                "db_password": "qaz123",
                "batch_size": 2000
            },
        )
        ingest_tasks.append(task)
    
    spark_task = SparkSubmitOperator(
        task_id="run_feature_kaggle",
        application="/mnt/c/Users/quang/Desktop/project/model/train_xgboost/data/processing/feature_kaggle.py",  # replace with full path
        conn_id="spark_master",  # must point to a properly defined Spark connection, go to admin in UI -> choose a spark type and set to "spark://192.168.1.110:7777"
        jars="/mnt/c/Users/quang/Desktop/project/stuff/postgresql-42.7.1.jar",     # full path to JAR
        executor_memory="2G",
        conf={
            "spark.master": "spark://192.168.1.110:7777", 
            "spark.driver.host": "192.168.1.9",
            "spark.driver.bindAddress": "192.168.1.9",
            "spark.driver.port": "46242",
            "spark.blockManager.port": "10000",
            "spark.driver.blockManager.port": "10000"
        },
        verbose=True,
        name="airflow_feature_kaggle_job",
        spark_binary="spark-submit"
    )
    
    move_data_task = PythonOperator(
        task_id="move_data_from_newrecord_to_record",
        python_callable=move_data_to_processed_table,
        op_kwargs={
            "source_table": "Record",
            "destination_table": "ProcessedRecord"
        }
    )
    
    ingest_tasks >> spark_task >> move_data_task