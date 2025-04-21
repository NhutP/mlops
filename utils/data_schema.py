import json
from confluent_kafka.schema_registry import Schema, SchemaRegistryClient

# Schema Registry Configuration
schema_registry_conf = {
    'url': 'http://192.168.1.110:8081'  # Replace with your Schema Registry URL
}

# Initialize Schema Registry Client
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# Load schemas from JSON file
with open('rossman_schemas.json', 'r') as f:
    all_schema = json.load(f)

schema_id = {}
converted_schemas = {}

# Convert each schema dictionary to a JSON string and register it
for name, schema_dict in all_schema.items():
    # Convert dict to JSON string
    schema_json_str = json.dumps(schema_dict)
    
    # Create a Schema object using the JSON string (use "AVRO" as the schema type)
    converted_schemas[name] = Schema(schema_json_str, "AVRO")
    
    # Register the schema under the subject name (e.g., "movie-value")
    subject = name + '-value'
    schema_id[subject] = schema_registry_client.register_schema(subject, converted_schemas[name])
    
    print(f"Registered {name} schema under subject '{subject}' with ID: {schema_id[subject]}")

# Save the registered schema IDs to a JSON file
with open('schema_id.json', 'w') as f:
    json.dump(schema_id, f)

print("Schema registration completed and IDs saved to 'schema_id.json'.")