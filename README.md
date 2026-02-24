# FiveCross Unified Data Client

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Docker-Supported-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/Engines-TA%20%7C%20ODPS%20%7C%20Holo-orange.svg" alt="Engines">
  <img src="https://img.shields.io/badge/Security-Protected-green.svg" alt="Security">
</p>

A powerful and unified data extraction framework for ThinkingData (TA), AliCloud ODPS (MaxCompute), and Hologres. This project is the evolved version of `ali-data-client` and `thinking-data-client`, integrated into a professional "Data Worker" service.

## 🌟 Key Features

- **Multi-Engine Support**: 
  - `ta`: ThinkingData (Supports **China** and **Global** regions with auto-login).
  - `odps`: AliCloud MaxCompute (Supports China and Global regions).
  - `holo`: AliCloud Hologres (Postgres-compatible).
- **Intelligent Emailing**: 
  - Send reports with multiple attachments to multiple recipients.
  - Parse recipients directly from SQL comments (`-- MAILTO: ...`).
- **Flexible Workflows**:
  - **Scheduled Tasks**: Define multiple queries in a single JSON file and run them all at once.
  - **Ad-hoc Queries**: Powerful CLI for single queries with data preview.
- **Advanced Export (xlsx, csv, txt, json)**:
  - Automatic format conversion for raw downloads (e.g., TA's CSV to Excel).
- **Robustness**:
  - Playwright-based smart login for TA (Auto-fill + Enter fallback).
  - Session persistence via persistent browser context.
- **Private SQL Library**: Securely integrated via Git Submodules.
- **One-Click Setup**: Automated environment initialization.

## 🛠 Setup & Initialization

### 1. Local Environment (Windows)
We provide a one-click setup script to handle Python VENV, dependencies, and Playwright drivers.
1.  **Clone the project**:
    ```bash
    git clone --recursive https://github.com/yukhyohwa/fivecross-data-client.git
    cd fivecross-data-client
    ```
2.  **Run Setup**:
    Double-click `setup.bat` or run `.\setup.bat`.
3.  **Configure `.env`**:
    - **ThinkingData**: Set `TA_USER_CN`/`TA_PASS_CN` or `TA_USER_GLOBAL`/`TA_PASS_GLOBAL`.
    - **AliCloud**: Set `ALIYUN_AK_CN`/`ALIYUN_SK_CN` and endpoint variables.
    - **Email**: Configure `SMTP_SERVER`, `SENDER_EMAIL`, and `SENDER_PASSWORD` (App Password).

### 2. Docker (Containerized)
Ideal for scheduled tasks on Linux servers.
```bash
docker build -t fivecross-client .
docker run --env-file .env fivecross-client --engine ta --sql "SELECT ..."
```

## 📖 Usage

### 1. Ad-hoc Queries (IDE & CLI)
```bash
# ThinkingData (Default: Global)
python main.py --engine ta --region global --file queries/adhoc_ta.sql

# AliCloud ODPS (Default: Global)
python main.py --engine odps --region global --file queries/adhoc_ali.sql

# Using the integrated SQL library
python main.py --engine ta --file queries/sql-lib/games/slam_dunk/maxcompute/active_users.sql

# Direct SQL strings
python main.py --engine odps --sql "SELECT count(*) FROM ods_log_login WHERE day='20240101'"
```

### 2. Scheduled Multi-Tasks & Automation
Edit `tasks/scheduled_multi_tasks.json` to define your suite of reports:
```json
[
  {
    "name": "Daily_China_Stats",
    "engine": "ta", "region": "china",
    "file": "queries/daily_stats.sql",
    "mailto": "boss@example.com",
    "formats": ["xlsx"]
  }
]
```
**Trigger the tasks:**
```bash
# Windows (Manual)
.\scripts\run_query.bat

# Manual CLI
python main.py --task tasks/scheduled_multi_tasks.json
```

## 🕒 Windows Task Scheduler (Automation)
To run your reports automatically every day:
1.  **Open Task Scheduler**: Press `Win + R`, type `taskschd.msc`, and hit Enter.
2.  **Create Basic Task**:
    - Name: `FiveCross_Daily_Report`
    - Trigger: `Daily` (e.g., 08:30 AM)
    - Action: `Start a program`
3.  **Configure Action**:
    - Program/script: `C:\Users\5xgames\Desktop\github\fivecross-data-client\scripts\run_query.bat`
    - Start in (optional): `C:\Users\5xgames\Desktop\github\fivecross-data-client\`
4.  **Security Options**: (Optional) In the Task Properties, check "Run whether user is logged on or not" and "Run with highest privileges" for better reliability.

### 3. Log Seeker (Tool)
Quickly locate specific IDs within massive local CSV logs:
```bash
python tools/log_seek.py 78128243 90000730
```

## ⚙️ CLI Arguments
| Argument | Description | Options |
| :--- | :--- | :--- |
| `--engine` | Output target engine | `ta`, `odps`, `holo` |
| `--region` | Target region | `china`, `global` (Default) |
| `--file` | Path to SQL file | e.g. `queries/adhoc.sql` |
| `--sql` | Direct SQL string | Any valid SQL |
| `--task` | Multi-task JSON path | e.g. `tasks/daily.json` |
| `--mailto` | Recipient emails | Comma separated |
| `--formats` | Export formats | `xlsx`, `csv`, `txt`, `json` |
| `--show` | Display browser | TA engine only |
| `--login` | Force login flow | TA engine only |

## 🔒 Security & Privacy
- **.env**: Never committed to Git. Local credentials stay local.
- **submodules**: The `sql-lib` is a private repository. External users cannot access your SQL logic even if they have this tool's code.

## 📝 SQL Directives
Add recipients directly in your SQL files:
```sql
-- MAILTO: analytics@example.com, boss@example.com
SELECT * FROM ...
```

## 📂 Project Structure
- `src/core/`: Engine logic (TA, ODPS, Holo).
- `src/utils/`: Exporter, Mailer, and Logger utilities.
- `queries/sql-lib/`: **[Private Submodule]** The shared internal SQL library.
- `tools/`: Built-in utilities (Log Seeker, etc.).
- `output/`: Generated reports and debug snapshots.
- `setup.bat`: One-click initialization script.
