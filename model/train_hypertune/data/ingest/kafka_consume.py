from confluent_kafka import DeserializingConsumer
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient

def key_deserializer(key, ctx):
    """Custom key deserializer that decodes the key using UTF-8."""
    if key is None:
        return None
    return key.decode("utf-8")

class KafkaAvroConsumer:
    def __init__(self, kafka_broker, schema_registry_url, topic, group_id, schema_subject=None):
        """
        Initialize the Kafka Avro Consumer.
        
        :param kafka_broker: Kafka broker address(es) as a string 
                             (e.g., "192.168.1.110:9092,192.168.1.111:9092").
        :param schema_registry_url: URL for the Schema Registry 
                                    (e.g., "http://192.168.1.110:8081").
        :param topic: The Kafka topic to subscribe to.
        :param group_id: Consumer group ID.
        :param schema_subject: The subject name used to fetch the Avro schema from Schema Registry.
                               If None, defaults to '<topic>-value'.
        """
        self.kafka_broker = kafka_broker
        self.schema_registry_url = schema_registry_url
        self.topic = topic
        self.group_id = group_id

        # Initialize the Schema Registry client.
        self.schema_registry_client = SchemaRegistryClient({'url': schema_registry_url})
        
        # Determine the schema subject name.
        if schema_subject is None:
            schema_subject = topic + "-value"
        
        # Fetch the latest schema using the subject.
        schema_obj = self.schema_registry_client.get_latest_version(schema_subject)
        self.schema_str = schema_obj.schema.schema_str
        print(f"✅ Fetched Schema for subject '{schema_subject}': {self.schema_str}")
        
        # Create the Avro deserializer using the fetched schema string.
        self.avro_deserializer = AvroDeserializer(self.schema_registry_client, self.schema_str)
        
        # Configure the Kafka consumer.
        consumer_conf = {
            'bootstrap.servers': self.kafka_broker,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',  # Start from beginning if no offset exists.
            'key.deserializer': key_deserializer,  # Use the custom key deserializer.
            'value.deserializer': self.avro_deserializer  # Deserialize values from Avro to dict.
        }
        self.consumer = DeserializingConsumer(consumer_conf)
        self.consumer.subscribe([self.topic])
        print(f"✅ Kafka Consumer started. Listening to topic '{self.topic}' in group '{self.group_id}'...")


    def read_all_messages(self, poll_timeout=1.0):
        """
        Continuously poll Kafka for new messages and yield (key, value) tuples.
        
        :param poll_timeout: Time in seconds to wait for messages on each poll.
        :yield: A tuple (key, value) for each received message.
        """
        try:
            while True:
                msg = self.consumer.poll(timeout=poll_timeout)
                if msg is None:
                    continue  # No new message; keep polling.
                if msg.error():
                    print(f"❌ Error: {msg.error()}")
                    continue
                yield (msg.key(), msg.value())
        except KeyboardInterrupt:
            print("\n🛑 Consumer interrupted by user.")
        finally:
            self.consumer.close()


    def read_batch(self, batch_size, poll_timeout=1.0):
        """
        Poll Kafka for messages and return a batch of messages as a list of (key, value) tuples.
        
        :param batch_size: The number of messages to read before returning.
        :param poll_timeout: Time in seconds to wait for each poll.
        :return: List of (key, value) tuples.
        """
        messages = []
        unsuccess_poll = 0
        
        while len(messages) < batch_size:
            msg = self.consumer.poll(timeout=poll_timeout)
            if msg is None:
                unsuccess_poll += 1
                if unsuccess_poll == 10:
                    return messages
                continue  # No message received in this poll, keep waiting.
            if msg.error():
                print(f"❌ Error: {msg.error()}")
                continue
            # messages.append((msg.key(), msg.value()))
            messages.append(msg.value())
        return messages


# Example usage:
if __name__ == "__main__":
    # Configuration parameters
    KAFKA_BROKER = "192.168.1.110:9092,192.168.1.111:9092"
    SCHEMA_REGISTRY_URL = "http://192.168.1.110:8081"
    TOPIC_NAME = "Store"          # Kafka topic name
    GROUP_ID = "ttt"         # Consumer group name

    # You can specify a schema subject or let it default to "<topic>-value".
    schema_subject = "Store-value"  # Optional; defaults to "Movie-value" if not provided

    # Create an instance of the consumer.
    consumer = KafkaAvroConsumer(KAFKA_BROKER, SCHEMA_REGISTRY_URL, TOPIC_NAME, GROUP_ID, schema_subject)
    
    # Read and print all messages from the topic.
    for key, value in consumer.read_all_messages():
        print(f"✅ Received message: Key={key}, Value={value}")
        print(value)
        print(type(value))
        print('----------------------------')
        input("Press Enter to fetch the next message...")
