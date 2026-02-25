/*
================================================================================
Game: Kuroko's Basketball (繁體黑子)
Region: TC (Traditional Chinese)
Description: 3. 籃球寶箱 (Basketball Chest Output)
================================================================================
*/
SELECT 
    CASE id 
        WHEN '1610041' THEN '麥迪籃球寶箱(1610041)'
        WHEN '1610035' THEN 'LG赤司籃球寶箱(1610035)'
        WHEN '1610038' THEN 'LG青峰籃球寶箱(1610038)'
    END AS chest_name,
    CASE id 
        WHEN '1610041' THEN '2026-02-05 09:00 ~ 2026-02-28 23:59'
        WHEN '1610035' THEN '2025-11-06 10:00 ~ 2025-11-26 23:59'
        WHEN '1610038' THEN '2026-01-01 00:00 ~ 2026-01-21 23:59'
    END AS period,
    SUM(TRY_CAST(diff AS BIGINT)) AS output_count
FROM ta.v_event_10
CROSS JOIN UNNEST(a_rst) AS t(id, "before", diff, "after", "key")
WHERE "$part_date" >= '2025-11-06' AND "$part_date" <= '2026-02-28'
  AND TRY_CAST(diff AS BIGINT) > 0 
  AND (
      (id = '1610041' AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59') OR
      (id = '1610035' AND "#event_time" BETWEEN TIMESTAMP '2025-11-06 10:00:00' AND TIMESTAMP '2025-11-26 23:59:59') OR
      (id = '1610038' AND "#event_time" BETWEEN TIMESTAMP '2026-01-01 00:00:00' AND TIMESTAMP '2026-01-21 23:59:59')
  )
GROUP BY 1, 2
