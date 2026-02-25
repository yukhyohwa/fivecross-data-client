/*
================================================================================
Game: Kuroko's Basketball (繁體黑子)
Region: TC (Traditional Chinese)
Description: 2. 球場販售狀況 (Court Sales Status)
================================================================================
*/
SELECT 
    CASE id 
        WHEN '50201037' THEN '火箭球場(50201037)'
        WHEN '50201036' THEN '海底球場(50201036)'
    END AS court_name,
    CASE id 
        WHEN '50201037' THEN '2026-02-05 09:00 ~ 2026-02-28 23:59'
        WHEN '50201036' THEN '2026-02-12 00:00 ~ 2026-02-25 23:59'
    END AS period,
    CASE id 
        WHEN '50201037' THEN '累儲8000點券'
        WHEN '50201036' THEN '春節扭蛋'
    END AS method,
    SUM(TRY_CAST(diff AS BIGINT)) AS output_count
FROM ta.v_event_10
CROSS JOIN UNNEST(a_rst) AS t(id, "before", diff, "after", "key")
WHERE "$part_date" >= '2026-02-05' AND "$part_date" <= '2026-02-28'
  AND TRY_CAST(diff AS BIGINT) > 0 
  AND (
      (id = '50201037' AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59') OR
      (id = '50201036' AND "#event_time" BETWEEN TIMESTAMP '2026-02-12 00:00:00' AND TIMESTAMP '2026-02-25 23:59:59')
  )
GROUP BY 1, 2, 3
