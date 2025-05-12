from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException

# Kafka Configuration
KAFKA_BROKER = "192.168.1.110:9092,192.168.1.111:9092"  # Change this to your Kafka broker

# Initialize Kafka Admin Client
admin_client = AdminClient({"bootstrap.servers": KAFKA_BROKER})

# Check if Topic Exists
def topic_exists(topic_name):
    """Check if a Kafka topic exists."""
    try:
        cluster_metadata = admin_client.list_topics(timeout=5)
        return topic_name in cluster_metadata.topics
    except KafkaException as e:
        print(f"❌ Error checking topic: {e}")
        return False

# Create Topic if it Doesn't Exist
def create_topic(topic_name, num_partitions=1, replication_factor=1):
    """Create a Kafka topic if it does not exist."""
    if topic_exists(topic_name):
        print(f"✅ Topic '{topic_name}' already exists.")
        return
    
    print(f"⚡ Creating topic '{topic_name}'...")
    new_topic = NewTopic(topic_name, num_partitions, replication_factor)
    future = admin_client.create_topics([new_topic])

    # Wait for the topic creation to complete
    for topic, f in future.items():
        try:
            f.result()  # Block until complete
            print(f"✅ Topic '{topic}' created successfully!")
        except Exception as e:
            print(f"❌ Failed to create topic '{topic}': {e}")


# Run the check & create function
create_topic("Record", 2, 2)
create_topic("Store", 2, 2)
create_topic("Weather", 2, 2)