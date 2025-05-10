import pandas as pd
from feast import FeatureStore

# Initialize the FeatureStore (this reads your feature_store.yaml)
fs = FeatureStore(repo_path="./feature_serve/feature_repo")

# Create an entity DataFrame. 
# Note: Your DataFrame should include the entity key ("record_id") 
# and an "event_timestamp" column.
entity_df = pd.DataFrame({
    "record_id": [1, 2, 3],  # Example record IDs; ensure these exist in your table.
    "event_timestamp": pd.to_datetime([
        "2023-09-01 00:00:00",
        "2023-09-01 00:00:00",
        "2023-09-01 00:00:00"
    ])
})

# Fetch historical features.
# The feature names are specified as "FeatureViewName:feature_name".
historical_features = fs.get_historical_features(
    entity_df=entity_df,
    features=[
        "allfeatures_view:storetype",
        "allfeatures_view:assortment",
        "allfeatures_view:shopavg_open",
        "allfeatures_view:shopavg_salespercustomer",
        # Add more features as needed.
    ]
)

# Convert the result to a DataFrame.
feature_df = historical_features.to_df()

# Print the resulting DataFrame.
print(feature_df)
