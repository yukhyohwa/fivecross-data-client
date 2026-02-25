import sys
import os
import argparse
import json
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table

# Local imports
from src.config import settings
from src.utils.logger import logger
from src.utils.exporter import export_data
from src.utils.mailer import send_emails

console = Console()

def get_engine(engine_name, region="global"):
    if engine_name == "ta":
        from src.core.engines.ta_engine import ThinkingDataEngine
        config = settings.TA_CREDENTIALS.get(region)
        return ThinkingDataEngine(config)
    elif engine_name == "odps":
        from src.core.engines.ali_engine import ODPSEngine
        return ODPSEngine(settings.ALI_CREDENTIALS.get(region, {}).get("odps"))
    elif engine_name == "holo":
        from src.core.engines.ali_engine import HoloEngine
        return HoloEngine(settings.ALI_CREDENTIALS.get(region, {}).get("holo"))
    return None

def parse_email_recipients(sql_content: str):
    """Parse email recipients from SQL file first line comment."""
    lines = sql_content.strip().split('\n')
    if not lines: return []
    first_line = lines[0].strip()
    if first_line.startswith('--') and 'MAILTO:' in first_line.upper():
        mailto_part = first_line.upper().split('MAILTO:', 1)[1]
        emails = [email.strip() for email in mailto_part.split(',')]
        return [e for e in emails if '@' in e]
    return []

def display_preview(results, title="Data Preview"):
    df = None
    if isinstance(results, pd.DataFrame):
        df = results
    elif isinstance(results, list) and results:
        last_item = results[-1]
        if isinstance(last_item, dict):
            if last_item.get("type") == "file":
                file_path = last_item.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        if file_path.endswith('.csv'): df = pd.read_csv(file_path, nrows=10)
                        elif file_path.endswith('.xlsx'): df = pd.read_excel(file_path, nrows=10)
                    except: pass
            else:
                headers = last_item.get("header", []) or last_item.get("headers", [])
                rows = last_item.get("rows", []) or last_item.get("results", [])
                if rows: df = pd.DataFrame(rows, columns=headers)
    
    if df is None or df.empty:
        logger.warning("No data found for preview.")
        return False

    console.print("\n" + "─" * 50)
    console.print(f"[bold yellow]🔍 {title} (Top 10 Rows):[/bold yellow]\n")

    display_cols = list(df.columns[:10])
    table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
    for col in display_cols: table.add_column(str(col), overflow="fold")
    for _, row in df.head(10).iterrows(): table.add_row(*[str(val) for val in row[:10]])
    
    console.print(table)
    console.print("─" * 50 + "\n")
    logger.info(f"[*] Stats: [bold]{len(df)}[/bold] rows and [bold]{len(df.columns)}[/bold] columns.")
    return True

def run_fetch_task(task_config, interactive=False):
    engine_name = task_config.get("engine", "ta")
    region = task_config.get("region", "global")
    sql_text = task_config.get("sql")
    sql_file = task_config.get("file")
    formats = task_config.get("formats", ["xlsx"])
    task_name = task_config.get("name", f"{engine_name}_export")
    mailto = task_config.get("mailto")
    show_browser = task_config.get("show", False)

    try:
        engine = get_engine(engine_name, region)
        sql_content = sql_text
        file_recipients = []
        if not sql_content and sql_file:
            p = os.path.join(settings.TASKS_DIR, sql_file)
            if not os.path.exists(p):
                for root, _, files in os.walk(settings.TASKS_DIR):
                    if sql_file in files:
                        p = os.path.join(root, sql_file)
                        break
            
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f: 
                    sql_content = f.read()
                file_recipients = parse_email_recipients(sql_content)
        
        if not sql_content:
            logger.error(f"SQL content not found.")
            return

        logger.info(f"🚀 Fetching: {task_name}...")
        if engine_name == "ta":
            results = engine.fetch(sql_content, headless=not show_browser)
        else:
            results = engine.fetch(sql_content)

        if results is not None:
            final_file_paths = []
            if interactive:
                display_preview(results)
                if console.input("\n[?] Download? (y/n, default y): ").lower().strip() == 'n': return
                
                custom_name = console.input(f"[?] File prefix (Default: '{task_name}'): ").strip()
                if custom_name: task_name = custom_name

                console.print("\n[?] Select Format:\n  1. Excel (.xlsx)\n  2. CSV (.csv)\n  3. Text (.txt)\n  4. All formats")
                choice = console.input(">> ").strip()
                if choice == '1': formats = ['xlsx']
                elif choice == '2': formats = ['csv']
                elif choice == '3': formats = ['txt']
                elif choice == '4': formats = ['xlsx', 'csv', 'txt']

            # Handle TA Direct Download
            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict) and results[0].get("type") == "file":
                original_file = results[0].get("file_path")
                try:
                    df_tmp = pd.read_csv(original_file)
                    final_file_paths = export_data(df_tmp, filename_prefix=task_name, formats=formats)
                    os.remove(original_file)
                except:
                    final_file_paths = [original_file]
            else:
                final_file_paths = export_data(results, filename_prefix=task_name, formats=formats)

            # Email logic
            recipient_str = mailto or ",".join(file_recipients)
            if recipient_str and final_file_paths:
                recipients = [r.strip() for r in recipient_str.split(",") if "@" in r]
                send_emails(recipients, f"Data Report: {task_name}", f"Task: {task_name} finished at {datetime.now()}", final_file_paths)
                
        return results
    except Exception as e:
        logger.error(f"Fetch error: {e}")

def run_predict_task(args):
    # (Remains similar to previous ltv logic)
    model_type = args.model
    file = args.file
    ecpnu = args.ecpnu
    net_rate = args.net_rate
    
    search_paths = [file, os.path.join(settings.INPUT_DIR, file), os.path.join(settings.PREDICT_INPUT_DIR, file), os.path.join(settings.EXPORT_DIR, file)]
    input_path = next((p for p in search_paths if os.path.exists(p)), None)
            
    if not input_path:
        logger.error(f"Input file not found: {file}")
        return

    try:
        from src.core.services.analytics.validator import DataValidator
        logger.info(f"🔮 Predicting {model_type.upper()}...")
        df_input = pd.read_csv(input_path) if input_path.endswith('.csv') else pd.read_excel(input_path)
        
        if model_type == "ltv":
            from src.core.services.analytics.ltv_service import LTVService
            df_clean = DataValidator.clean_ltv_data(df_input)
            service = LTVService(df_clean)
            result_df = service.predict(ecpnu=ecpnu, net_rate=net_rate)
            benchmarks = service.get_summary_benchmarks()
            display_preview(benchmarks, title="LTV Benchmarks")
            export_name = f"LTV_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_data(result_df, filename_prefix=export_name, formats=["xlsx"], output_dir=settings.OUTPUT_DIR)
        
        elif model_type == "mau":
            from src.core.services.analytics.mau_service import MAUService
            df_clean = DataValidator.clean_mau_data(df_input)
            service = MAUService(df_clean)
            result_df = service.predict(months_to_predict=args.months, growth_factor=args.growth)
            display_preview(result_df.tail(15), title="MAU Forecast")
            export_name = f"MAU_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_data(result_df, filename_prefix=export_name, formats=["xlsx"], output_dir=settings.OUTPUT_DIR)

    except Exception as e:
        logger.error(f"Prediction error: {e}")

def main():
    parser = argparse.ArgumentParser(description="FiveCross Unified Data Client")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    fetch_parser = subparsers.add_parser("fetch", help="Fetch data from engines")
    fetch_parser.add_argument("--engine", choices=["ta", "odps", "holo"])
    fetch_parser.add_argument("--region", default="global")
    fetch_parser.add_argument("--file", help="SQL file name")
    fetch_parser.add_argument("--task", help="JSON task file")
    fetch_parser.add_argument("--interactive", action="store_true", default=False)
    fetch_parser.add_argument("--show", action="store_true", default=False, help="Show browser (TA only)")
    fetch_parser.add_argument("--mailto", help="Comma separated emails")

    predict_parser = subparsers.add_parser("predict", help="Run analytics models")
    predict_parser.add_argument("model", choices=["ltv", "mau"])
    predict_parser.add_argument("--file", required=True)
    predict_parser.add_argument("--ecpnu", type=float, default=50.0)
    predict_parser.add_argument("--net_rate", type=float, default=0.35)
    predict_parser.add_argument("--months", type=int, default=12, help="For MAU: Months to forecast")
    predict_parser.add_argument("--growth", type=float, default=1.0, help="For MAU: Growth factor for NUU")

    parser.add_argument("--login", action="store_true")

    args = parser.parse_args()

    if args.login:
        get_engine("ta", args.region or "global").login(headless=False)
        return

    if args.command == "fetch":
        if args.task:
            task_path = os.path.join(settings.CONFIGS_DIR, args.task)
            if not os.path.exists(task_path):
                for root, _, files in os.walk(settings.CONFIGS_DIR):
                    if args.task in files:
                        task_path = os.path.join(root, args.task)
                        break
            if os.path.exists(task_path):
                with open(task_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                    for t in (tasks if isinstance(tasks, list) else [tasks]): run_fetch_task(t)
        else:
            # Single CLI runs (ad-hoc) are interactive by default
            run_fetch_task(vars(args), interactive=True)
            
    elif args.command == "predict":
        run_predict_task(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
