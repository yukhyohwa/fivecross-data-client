# FiveCross Data Client

A unified data extraction tool for FiveCross game operations. It retrieves data from **ThinkingData (TA)**, **AliCloud ODPS**, and **Hologres**. Forecasting is maintained separately in `fivecross-forecast-models`, which calls this client for online inputs.

## 🔌 Integration Methods

This project combines three integration approaches, selected according to each platform's supported access method:

| Platform | Implementation | General name |
| --- | --- | --- |
| ThinkingData (TA) | Uses Playwright to sign in to and operate the web SQL IDE, then reads query results from the browser session. | **Web UI automation** / **Browser automation** |
| AliCloud MaxCompute (ODPS) | Uses AliCloud AccessKey credentials and the `pyodps` SDK to submit SQL and retrieve results. | **API/SDK integration** / **Cloud service SDK integration** |
| AliCloud Hologres | Connects with `psycopg2` and executes SQL directly. | **Direct database connection** (Database Connectivity) |

> In short: TA access is browser automation, while ODPS and Hologres use direct programmatic integrations rather than GUI automation.

## 📁 Architecture Overview

FCDC follows a three-layer architecture to decouple business logic, execution configuration, and physical data.

* **`main.py`**: The central entry point for all operations.
* **`data/`**: Physical data storage (Git-ignored).
  * `output/`: Unified directory for query results.
* **`tasks/`**: Logic and Configuration.
  * `templates/`: **[Git Submodule]** Linked to `fivecross-sql-lib`. Contains game-specific SQL templates organized by Game/Region.
  * `configs/`: Operational parameters in JSON format.
    * `scheduled/`: Automated batch jobs (Day/Week/Month).
    * `adhoc/`: On-demand query configurations (successor to the old `queries` folder).
* **`scripts/`**: Automation and environment management utilities.

## 🚀 Getting Started

### 1. Initial Setup (Windows)

Run the setup script to initialize the Python environment and install dependencies:

```powershell
.\scripts\setup_env.bat
```

This script handles Virtualenv creation, pip dependency installation, and Playwright browser provisioning.

### 2. Command Usage

The CLI supports `fetch` for data extraction and `--login` for ThinkingData session setup.

#### Data Fetching

FCDC features a recursive search engine that locates files automatically within the `tasks/` directory.

```bash
# Quick Ad-hoc execution from the designated adhoc folder
python main.py fetch --engine ta --region global --file adhoc_ta.sql
python main.py fetch --engine odps --region global --file adhoc_ali.sql

# Execute a specific SQL file from templates/
python main.py fetch --engine ta --file kb_jp_insignia_gacha.sql --region global

# Execute a batch configuration from configs/
python main.py fetch --task scheduled_multi_tasks.json

# Interactive mode (provides data preview before export)
python main.py fetch --engine odps --file ltv_stats.sql --interactive

# Show browser window during execution (TA only)
python main.py fetch --engine ta --file adhoc_ta.sql --show
```

#### Forecasting has moved

LTV and MAU forecasting now belong to [fivecross-forecast-models](https://github.com/yukhyohwa/fivecross-forecast-models). Input files are maintained there under `data/input/`. The `predict` command has been removed. This client retains database access, login recovery, exports and scheduled fetch tasks.

#### Log Seeker (ID Lookup Tool)

A high-performance utility to scan massive CSV logs for specific user IDs or identifiers:

```bash
# Automatically finds the latest CSV in data/output/ and searches for ID
python tools\log_seek.py3010522

# Search for multiple IDs
python tools\log_seek.py ID1 ID2 ID3

# Specify a custom CSV path
python tools\log_seek.py 300000046 --path data\output\fullitemuselogs_20260520_0605_20260605_141238.csv
```

### 3. Task Configuration (JSON Schema)

Batch tasks in `tasks/configs/` support various parameters for advanced automation:

| Parameter   | Type   | Description                                    |
| :---------- | :----- | :--------------------------------------------- |
| `name`    | string | Prefix for the exported file.                  |
| `engine`  | string | `ta`, `odps`, or `holo`.                 |
| `region`  | string | `global` or `china`.                       |
| `file`    | string | SQL filename (auto-searched in`templates/`). |
| `sql`     | string | Direct SQL string (overrides`file`).         |
| `mailto`  | string | Comma-separated emails for automated delivery. |
| `formats` | list   | Export types:`["xlsx", "csv", "json"]`.      |

**Example `scheduled_multi_tasks.json`:**

```json
{
    "name": "daily_revenue_report",
    "engine": "ta",
    "file": "daily_stats.sql",
    "mailto": "admin@example.com, analyst@example.com",
    "formats": ["xlsx"]
}
```

### 4. Advanced Features

#### Automated Email Delivery

FCDC automatically parses email recipients from two sources:

1. The `mailto` field in your JSON configuration.
2. The **SQL Comment Header**: Adding `-- MAILTO: user@example.com` as the first line of your `.sql` file will automatically trigger an email dispatch upon task completion.

#### Dynamic ID Lookup (SQL Templates)

Leverage the **Git Submodule** in `tasks/templates/` to share common logic across projects. You can store your "ID Mapping" or "Static Metadata" SQLs in `common/` for reuse in multiple game-specific tasks.

### 5. ThinkingData (TA) Login & Region Management

The TA engine supports automated login and session persistence across multiple regions.

#### Multi-Region Support

Specify the target TA instance using the `--region` flag:

- `global`: Connects to the Global TA instance (e.g., Aliyun Hong Kong).
- `china`: Connects to the China TA instance.

#### Automated Login & Session Persistence

- **Session Storage**: Browser sessions are saved in the `ta_session/` directory, valid for up to 7 days.
- **Auto-Recovery**: If a session expires, the engine automatically:
  1. Clears the stale session data.
  2. Performs a fresh login using credentials from `.env`.
  3. Re-establishes the 7-day session.
- **Manual Login**: If you need to force a fresh login or establish a session for the first time:
  ```bash
  python main.py --login --region global
  ```

#### Required Configuration (.env)

Ensure your `.env` file contains the correct credentials for each region:

```env
# Global TA
TA_URL_GLOBAL=http://...
TA_USER_GLOBAL=your_user
TA_PASS_GLOBAL=your_password

# China TA
TA_URL_CN=https://...
TA_USER_CN=your_user
TA_PASS_CN=your_password
```

### 6. Windows Automation (Task Scheduler)

To fully automate your workflow:

1. Open **Windows Task Scheduler**.
2. Create a **New Basic Task** and set your desired trigger (e.g., Daily 8:00 AM).
3. For Action, select **Start a Program**.
4. **Program/script**: Browse to your FCDC root and select `scripts/run_scheduled_tasks.bat`.
5. **Start in**: Set this to the absolute path of your `fivecross-data-client` directory (Critical for path resolution).

## 🔄 SQL Library Synchronization

Since SQL templates are managed in a separate repository, synchronize the latest business logic via:

```bash
git submodule update --remote --merge
```

## 🛠️ Configuration

Manage your credentials and endpoints in the `.env` file at the project root. Refer to `.env.example` for the required schema.

## ⚠️ Known Issues & Solutions

### TA Engine: Monaco Editor Fails to Load Without `--show`

**Symptom:**
Running a TA fetch command without `--show` fails with a 30-second timeout:

```
ERROR  Execution failed: Page.wait_for_selector: Timeout 30000ms exceeded.
       waiting for locator(".monaco-editor, ...")
WARNING  No data found for preview.
```

Page title captured at failure is `加载中...` and any screenshot is pure white.

**Root Cause:**
The ThinkingData IDE is a heavy SPA that uses Monaco Editor (same engine as VS Code). This framework requires a **real browser rendering environment** to initialize:

| Requirement                  | Headless Chromium      | Headed Chromium (off-screen) |
| ---------------------------- | ---------------------- | ---------------------------- |
| GPU rendering pipeline       | ❌ Unavailable         | ✅ Active                    |
| `document.visibilityState` | ❌ Returns`"hidden"` | ✅ Returns`"visible"`      |
| `requestAnimationFrame`    | ❌ Throttled / frozen  | ✅ Normal 60fps              |
| Element layout dimensions    | ❌ May return 0        | ✅ Calculated correctly      |

When any of these conditions are abnormal, the SPA's boot sequence stalls indefinitely at the loading screen. Adding `--show` works because it opens a real browser window that satisfies all requirements.

**Solution (Already Applied):**
The TA engine (`src/core/engines/ta_engine.py`) always uses **headed (non-headless) mode**, but positions the browser window off-screen at `(-10000, -10000)` so it is invisible to the user. This gives the SPA a fully functional rendering environment without disrupting your workflow.

```python
# ta_engine.py — key configuration
headless=False,  # Always headed for reliable SPA rendering
args=[
    "--window-size=1920,1080",
    "--window-position=-10000,-10000",  # Off-screen but fully rendered
]
```

> **Note:** A Chrome process will appear in Task Manager during TA fetch operations. This is expected — the browser window is off-screen and will not appear on your display.
