from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, dayofweek, weekofyear, month, year, avg, stddev, 
    expr, datediff, unix_timestamp, when, lit, sum, count, lag, concat_ws
)
from pyspark.sql.window import Window

# Initialize Spark session using native JDBC support
spark = SparkSession.builder \
    .appName("RossmannFeatureEngineeringFull") \
    .getOrCreate()

# PostgreSQL connection parameters
jdbc_url = "jdbc:postgresql://localhost:5432/rossmann"
connection_options = {
    "user": "your_username",
    "password": "your_password",
    "driver": "org.postgresql.Driver"
}

# --- Step 1: Load Raw Data ---
# Read the Store table
store_df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "Store") \
    .option("user", connection_options["user"]) \
    .option("password", connection_options["password"]) \
    .option("driver", connection_options["driver"]) \
    .load()

# Read the Record table
record_df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "Record") \
    .option("user", connection_options["user"]) \
    .option("password", connection_options["password"]) \
    .option("driver", connection_options["driver"]) \
    .load()

# Convert 'date' column to date type
record_df = record_df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))

# Join Record with Store on "store"
df = record_df.join(store_df, on="store", how="left")

# --- Step 2: Create Basic Temporal Features ---
df = df.withColumn("day_of_week", dayofweek(col("date"))) \
       .withColumn("week_of_year", weekofyear(col("date"))) \
       .withColumn("month", month(col("date"))) \
       .withColumn("year", year(col("date")))

# Create a numeric representation of the date (days since epoch) for windowing
df = df.withColumn("date_num", (col("date").cast("long") / 86400).cast("integer"))

# --- Step 3: Recent Data Features ---
# Define a helper function to compute rolling averages and standard deviations
def add_rolling_features(df, window_days, feature):
    window_spec = Window.partitionBy("store").orderBy("date_num").rangeBetween(-window_days, -1)
    df = df.withColumn(f"rolling_avg_{feature}_{window_days}d", avg(col(feature)).over(window_spec)) \
           .withColumn(f"rolling_std_{feature}_{window_days}d", stddev(col(feature)).over(window_spec))
    return df

# Compute rolling features for different time windows for sales and customers.
for days in [30, 90, 180, 365, 730]:
    df = add_rolling_features(df, days, "sales")
    df = add_rolling_features(df, days, "customers")

# (Additional measures such as median, percentiles, or harmonic mean would require custom UDFs.)

# --- Step 4: Temporal Information Features ---
# Example: Days since competition opened (build competition start date from store info)
df = df.withColumn("competition_start",
                   to_date(concat_ws("-", col("competitionopensinceyear"), col("competitionopensincemonth"), lit("01")), "yyyy-M-d"))
df = df.withColumn("days_since_competition", datediff(col("date"), col("competition_start")))

# Create simple day counter features for promotion cycles:
df = df.withColumn("promo_cycle_day", col("date_num") % 14)  # 14-day cycle
df = df.withColumn("secondary_promo_cycle_day", col("date_num") % 90)  # Approx. 3-month cycle

# Create holiday flag (assuming 't' indicates true)
df = df.withColumn("is_holiday", when((col("schoolholiday")=="t") | (col("stateholiday")=="t"), 1).otherwise(0))

# Count holidays in current week, last week, and next week using range-based window functions:
holiday_window_current = Window.partitionBy("store").orderBy("date_num").rangeBetween(0, 6)
df = df.withColumn("holidays_current_week", expr("sum(is_holiday) over (partition by store order by date_num range between 0 and 6)"))
holiday_window_last = Window.partitionBy("store").orderBy("date_num").rangeBetween(-7, -1)
df = df.withColumn("holidays_last_week", expr("sum(is_holiday) over (partition by store order by date_num range between -7 and -1)"))
holiday_window_next = Window.partitionBy("store").orderBy("date_num").rangeBetween(1, 7)
df = df.withColumn("holidays_next_week", expr("sum(is_holiday) over (partition by store order by date_num range between 1 and 7)"))

# --- Step 5: Current Trends Features ---
# Approximate a linear trend (slope) over the past 90 days for sales using a window-based approach.
trend_window = Window.partitionBy("store").orderBy("date_num").rangeBetween(-90, -1)
df = df.withColumn("avg_day_90", avg(col("date_num")).over(trend_window)) \
       .withColumn("avg_sales_90", avg(col("sales")).over(trend_window))
df = df.withColumn("cov_day_sales", avg((col("date_num") - col("avg_day_90")) * (col("sales") - col("avg_sales_90"))).over(trend_window))
df = df.withColumn("var_day", avg((col("date_num") - col("avg_day_90"))**2).over(trend_window))
df = df.withColumn("trend_slope_90", col("cov_day_sales") / col("var_day"))

# Approximate year-over-year trend for the previous month (simplified approach)
# Here, we use the difference between current rolling average (365-day window) and that 365 days ago.
df = df.withColumn("rolling_avg_sales_365", col("rolling_avg_sales_365d"))  # from earlier window
df = df.withColumn("rolling_avg_sales_365d_ago", lag("rolling_avg_sales_365d", 365).over(Window.partitionBy("store").orderBy("date_num")))
df = df.withColumn("yoy_trend", col("rolling_avg_sales_365") - col("rolling_avg_sales_365d_ago"))

# --- Step 6: Other Store-Level Information ---
# Calculate average sales per customer for each record
df = df.withColumn("sales_per_customer", col("sales") / col("customers"))

# Aggregate store-level statistics (e.g., average sales during promotions)
store_agg = df.groupBy("store").agg(
    avg(when(col("promo")=="t", col("sales")).otherwise(None)).alias("avg_sales_promo"),
    avg("sales").alias("avg_sales_overall"),
    avg(when(col("day_of_week") == 7, col("sales")).otherwise(None)).alias("avg_sales_saturday")
)
df = df.join(store_agg, on="store", how="left")
df = df.withColumn("promo_sales_ratio", col("avg_sales_promo") / col("avg_sales_overall")) \
       .withColumn("saturday_sales_ratio", col("avg_sales_saturday") / col("avg_sales_overall"))

# Proportion of days a store is open (per store)
store_open = df.groupBy("store").agg(
    (sum(when(col("open")=="t", 1).otherwise(0)) / count("*")).alias("prop_open")
)
df = df.join(store_open, on="store", how="left")

# --- Step 7: Select and Write Final Features ---
final_columns = [
    "store", "date", "sales", "customers",
    "rolling_avg_sales_30", "rolling_std_sales_30",
    "rolling_avg_sales_90", "rolling_std_sales_90",
    "rolling_avg_sales_180", "rolling_std_sales_180",
    "rolling_avg_sales_365", "rolling_std_sales_365",
    "rolling_avg_sales_730", "rolling_std_sales_730",
    "rolling_avg_customers_30", "rolling_avg_customers_90", "rolling_avg_customers_180",
    "rolling_avg_customers_365", "rolling_avg_customers_730",
    "day_of_week", "week_of_year", "month", "year",
    "days_since_competition", "promo_cycle_day", "secondary_promo_cycle_day",
    "holidays_current_week", "holidays_last_week", "holidays_next_week",
    "trend_slope_90", "yoy_trend", "sales_per_customer",
    "promo_sales_ratio", "saturday_sales_ratio", "prop_open",
    "storetype", "assortment", "competitiondistance", "promo2", "promointerval"
]

final_df = df.select(*final_columns)

# Write the final feature DataFrame to a new PostgreSQL table
final_df.write.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "record_features_full") \
    .option("user", connection_options["user"]) \
    .option("password", connection_options["password"]) \
    .option("driver", connection_options["driver"]) \
    .mode("overwrite") \
    .save()

spark.stop()
