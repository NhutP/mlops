import pandas as pd
from datetime import datetime
from feast import FeatureStore
from sqlalchemy import create_engine


def retrieve_training_data():
  engine = create_engine("postgresql://postgres:qaz123@192.168.1.110:5000/rossman")
  # engine = create_engine("postgresql://postgres:qaz123@external-postgres.default.svc.cluster.local:5000/rossman")
    
  # 2. Define a SQL query to extract all distinct entity keys (and a suitable event timestamp)
  # Here we assume your offline table has an "id" column (the primary key) and "eventTimestamp"
  # We filter for rows where eventTimestamp is before today (CURRENT_DATE).
  # query = """
  #     SELECT DISTINCT id, event_timestamp as event_timestamp
  #     FROM record_features_all
  #     WHERE eventTimestamp < CURRENT_DATE
  # """
  query = """
      SELECT DISTINCT id, event_timestamp as event_timestamp
      FROM record_features_all
  """
  
  # 3. Execute the query and create an entity DataFrame.
  entity_df = pd.read_sql_query(query, engine)
  # Ensure the event_timestamp column is converted to datetime.
  entity_df["event_timestamp"] = pd.to_datetime(entity_df["event_timestamp"])
  
  # 4. Initialize the Feast FeatureStore.
  fs = FeatureStore(repo_path="./data/feature_serve/feature_repo")
  
  sales_features_df = fs.get_historical_features(
      entity_df=entity_df,
      features = [
      # "allfeatures_view:assortment",
      # "allfeatures_view:shopavg_schoolholiday",
      # "allfeatures_view:shopsales_promo",
      "allfeatures_view:day",
      "allfeatures_view:dayofweek",
      "allfeatures_view:dayofyear",
      "allfeatures_view:week",
      # "allfeatures_view:Promo2SinceYear",
      # "allfeatures_view:daysinpromocycle",
      # "allfeatures_view:primpromocycle",
      # "allfeatures_view:promointerval",
      # "allfeatures_view:CompetitionDistance",
      # "allfeatures_view:CompetitionOpenSinceYear",
      # "allfeatures_view:daysincompetition_unrounded",
      # "allfeatures_view:schoolholiday",
      # "allfeatures_view:stateholiday",
      # "allfeatures_view:holidays_lastweek",
      # "allfeatures_view:holidays_nextweek",
      # "allfeatures_view:holidays_thisweek",
      ### "allfeatures_view:prevquarter_med",
      ### "allfeatures_view:prevyear_dps_med",
      # "allfeatures_view:weather_maxtemp",
      # "allfeatures_view:weather_precip",
      # "allfeatures_view:closurefeat",
      
      "allfeatures_view:sales" # target column
  ]

  ).to_df()
  print(sales_features_df.head(5))
  
  return sales_features_df
# # Print a preview of the retrieved features.
# print(sales_features_df.head())
# print(type(sales_features_df))