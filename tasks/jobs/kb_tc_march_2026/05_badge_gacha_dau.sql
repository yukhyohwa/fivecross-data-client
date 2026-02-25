/*
================================================================================
Game: Kuroko's Basketball (繁體黑子)
Region: TC (Traditional Chinese)
Description: 6. 玩法狀況 - 徽章扭蛋 每日參與人數 (Gameplay DAU)
================================================================================
*/
SELECT 
    "$part_date" AS gacha_date,
    COUNT(DISTINCT "#user_id") AS daily_participants
FROM ta.v_event_10
WHERE "$part_date" BETWEEN '2026-02-05' AND '2026-02-28'
  AND "#event_time" BETWEEN TIMESTAMP '2026-02-05 09:00:00' AND TIMESTAMP '2026-02-28 23:59:59'
  AND "$part_event" = 'badge_gacha' 
GROUP BY 1
ORDER BY 1
