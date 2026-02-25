-- MAILTO: xiaohua.lu@5xgames.com
-- Environment: MaxCompute (ODPS)
-- Game: Slam Dunk TC (灌篮高手 繁体)
-- App ID: 23002013
-- Description: New users and 90-day returning users metrics (Size, Income, LTV)
-- Dimensions: Date, User Category, OS (Android/iOS)
-- Metrics: 
--   - Income: Day 1, 3, 6, 7, 14, 30, 60, 90 (Absolute cumulative revenue)
--   - LTV: Day 1, 3, 7, 14, 30, 60, 90 (Cumulative revenue per user)

SET odps.sql.hive.compatible = TRUE;

WITH 
    -- Step 1: Extract daily activity, include OS, and calculate gaps
    raw_activity AS (
        SELECT 
            device_id, 
            day, 
            purchase,
            reg_day,
            os,
            LAG(day, 1) OVER (PARTITION BY device_id ORDER BY day) as last_login_day
        FROM dm_platform.daily_lcx_user_info
        WHERE app_id = 23002013
          AND day >= 20250901 -- Look back ~4 months to identify 90-day churn
    ),
    
    -- Step 2: Identify New and Returning (90d+) Users with OS
    user_cohorts AS (
        SELECT
            device_id,
            os,
            day as cohort_date,
            CASE 
                WHEN CAST(reg_day AS BIGINT) = CAST(day AS BIGINT) THEN 'New User'
                ELSE 'Return User (30d+)'
            END as user_category
        FROM raw_activity
        WHERE day >= 20260205
          AND (
            -- Condition 1: New Registration
            CAST(reg_day AS BIGINT) = CAST(day AS BIGINT)
            OR 
            -- Condition 2: Returning after 90 days gap
            (
                CAST(reg_day AS BIGINT) < CAST(day AS BIGINT) -- Is an old user
                AND (
                    last_login_day IS NULL -- No login since at least 2025-09-01
                    OR 
                    DATEDIFF(TO_DATE(CAST(day AS STRING), 'yyyymmdd'), TO_DATE(CAST(last_login_day AS STRING), 'yyyymmdd'), 'dd') > 30
                )
            )
          )
    ),

    -- Step 3: Expand to include a 'Total' category for convenience
    expanded_cohorts AS (
        -- Per Category and OS
        SELECT device_id, os, cohort_date, user_category FROM user_cohorts
        UNION ALL
        -- Total Category per OS
        SELECT device_id, os, cohort_date, 'Total (New+Return)' as user_category FROM user_cohorts
    )

-- Step 4: Final Aggregation (Size, Income, LTV)
SELECT
    t.cohort_date AS "日期",
    t.user_category AS "用户类别",
    LOWER(t.os) AS "OS",
    COUNT(DISTINCT t.device_id) AS "人数",
    
    -- Income Calculation (Cumulative Revenue)
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 0 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入1",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 2 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入3",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 5 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入6",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 6 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入7",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 13 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入14",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 29 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入30",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 59 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入60",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 89 THEN COALESCE(p.purchase, 0) ELSE 0 END), 2) AS "收入90",

    -- LTV Calculation (Cumulative Revenue / Cohort Size)
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 0 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV1",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 2 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV3",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 6 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV7",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 13 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV14",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 29 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV30",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 59 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV60",
    ROUND(SUM(CASE WHEN DATEDIFF(TO_DATE(CAST(p.day AS STRING), 'yyyymmdd'), TO_DATE(CAST(t.cohort_date AS STRING), 'yyyymmdd'), 'dd') BETWEEN 0 AND 89 THEN COALESCE(p.purchase, 0) ELSE 0 END) / COUNT(DISTINCT t.device_id), 2) AS "LTV90"

FROM expanded_cohorts t
LEFT JOIN dm_platform.daily_lcx_user_info p 
    ON t.device_id = p.device_id 
    AND p.app_id = 23002013
    AND p.day >= t.cohort_date
GROUP BY 
    t.cohort_date, 
    t.user_category,
    t.os
ORDER BY 
    t.cohort_date DESC, 
    t.user_category,
    t.os;
