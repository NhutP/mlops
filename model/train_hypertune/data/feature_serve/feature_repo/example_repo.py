from datetime import timedelta
from feast import FeatureStore, Entity, Field, FeatureView, ValueType
from feast.types import String, Float32, Int64 as FieldInt64  # For schema fields

# Define entities for a composite key.
record_id_entity = Entity(
    name="id",  
    value_type=ValueType.INT64,  # Use the old enum here.
    description="Unique store identifier",
)


# Import the PostgreSQL source.
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)

# # Define the PostgreSQL source with an explicit timestamp column.
# allfeatures_source = PostgreSQLSource(
#     name="record_features_all_source",
#     query="""
#         SELECT * FROM record_features_all;
#     """,
#     created_timestamp_column="eventTimestamp"  # This column is expected in the query result.
# )

allfeatures_source = PostgreSQLSource(
    name="record_features_all_source",
    table="record_features_all",  # Use the table directly.
    timestamp_field="event_timestamp"
    # created_timestamp_column="event_timestamp"  # This column exists in your table.
)


# Define the FeatureView with all the feature columns using Field.
allfeatures_view = FeatureView(
    name="allfeatures_view",
    entities=[record_id_entity],
    ttl=timedelta(days=7000),
    schema=[
        Field(name="storetype", dtype=String),
        Field(name="assortment", dtype=String),
        Field(name="shopavg_open", dtype=Float32),
        Field(name="shopavg_salespercustomer", dtype=Float32),
        Field(name="shopavg_schoolholiday", dtype=Float32),
        Field(name="shopsales_holiday", dtype=Float32),
        Field(name="shopsales_promo", dtype=Float32),
        Field(name="shopsales_saturday", dtype=Float32),
        Field(name="day", dtype=FieldInt64),
        Field(name="dayofweek", dtype=FieldInt64),
        Field(name="dayofyear", dtype=FieldInt64),
        Field(name="month", dtype=FieldInt64),
        Field(name="week", dtype=FieldInt64),
        Field(name="year", dtype=FieldInt64),
        Field(name="dayavg_openyesterday", dtype=Float32),
        Field(name="Promo2", dtype=String),
        Field(name="Promo2SinceWeek", dtype=FieldInt64),
        Field(name="Promo2SinceYear", dtype=FieldInt64),
        Field(name="daysinpromocycle", dtype=FieldInt64),
        Field(name="primpromocycle", dtype=FieldInt64),
        Field(name="promo", dtype=String),
        Field(name="promointerval", dtype=String),
        Field(name="CompetitionDistance", dtype=Float32),
        Field(name="CompetitionOpenSinceMonth", dtype=FieldInt64),
        Field(name="CompetitionOpenSinceYear", dtype=FieldInt64),
        Field(name="daysincompetition", dtype=FieldInt64),
        Field(name="daysincompetition_unrounded", dtype=FieldInt64),
        Field(name="rnd_CompetitionDistance", dtype=Float32),
        Field(name="schoolholiday", dtype=String),
        Field(name="stateholiday", dtype=String),
        Field(name="holidays_lastweek", dtype=Float32),
        Field(name="holidays_nextweek", dtype=Float32),
        Field(name="holidays_thisweek", dtype=Float32),
        Field(name="prevquarter_dps_med", dtype=Float32),
        Field(name="prevhalfyear", dtype=Float32),
        Field(name="prevyear_med", dtype=Float32),
        Field(name="prevquarter_cust_dps_med", dtype=Float32),
        Field(name="prevyear_cust_dps_med", dtype=Float32),
        Field(name="lastmonth_yoy", dtype=Float32),
        Field(name="linmod_quarterly", dtype=Float32),
        Field(name="linmod_yearly", dtype=Float32),
        Field(name="weather_maxtemp", dtype=Float32),
        Field(name="weather_precip", dtype=Float32),
        Field(name="relativeweather_maxtemp", dtype=Float32),
        Field(name="relativeweather_precip", dtype=Float32),
        Field(name="closurefeat", dtype=FieldInt64),
        Field(name="sales", dtype=Float32),
    ],
    online=False,  # Set to True if you intend to serve these features in real time.
    source=allfeatures_source,
)