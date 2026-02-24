# FiveCross Unified Data Client

A powerful and unified data extraction framework for ThinkingData (TA), AliCloud ODPS (MaxCompute), and Hologres. Designed for both quick ad-hoc analysis and scheduled multi-task reporting.

## 🌟 Key Features

- **Multi-Engine Support**: 
  - `ta`: ThinkingData (Supports **China** and **Global** regions with auto-login).
  - `odps`: AliCloud MaxCompute (Supports China and Global regions).
  - `holo`: AliCloud Hologres (Postgres-compatible).
- **Flexible Workflows**:
  - **Scheduled Tasks**: Define multiple queries in a single JSON file and run them all at once.
  - **Ad-hoc Queries**: Powerful CLI for single queries with data preview and interactive download options.
- **Advanced Export (xlsx, csv, txt, json)**:
  - Supports multiple formats per task.
  - Automatic format conversion for raw downloads (e.g., TA's CSV to Excel).
- **Intelligent Emailing**:
  - Send reports with multiple attachments to multiple recipients.
  - Parse recipients directly from SQL comments (`-- MAILTO: ...`).
- **Robustness**:
  - Smart login mechanism (Auto-fill + Enter fallback) for ThinkingData.
  - Session persistence via persistent browser context.
  - Debug screenshots and logs on failure.

## 🛠 Setup

1. **Environment Preparation** (Recommended: Python 3.10+):
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configuration**:
   - Create a `.env` file based on `.env.example`.
   - **ThinkingData**: Set `TA_USER_CN`/`TA_PASS_CN` for China and `TA_USER_GLOBAL`/`TA_PASS_GLOBAL` for Global.
   - **AliCloud**: Ensure `ALIYUN_AK_CN`/`ALIYUN_SK_CN` and `ALIYUN_AK_OVERSEAS`/`ALIYUN_SK_OVERSEAS` are set.
   - Set `USER_DATA_DIR` to maintain browser sessions.

## 📖 Usage

### 1. One-Click Scheduled Tasks (Recommended)
Simply edit `tasks/scheduled_multi_tasks.json` to define your tasks, then run:
```bash
# Via script
.\scripts\run_query.bat

# Via command line
python main.py --task tasks/scheduled_multi_tasks.json
```

### 2. Interactive Ad-hoc Queries
Run single queries with a **Data Preview** and interactive options for naming and formats:
```bash
# ThinkingData (Default: Global)
python main.py --engine ta --file queries/adhoc_ta.sql

# ThinkingData (China)
python main.py --engine ta --region china --file queries/adhoc_ta.sql

# AliCloud ODPS (Default: Global)
python main.py --engine odps --file queries/adhoc_ali.sql
```
*Note: Interactive mode is automatically enabled for single engine runs.*

### 3. CLI Arguments
- `--engine`: [ta, odps, holo]
- `--region`: [china, global] (Default: global)
- `--file`: Path to SQL file.
- `--sql`: Direct SQL string.
- `--mailto`: Recipient emails (comma separated).
- `--formats`: Output formats (e.g., `xlsx,csv`).
- `--show`: Display browser (TA engine only).
- `--login`: Force login flow (TA engine only).

## 📂 Task Configuration (JSON)
Tasks are defined in `tasks/scheduled_multi_tasks.json`:
```json
[
  {
    "name": "Daily_China_Stats",
    "engine": "ta",
    "region": "china",
    "file": "queries/daily_stats.sql",
    "mailto": "boss@example.com",
    "formats": ["xlsx"]
  },
  {
    "name": "Daily_Global_Stats",
    "engine": "ta",
    "region": "global",
    "file": "queries/global_stats.sql",
    "formats": ["csv"]
  }
]
```

## 📝 SQL Directives
You can specify recipients directly in your SQL file:
```sql
-- MAILTO: user1@example.com, user2@example.com
SELECT * FROM ...
```

## 📁 Project Structure
- `src/core/`: Engine logic (ThinkingData, AliCloud).
- `src/utils/`: Exporter, Mailer, and Logger utilities.
- `tasks/`: Multi-task configuration files.
- `output/`: Generated reports and debug logs.
- `scripts/`: Batch scripts for quick execution.
