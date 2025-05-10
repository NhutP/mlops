from kafka_consume import KafkaAvroConsumer
from sql_bulk_inserter import PostgresBulkInserter


class data_ingester:
    def __init__(self, consumer: KafkaAvroConsumer, inserter: PostgresBulkInserter):
        self.consumer = consumer
        self.inserter = inserter
    
    
    def ingest_data(self, table_name, batch_size=20000):        
        while True:
            data_message = self.consumer.read_batch(batch_size=batch_size)

            if len(data_message) == 0:
                break
            
            self.inserter.bulk_insert(table=table_name, data=data_message)
            
        print(f'Done {table_name}')
    
    
if __name__ == '__main__':
    KAFKA_BROKER = "192.168.1.110:9092,192.168.1.111:9092"
    SCHEMA_REGISTRY_URL = "http://192.168.1.110:8081"
    
    GROUP_ID = "2503-4"         # Consumer group name
    
    for topic in ["Weather", "Store", "Record"]:
        print(f"change topic to {topic}")
        TOPIC_NAME = topic          # Kafka topic name
        table_name = topic
        
        # You can specify a schema subject or let it default to "<topic>-value".
        schema_subject = topic + "-value" # Optional; defaults to "Movie-value" if not provided

        # Create an instance of the consumer.
        consumer = KafkaAvroConsumer(KAFKA_BROKER, SCHEMA_REGISTRY_URL, TOPIC_NAME, GROUP_ID, schema_subject)

        inserter = PostgresBulkInserter(
            db_host="192.168.1.110",
            db_port="5000",
            db_name= "rossman",
            db_user="postgres",
            db_password="qaz123"
        )
        
        data_ingest = data_ingester(consumer, inserter)
        data_ingest.ingest_data(table_name=topic, batch_size=2000)