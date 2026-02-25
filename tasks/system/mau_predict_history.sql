-- Index. MAU Predict History
-- Description: Historical data for MAU prediction.

SELECT data_date, 
    COUNT(DISTINCT CASE WHEN user_type = 'nuu' THEN lcm_id ELSE NULL END) AS nuu,
    COUNT(DISTINCT CASE WHEN user_type = 'ouu' THEN lcm_id ELSE NULL END) AS ouu,
    COUNT(DISTINCT CASE WHEN user_type = 'ruu' THEN lcm_id ELSE NULL END) AS ruu,
    ROUND(COUNT(DISTINCT CASE WHEN user_type = 'nuu' AND if_stay = 1 THEN lcm_id ELSE NULL END) / COUNT(DISTINCT CASE WHEN user_type = 'nuu' THEN lcm_id ELSE NULL END), 4) AS nuu_retention_rate,
    ROUND(COUNT(DISTINCT CASE WHEN user_type = 'ouu' AND if_stay = 1 THEN lcm_id ELSE NULL END) / COUNT(DISTINCT CASE WHEN user_type = 'ouu' THEN lcm_id ELSE NULL END), 4) AS ouu_retention_rate,
    ROUND(COUNT(DISTINCT CASE WHEN user_type = 'ruu' AND if_stay = 1 THEN lcm_id ELSE NULL END) / COUNT(DISTINCT CASE WHEN user_type = 'ruu' THEN lcm_id ELSE NULL END), 4) AS ruu_retention_rate
FROM 
(
    SELECT a.data_date, a.lcm_id, user_type, CASE WHEN b.lcm_id IS NOT NULL THEN 1 ELSE 0 END AS if_stay
    FROM 
    (
        SELECT SUBSTR(TO_DATE(month, 'yyyyMM'), 1, 10) AS data_date, lcm_id, user_type
        FROM dm_platform.monthly_lcx_user_info 
        WHERE app_id = '{app_id}'
            AND month >= '{start_month}'
            AND month <= '{end_month}'
            AND is_water = '不是水'
            AND is_black = '不是黑'
    ) a
    LEFT JOIN
    (
        SELECT SUBSTR(TO_DATE(month, 'yyyyMM'), 1, 10) AS data_date, lcm_id
        FROM dm_platform.monthly_lcx_user_info 
        WHERE app_id = '{app_id}'
            AND month >= '{start_month}'
    ) b ON a.lcm_id = b.lcm_id AND MONTHS_BETWEEN(b.data_date, a.data_date) = 1
) x
GROUP BY data_date
ORDER BY data_date
