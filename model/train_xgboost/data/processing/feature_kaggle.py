from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, dayofmonth, dayofweek, weekofyear, month, year, date_format,
    avg, stddev, sum as _sum, when, lag, lit, concat_ws, round, log, unix_timestamp, datediff
)
from pyspark.sql.window import Window

# Initialize Spark session (ensure the PostgreSQL JDBC driver is available)
spark = SparkSession.builder \
    .appName("RossmannFullFeatureEngineering") \
    .getOrCreate()

# PostgreSQL connection parameters
jdbc_url = "jdbc:postgresql://192.168.1.110:5000/rossman?sslmode=disable"
conn_props = {
    "user": "postgres",
    "password": "qaz123",
    "driver": "org.postgresql.Driver"
}

# ----------------------------
# 1. Load Raw Data from PostgreSQL
# ----------------------------
store_df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "Store") \
    .option("user", conn_props["user"]) \
    .option("password", conn_props["password"]) \
    .option("driver", conn_props["driver"]) \
    .load()

record_df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "Record") \
    .option("user", conn_props["user"]) \
    .option("password", conn_props["password"]) \
    .option("driver", conn_props["driver"]) \
    .load()

weather_df = spark.read.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "Weather") \
    .option("user", conn_props["user"]) \
    .option("password", conn_props["password"]) \
    .option("driver", conn_props["driver"]) \
    .load()

# ----------------------------
# 2. Process Record Data and Join with Store
# ----------------------------
# Convert record date to date type
record_df = record_df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))

# Join Record with Store on 'store'
df = record_df.join(store_df, on="store", how="left")

# ----------------------------
# 3. Add Basic Temporal Features from Record Date
# ----------------------------
df = df.withColumn("day", dayofmonth(col("date"))) \
       .withColumn("dayofweek", dayofweek(col("date"))) \
       .withColumn("dayofyear", date_format(col("date"), "D").cast("int")) \
       .withColumn("month", month(col("date"))) \
       .withColumn("week", weekofyear(col("date"))) \
       .withColumn("year", year(col("date")))

# Create a numeric version of the date (days since epoch) for windowing
df = df.withColumn("date_num", (unix_timestamp(col("date")) / 86400).cast("int"))

# ----------------------------
# 4. Convert Flag Columns to Integers
# ----------------------------
df = df.withColumn("open_flag", when(col("open")=="t", 1).otherwise(0)) \
       .withColumn("promo_flag", when(col("promo")=="t", 1).otherwise(0)) \
       .withColumn("schoolholiday_flag", when(col("schoolholiday")=="t", 1).otherwise(0)) \
       .withColumn("stateholiday_flag", when(col("stateholiday")=="t", 1).otherwise(0))

# ----------------------------
# 5. Shop-Level Aggregates (Other Store Info)
# ----------------------------
store_window = Window.partitionBy("store")
df = df.withColumn("sales_per_customer", col("sales") / col("customers")) \
       .withColumn("shopavg_open", avg("open_flag").over(store_window)) \
       .withColumn("shopavg_salespercustomer", avg("sales_per_customer").over(store_window)) \
       .withColumn("shopavg_schoolholiday", avg("schoolholiday_flag").over(store_window)) \
       .withColumn("shopsales_holiday", avg(when((col("schoolholiday_flag")==1) | (col("stateholiday_flag")==1), col("sales"))).over(store_window)) \
       .withColumn("shopsales_promo", avg(when(col("promo_flag")==1, col("sales"))).over(store_window)) \
       .withColumn("shopsales_saturday", avg(when(col("dayofweek")==7, col("sales"))).over(store_window))

# ----------------------------
# 6. Yesterday's Open Flag
# ----------------------------
store_order = Window.partitionBy("store").orderBy("date_num")
df = df.withColumn("dayavg_openyesterday", lag("open_flag", 1).over(store_order))

# ----------------------------
# 7. Promo and Competition Features
# ----------------------------
# Promo2, Promo2SinceWeek, Promo2SinceYear, promointerval come from the Store table (already joined)
# daysinpromocycle: assume a fixed 14-day cycle
df = df.withColumn("daysinpromocycle", col("date_num") % 14)
# primpromocycle: for illustration, set equal to promo_flag (placeholder)
df = df.withColumn("primpromocycle", col("promo_flag"))

# Competition features: construct competition_start date and compute daysincompetition
df = df.withColumn("competition_start", 
                   to_date(concat_ws("-", col("competitionopensinceyear"), col("competitionopensincemonth"), lit("01")), "yyyy-M-d"))
df = df.withColumn("daysincompetition", datediff(col("date"), col("competition_start")))
df = df.withColumn("daysincompetition_unrounded", col("daysincompetition"))
df = df.withColumn("rnd_CompetitionDistance", when(col("competitiondistance") > 0, round(log(col("competitiondistance")))).otherwise(lit(None)))

# ----------------------------
# 8. Holiday Counts (Temporal Information)
# ----------------------------
# Create a combined holiday flag
df = df.withColumn("holiday_flag", when((col("schoolholiday_flag")==1) | (col("stateholiday_flag")==1), 1).otherwise(0))
# Define windows for last week, this week, next week based on date_num
w_last7 = Window.partitionBy("store").orderBy("date_num").rangeBetween(-7, -1)
w_this7 = Window.partitionBy("store").orderBy("date_num").rangeBetween(0, 6)
w_next7 = Window.partitionBy("store").orderBy("date_num").rangeBetween(1, 7)
df = df.withColumn("holidays_lastweek", _sum("holiday_flag").over(w_last7)) \
       .withColumn("holidays_thisweek", _sum("holiday_flag").over(w_this7)) \
       .withColumn("holidays_nextweek", _sum("holiday_flag").over(w_next7))

# ----------------------------
# 9. Recent Data Features (Rolling Aggregates)
# ----------------------------
def add_rolling_feature(df, window_days, feature, alias_suffix=""):
    win = Window.partitionBy("store").orderBy("date_num").rangeBetween(-window_days, -1)
    return df.withColumn(f"prev{window_days}_{feature}{alias_suffix}", avg(col(feature)).over(win))

# Compute rolling averages for sales and customers over 90 (quarter), 180 (half-year), 365 (year) days
df = add_rolling_feature(df, 90, "sales")
df = add_rolling_feature(df, 180, "sales")
df = add_rolling_feature(df, 365, "sales")
df = add_rolling_feature(df, 90, "customers", "_cust")

# For features like median or harmonic mean (e.g., prevquarter_dps_med, prevquarter_med),
# we use avg as a placeholder (in practice, use UDFs for median/hmean)
df = df.withColumn("prevquarter_dps_med", avg(when(col("promo_flag")==1, col("sales"))).over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-90, -1)))
df = df.withColumn("prevquarter_med", avg("sales").over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-90, -1)))
df = df.withColumn("prevhalfyear", avg("sales").over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-180, -1)))
df = df.withColumn("prevyear_med", avg("sales").over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-365, -1)))
df = df.withColumn("prevquarter_cust_dps_med", avg(when(col("promo_flag")==1, col("customers"))).over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-90, -1)))
df = df.withColumn("prevyear_cust_dps_med", avg(when(col("promo_flag")==1, col("customers"))).over(Window.partitionBy("store").orderBy("date_num").rangeBetween(-365, -1)))

# ----------------------------
# 10. Last Month Year-over-Year (YoY) Change (Placeholder)
# ----------------------------
df = df.withColumn("lastmonth_yoy", (lag("sales", 30).over(store_order) - lag("sales", 365).over(store_order)) / lag("sales", 365).over(store_order))

# ----------------------------
# 11. Linear Trend Features (Current Trends)
# ----------------------------
# Compute quarterly trend (linmod_quarterly) as slope over previous 90 days
trend_win_90 = Window.partitionBy("store").orderBy("date_num").rangeBetween(-90, -1)
df = df.withColumn("avg_date_90", avg("date_num").over(trend_win_90)) \
       .withColumn("avg_sales_90", avg("sales").over(trend_win_90))
df = df.withColumn("cov_day_sales", avg((col("date_num") - col("avg_date_90"))*(col("sales") - col("avg_sales_90"))).over(trend_win_90)) \
       .withColumn("var_day", avg((col("date_num") - col("avg_date_90"))**2).over(trend_win_90))
df = df.withColumn("linmod_quarterly", col("cov_day_sales") / col("var_day"))

# Compute yearly trend (linmod_yearly) over previous 365 days
trend_win_365 = Window.partitionBy("store").orderBy("date_num").rangeBetween(-365, -1)
df = df.withColumn("avg_date_365", avg("date_num").over(trend_win_365)) \
       .withColumn("avg_sales_365", avg("sales").over(trend_win_365))
df = df.withColumn("cov_day_sales_365", avg((col("date_num") - col("avg_date_365"))*(col("sales") - col("avg_sales_365"))).over(trend_win_365)) \
       .withColumn("var_day_365", avg((col("date_num") - col("avg_date_365"))**2).over(trend_win_365))
df = df.withColumn("linmod_yearly", col("cov_day_sales_365") / col("var_day_365"))

# ----------------------------
# 12. Weather Features (Modified)
# ----------------------------
# Join weather data on date and matching state: assume Store has column 'storestate'
df = df.join(
    weather_df.select(
        to_date(col("date"), "yyyy-MM-dd").alias("wdate"),
        col("maxtemperaturec"),
        col("precipitationmm"),
        col("state").alias("wstate")
    ),
    (df.date == col("wdate")) & (df.storestate == col("wstate")),
    "left"
)
df = df.withColumn("weather_maxtemp", col("maxtemperaturec")) \
       .withColumn("weather_precip", col("precipitationmm"))

# Create a numeric version of wdate (in days since epoch) to use in the window range
df = df.withColumn("wdate_num", (unix_timestamp(col("wdate"))/86400).cast("long"))

# Relative weather: divide today's weather by average over last 7 days (by state)
weather_win = Window.partitionBy("wstate").orderBy("wdate_num").rangeBetween(-7, -1)
df = df.withColumn("avg_maxtemp_7", avg(col("maxtemperaturec")).over(weather_win))
df = df.withColumn("relativeweather_maxtemp", col("maxtemperaturec") / col("avg_maxtemp_7"))
df = df.withColumn("avg_precip_7", avg(col("precipitationmm")).over(weather_win))
df = df.withColumn("relativeweather_precip", col("precipitationmm") / col("avg_precip_7"))

# ----------------------------
# 13. Closure Feature
# ----------------------------
df = df.withColumn("closurefeat", when(col("open_flag") == 0, 1).otherwise(0))

# ----------------------------
# 14. Select Final Columns (as per your dictionary)
# ----------------------------
final_cols = [
    "id",
    "store", "customers", "storetype", "assortment",
    "shopavg_open", "shopavg_salespercustomer", "shopavg_schoolholiday",
    "shopsales_holiday", "shopsales_promo", "shopsales_saturday",
    "date",
    "day", "dayofweek", "dayofyear", "month", "week", "year",
    "dayavg_openyesterday",
    "Promo2", "Promo2SinceWeek", "Promo2SinceYear", "daysinpromocycle", "primpromocycle", "promo", "promointerval",
    "CompetitionDistance", "CompetitionOpenSinceMonth", "CompetitionOpenSinceYear", "daysincompetition", "daysincompetition_unrounded", "rnd_CompetitionDistance",
    "schoolholiday", "stateholiday", "holidays_lastweek", "holidays_nextweek", "holidays_thisweek",
    "prevquarter_dps_med", "prevhalfyear", "prevyear_med",
    "prevquarter_cust_dps_med", "prevyear_cust_dps_med",
    "lastmonth_yoy", "linmod_quarterly", "linmod_yearly",
    "weather_maxtemp", "weather_precip", "relativeweather_maxtemp", "relativeweather_precip",
    "closurefeat",
    "event_timestamp",  # ADDED: include event_timestamp column
    "sales"  # Target column added here
]

final_df = df.select(*final_cols)

# ----------------------------
# 15. Write Final Features to PostgreSQL
# ----------------------------
final_df.coalesce(5).write.format("jdbc") \
    .option("url", jdbc_url) \
    .option("dbtable", "new_record_features_all") \
    .option("user", conn_props["user"]) \
    .option("password", conn_props["password"]) \
    .option("driver", conn_props["driver"]) \
    .mode("overwrite") \
    .save()

spark.stop()