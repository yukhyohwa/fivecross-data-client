# FiveCross Unified Data Client

A unified framework for extracting data from multiple sources (ThinkingData, AliCloud ODPS, Hologres) and automatically pushing reports via email.

## 🚀 Features
- **Multi-Engine Support**: 
  - `ta`: ThinkingData (Playwright Browser Automation)
  - `odps`: AliCloud MaxCompute (API-based)
  - `holo`: AliCloud Hologres (Postgres-based)
- **Auto-Export**: Saves all results to professional Excel files.
- **Email Notification**: Supports multiple recipients with attachments.
- **Async Monitoring**: Intelligent detection of long-running queries for ThinkingData.

## 🛠 Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and fill in your credentials.

## 📖 Usage

### Running ThinkingData Queries
```bash
python main.py --engine ta --file queries/ta_adhoc.sql --mailto user@example.com
```

### Running AliCloud ODPS Queries (Global Region)
```bash
python main.py --engine odps --region global --sql "SELECT * FROM your_table LIMIT 10"
```

### Running Hologres Queries
```bash
python main.py --engine holo --file queries/your_holo_query.sql
```

## 📂 Project Structure
- `src/core/`: Engine implementations.
- `src/utils/`: Shared utilities (Mailer, Exporter, Logger).
- `queries/`: SQL query repository.
- `output/`: Generated Excel reports.
