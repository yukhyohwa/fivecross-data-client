/*
================================================================================
Game: Kuroko's Basketball (繁體黑子)
Region: TC (Traditional Chinese)
Description: 4 & 5. 二週年期間 與 NBA活動期間 用戶數量 (Anniversary & NBA New/Returning Users)
================================================================================
*/
WITH UserSessions AS (
    SELECT 
        "#user_id",
        "$part_date",
        "#event_time",
        LAG("#event_time") OVER (PARTITION BY "#user_id" ORDER BY "#event_time" ASC) AS prev_login_time,
        MIN("$part_date") OVER (PARTITION BY "#user_id") AS reg_date
    FROM ta.v_event_10
    WHERE "$part_event" = 'login'
),
FlaggedUsers AS (
    SELECT 
        "#user_id",
        CASE WHEN reg_date BETWEEN '2026-01-22' AND '2026-02-05' 
             AND "#event_time" BETWEEN TIMESTAMP '2026-01-22 00:00:00' AND TIMESTAMP '2026-02-05 08:59:59' THEN 1 ELSE 0 END AS is_anniv_new,
        CASE WHEN DATE_DIFF('day', CAST(prev_login_time AS DATE), CAST("$part_date" AS DATE)) >= 30
             AND "#event_time" BETWEEN TIMESTAMP '2026-01-22 00:00:00' AND TIMESTAMP '2026-02-05 08:59:59' THEN 1 ELSE 0 END AS is_anniv_return,
             
        CASE WHEN reg_date BETWEEN '2026-02-05' AND '2026-02-28'
             AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59' THEN 1 ELSE 0 END AS is_nba_new,
        CASE WHEN DATE_DIFF('day', CAST(prev_login_time AS DATE), CAST("$part_date" AS DATE)) >= 30
             AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59' THEN 1 ELSE 0 END AS is_nba_return
    FROM UserSessions
)
SELECT 
    '二週年期間 (2026-01-22 00:00 ~ 2026-02-05 08:59)' AS period,
    COUNT(DISTINCT CASE WHEN is_anniv_new = 1 THEN "#user_id" END) AS new_users,
    COUNT(DISTINCT CASE WHEN is_anniv_return = 1 THEN "#user_id" END) AS return_users
FROM FlaggedUsers
UNION ALL
SELECT 
    'NBA活動期間 (2026-02-05 09:00 ~ 2026-02-28 23:59)',
    COUNT(DISTINCT CASE WHEN is_nba_new = 1 THEN "#user_id" END),
    COUNT(DISTINCT CASE WHEN is_nba_return = 1 THEN "#user_id" END)
FROM FlaggedUsers
