/*
================================================================================
Game: Kuroko's Basketball (繁體黑子)
Region: TC (Traditional Chinese)
Description: 1. 球員產出與時裝持有狀況 (Player & Costume Output Status)
================================================================================
*/
WITH ItemOutput AS (
    SELECT 
        id AS item_id,
        SUM(TRY_CAST(diff AS BIGINT)) AS total_output
    FROM ta.v_event_10
    CROSS JOIN UNNEST(a_rst) AS t(id, "before", diff, "after", "key")
    WHERE "$part_date" >= '2025-11-06' AND "$part_date" <= '2026-02-28'
      AND TRY_CAST(diff AS BIGINT) > 0 
      AND (
          -- Players
          (id = '99600403' AND "#event_time" BETWEEN TIMESTAMP '2025-11-06 10:00:00' AND TIMESTAMP '2025-11-26 23:59:59') OR
          (id = '99100402' AND "#event_time" BETWEEN TIMESTAMP '2025-12-04 10:00:00' AND TIMESTAMP '2025-12-25 08:59:59') OR
          (id = '99400503' AND "#event_time" BETWEEN TIMESTAMP '2026-01-01 00:00:00' AND TIMESTAMP '2026-01-21 23:59:59') OR
          (id = '99900601' AND "#event_time" BETWEEN TIMESTAMP '2026-01-22 00:00:00' AND TIMESTAMP '2026-02-05 08:59:59') OR
          (id = '99210101' AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59') OR
          -- Costumes (Lifetime output / Held count)
          (id IN ('96600461', '96100431', '96400542', '96900602', '96210102'))
      )
    GROUP BY 1
),
PlayerReport AS (
    SELECT 
        'LG赤司(99600403)' AS player_name,
        '2025-11-06 10:00 ~ 2025-11-26 23:59' AS period,
        (SELECT total_output FROM ItemOutput WHERE item_id = '99600403') AS player_output,
        '96600461' AS costume_id,
        (SELECT total_output FROM ItemOutput WHERE item_id = '96600461') AS costume_held
    UNION ALL
    SELECT 'LG日向(99100402)', '2025-12-04 10:00 ~ 2025-12-25 08:59', (SELECT total_output FROM ItemOutput WHERE item_id = '99100402'), '96100431', (SELECT total_output FROM ItemOutput WHERE item_id = '96100431')
    UNION ALL
    SELECT 'LG青峰(99400503)', '2026-01-01 00:00 ~ 2026-01-21 23:59', (SELECT total_output FROM ItemOutput WHERE item_id = '99400503'), '96400542', (SELECT total_output FROM ItemOutput WHERE item_id = '96400542')
    UNION ALL
    SELECT '灰崎(99900601)', '2026-01-22 00:00 ~ 2026-02-05 08:59', (SELECT total_output FROM ItemOutput WHERE item_id = '99900601'), '96900602', (SELECT total_output FROM ItemOutput WHERE item_id = '96900602')
    UNION ALL
    SELECT '麥迪(99210101)', '2026-02-05 09:00 ~ 2026-02-28 23:59', (SELECT total_output FROM ItemOutput WHERE item_id = '99210101'), '96210102', (SELECT total_output FROM ItemOutput WHERE item_id = '96210102')
)
SELECT * FROM PlayerReport
