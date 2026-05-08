CREATE TABLE IF NOT EXISTS FROSTLINE.RAW.REVIEW_STARS_AGG (
    business_id STRING,
    avg_stars FLOAT,
    review_count INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TASK FROSTLINE.RAW.REVIEW_STREAM_TASK
    WAREHOUSE = FROSTLINE_WH
    SCHEDULE = '1 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('FROSTLINE.RAW.REVIEW_STREAM')
AS
    MERGE INTO FROSTLINE.RAW.REVIEW_STARS_AGG t
    USING (
        SELECT DATA:business_id::STRING AS business_id,
               AVG(DATA:stars::FLOAT) AS avg_stars,
               COUNT(*) AS review_count
        FROM FROSTLINE.RAW.REVIEW_STREAM
        GROUP BY DATA:business_id::STRING
    ) s
    ON t.business_id = s.business_id
    WHEN MATCHED THEN UPDATE SET
        t.avg_stars = s.avg_stars,
        t.review_count = t.review_count + s.review_count,
        t.last_updated = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (business_id, avg_stars, review_count)
        VALUES (s.business_id, s.avg_stars, s.review_count);

ALTER TASK FROSTLINE.RAW.REVIEW_STREAM_TASK RESUME;