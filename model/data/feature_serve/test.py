import pandas as pd
from feast import FeatureStore

fs = FeatureStore(repo_path="./feature_repo")

entity_df = pd.DataFrame({
    "id": [904377, 904387],         # As strings, matching the entity type
    "event_timestamp": pd.to_datetime(["2025-03-26 11:47:02.78501", "2025-03-26 11:47:02.78501"])
})

features = fs.get_historical_features(
    entity_df=entity_df,
    features=[
        "allfeatures_view:sales",
        "allfeatures_view:storetype",
    ]
)

df = features.to_df()
print(df)
