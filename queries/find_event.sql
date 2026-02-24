-- =================================================================================
-- 模板说明：用于快速定位 ID 所属事件的查询脚本
-- 核心功能：通过排除高频且无关的日志事件（如点击、启动、战斗等），精准获取道具产出和活动相关的日志。
-- =================================================================================

-- 优化建议：通过显式指定字段（已剔除 280+ 个空列）可大幅减少 CSV 体积并提升下载速度
SELECT 
    "#user_id",      -- 用户唯一标识
    "#event_name",    -- 事件名
    "#event_time",    -- 日志时间
    "#account_id",    -- 账号ID
    "$part_event",    -- 分区事件
    "item_id",        -- 道具ID
    "reason",         -- 原因/来源
    "item_num",       -- 数量
    "level_id"        -- 关卡/场景ID
    -- 如需增加其他字段，请在此输入
FROM ta.v_event_10
WHERE "$part_date" >= '2026-02-03'                      -- 设置查询开始日期
  AND "$part_date" <= '2026-02-03'                      -- 设置查询结束日期

-- 【关键：屏蔽列表】排除掉异常高频、下载量巨大且通常与道具产出无关的事件
AND "$part_event" NOT IN (
    'button_click',          -- 按钮点击
    'friend_gift',           -- 好友赠礼
    'summary_login',         -- 登录汇总
    'player_activity',       -- 会话活跃
    'login',                -- 登录
    'gamer_guide',          -- 新手引导
    'trust_camp_result',    -- 模型结果
    'match_start',          -- 匹配开始
    'pvp_info',             -- PVP信息
    'battle_result',        -- 战斗结果
    'vsloading',            -- 加载界面
    'fight_data',           -- 战斗数据
    'player_send_refresh',  -- 刷新分发
    'card_skillrune',       -- 技能符文
    'gin_monopoly_roll',    -- 大富翁掷骰
    'sign',                 -- 签到
    'change_name'           -- 改名
)

-- 精确过滤时间段（可选）
AND "#event_time" >= timestamp '2026-02-03 11:00:00' 
AND "#event_time" <= timestamp '2026-02-03 13:00:00'
