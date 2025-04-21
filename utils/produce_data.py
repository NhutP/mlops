import pandas as pd
import json
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from tqdm import tqdm


# Configuration
SCHEMA_REGISTRY_URL = "http://192.168.1.110:8081"  # Update with your Schema Registry URL
KAFKA_BROKER = "192.168.1.110:9092,192.168.1.111:9092"  # Update with your Kafka brokers



class data_producer:
    def __init__(self, producer, topic_name, key_generator = lambda x : None):
        self.producer = producer
        self.topic_name = topic_name
        self.key_generator = key_generator
        
        def delivery_report(err, msg):
            pass
            # """Handles Kafka response for each message."""
            # if err is not None:
            #     print(f"❌ Message delivery failed: {err}")
            # else:
            #     # Don't decode Avro messages (they are already serialized)
            #     print(f"✅ Message delivered to {msg.topic()} [Partition {msg.partition()}] at offset {msg.offset()}")

                
        self.delivery_report = delivery_report
        
        
    def send_avro_message(self, message):
        key = self.key_generator(message)
        # Produce the message to Kafka
        producer.produce(topic=topic_name, key=key, value=message, on_delivery=self.delivery_report)
        producer.flush()  # Ensure the message is sent
        # print(f"✅ Message sent to topic '{topic_name}': {message}")

        
    def send_all(self, data):
        for message in tqdm(data):
            key = self.key_generator(message)

            # Produce the message to Kafka
            producer.produce(topic=self.topic_name, key=key, value=message, on_delivery=self.delivery_report)
            
        producer.flush()  # Ensure the message is sent
            

csv_link = {'Store' : "/mnt/c/Users/quang/Desktop/project/stuff/rossmann-store-sales/store.csv", 
            "Record" : "/mnt/c/Users/quang/Desktop/project/stuff/rossmann-store-sales/train.csv",
            "Weather" : "/mnt/c/Users/quang/Desktop/project/stuff/rossmann-store-sales/merged_weather.csv"}

data = ["Weather", "Record", "Store"] 


for i in data:
    topic_name = i  # Your Kafka topic

    # Helper function: converts a message to a dict (required by AvroSerializer)
    def message_to_dict(message, ctx):
        return message

    # Initialize Schema Registry Client
    schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})

    # Query Schema from Schema Registry
    subject = topic_name + "-value"  # Schema is stored as "<topic>-value"
    schema_obj = schema_registry_client.get_latest_version(subject)
    schema_str = schema_obj.schema.schema_str
    print(f"✅ Fetched Schema for {subject}: {schema_str}")

    # Create Avro Serializer using the fetched schema
    avro_serializer = AvroSerializer(schema_registry_client, schema_str, message_to_dict)

    # Configure the Kafka Producer
    producer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'key.serializer': lambda key, ctx : key.encode("utf-8") if key else None,         # Encode keys as strings
        'value.serializer': avro_serializer,     # Serialize values using Avro
        'acks' : 'all'
    }
    
    # Initialize the Producer
    producer = SerializingProducer(producer_conf)
    batch_producer = data_producer(producer, topic_name)
    
    chunk_size = 50000

    for df in pd.read_csv(csv_link[topic_name], chunksize=chunk_size, dtype=str, keep_default_na=False):
        df_dict = [row.to_dict() for _, row in df.iterrows()]
        batch_producer.send_all(df_dict)