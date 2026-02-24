# FiveCross Unified Data Client

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Docker-Supported-blue?logo=docker" alt="Docker">
  <img src="https://img.shields.io/badge/Engines-TA%20%7C%20ODPS%20%7C%20Holo-orange.svg" alt="Engines">
  <img src="https://img.shields.io/badge/Security-Protected-green.svg" alt="Security">
</p>

A powerful and unified data extraction framework for ThinkingData (TA), AliCloud ODPS (MaxCompute), and Hologres. This project is the evolved version of `ali-data-client` and `thinking-data-client`, integrated into a professional "Data Worker" service.

## 🌟 Key Features

- **Multi-Engine Support**: ThinkingData (Global & China), AliCloud MaxCompute, and Hologres.
- **Unified Logic**: One client for all company data platforms.
- **Private SQL Library**: Securely integrated via Git Submodules (keeps business logic separate from tool code).
- **One-Click Setup**: Automated environment initialization for local and containerized environments.
- **Intelligent Export**: Automatic format conversion (Excel, CSV, JSON) and email delivery.

## 🛠 Setup & Initialization

### 1. Local Environment (Windows)
We provide a one-click setup script to handle Python VENV, dependencies, and Playwright drivers.
1.  **Clone the project**:
    ```bash
    git clone --recursive https://github.com/yukhyohwa/fivecross-data-client.git
    cd fivecross-data-client
    ```
2.  **Run Setup**:
    Double-click `setup.bat` or run:
    ```powershell
    .\setup.bat
    ```
3.  **Configure Credentials**:
    Edit the newly created `.env` file with your platform credentials.

### 2. Docker (Containerized)
Ideal for scheduled tasks on Linux servers.
```bash
# Build
docker build -t fivecross-client .

# Run
docker run --env-file .env fivecross-client --engine ta --sql "SELECT ..."
```

## 📂 Project Structure

- `src/core/`: Engine logic (TA, ODPS, Holo).
- `queries/sql-lib/`: **[Private Submodule]** The shared internal SQL library.
- `ta_session/`: Local browser session storage (ignored by git).
- `output/`: Generated reports and debug snapshots.
- `setup.bat`: One-click initialization script.
- `Dockerfile`: Container definition.

## 📖 Usage

### Ad-hoc Queries
```bash
# Using the integrated SQL library
python main.py --engine ta --file queries/sql-lib/games/slam_dunk/maxcompute/active_users.sql

# Direct SQL strings
python main.py --engine odps --sql "SELECT count(*) FROM ods_log_login WHERE day='20240101'"
```

### Scheduled Multi-Tasks
Edit `tasks/scheduled_multi_tasks.json` and run:
```bash
python main.py --task tasks/scheduled_multi_tasks.json
```

## 🔒 Security & Privacy
- **.env**: Never committed to Git. Local credentials stay local.
- **submodules**: The `sql-lib` is a private repository. External users cannot access your SQL logic even if they have this tool's code.

## 📝 SQL Directives
Add recipients directly in your SQL files:
```sql
-- MAILTO: analytics@example.com, boss@example.com
SELECT * FROM ...
```

