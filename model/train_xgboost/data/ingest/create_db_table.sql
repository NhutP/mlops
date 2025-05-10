-- Connect initially to the default database (this script should be run against "postgres")
-- Ensure the dblink extension is available.
CREATE EXTENSION IF NOT EXISTS dblink;

-- Use a DO block to check if "rossman" exists, and if not, create it using dblink_exec.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'rossman') THEN
        PERFORM dblink_exec(
            'dbname=postgres host=192.168.1.110 port=5000 user=postgres password=qaz123'::text,
            'CREATE DATABASE rossman'::text
        );
        RAISE NOTICE 'Database rossman created.';
    ELSE
        RAISE NOTICE 'Database rossman already exists.';
    END IF;
END $$;

\echo 'Finished checking/creating rossman database.'

-- Now connect to the rossman database on the remote server.
\connect rossman postgres 192.168.1.110 5000

\echo 'Connected to rossman database.'

-- Create the "Rossman" table.
CREATE TABLE IF NOT EXISTS Record (
    id SERIAL PRIMARY KEY,
    store VARCHAR(10) NOT NULL,
    dayOfWeek INT,
    "date"  DATE,
    sales INT,
    customers INT,
    "open" BOOLEAN,
    promo BOOLEAN,
    schoolHoliday BOOLEAN,
    stateHoliday CHAR(1),
    event_timestamp TIMESTAMP DEFAULT NOW()
);

-- ALTER TABLE record_features_all
-- ALTER COLUMN "date" TYPE TEXT USING TO_CHAR("date", 'YYYY-MM-DD');

-- ALTER TABLE Record
-- ALTER COLUMN "date" TYPE TEXT USING TO_CHAR("date", 'YYYY-MM-DD');

-- Create the "Rating" table.
CREATE TABLE IF NOT EXISTS Store (
    store  VARCHAR(10),
    storeType CHAR(1),
    assortment CHAR(1),
    competitionDistance INT,
    competitionOpenSinceMonth INT,
    competitionOpenSinceYear INT,
    promo2 BOOLEAN,
    promo2SinceWeek INT,
    promo2SinceYear INT,
    promoInterval VARCHAR(50),
    storeState VARCHAR(5)
);


CREATE TABLE Weather (
    "date" DATE,
    maxTemperatureC INTEGER,
    meanTemperatureC INTEGER,
    minTemperatureC INTEGER,
    dewPointC INTEGER,
    meanDewPointC INTEGER,
    minDewpointC INTEGER,
    maxHumidity INTEGER,
    meanHumidity INTEGER,
    minHumidity INTEGER,
    maxSeaLevelPressurehPa INTEGER,
    meanSeaLevelPressurehPa INTEGER,
    minSeaLevelPressurehPa INTEGER,
    maxVisibilityKm INTEGER,
    meanVisibilityKm INTEGER,
    minVisibilityKm INTEGER,
    maxWindSpeedKmH INTEGER,
    meanWindSpeedKmH INTEGER,
    maxGustSpeedKmH INTEGER,
    precipitationMm NUMERIC,
    cloudCover INTEGER,
    events VARCHAR(50),
    windDirDegrees INTEGER,
    "state" VARCHAR(5)
);


\echo 'Tables created successfully in rossman database.'