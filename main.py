import sys
import os
import argparse
import json
import pandas as pd
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.config import settings
from src.utils.logger import logger
from src.utils.exporter import export_data
from src.utils.mailer import send_emails

console = Console()

def get_engine(engine_name, region="china"):
    if engine_name == "ta":
        from src.core.ta_engine import ThinkingDataEngine
        return ThinkingDataEngine()
    
    elif engine_name == "odps":
        from src.core.ali_engine import ODPSEngine
        config = settings.ALI_CREDENTIALS.get(region, {}).get("odps")
        if not config: raise ValueError(f"No ODPS config for region: {region}")
        return ODPSEngine(config)
        
    elif engine_name == "holo":
        from src.core.ali_engine import HoloEngine
        config = settings.ALI_CREDENTIALS.get(region, {}).get("holo")
        if not config: raise ValueError(f"No Holo config for region: {region}")
        return HoloEngine(config)
    
    else:
        raise ValueError(f"Unknown engine: {engine_name}")

def parse_email_recipients(sql_content: str):
    """
    Parse email recipients from SQL file first line comment.
    Format: -- MAILTO: email1@example.com, email2@example.com
    """
    lines = sql_content.strip().split('\n')
    if not lines:
        return []
    
    first_line = lines[0].strip()
    if first_line.startswith('--') and 'MAILTO:' in first_line.upper():
        mailto_part = first_line.split('MAILTO:', 1)[1] if 'MAILTO:' in first_line else first_line.split('mailto:', 1)[1]
        emails = [email.strip() for email in mailto_part.split(',')]
        return [e for e in emails if '@' in e and '.' in e]
    return []

def display_preview(results):
    """
    Display a data preview using rich table, similar to ali-data-client.
    """
    df = None
    if isinstance(results, pd.DataFrame):
        df = results
    elif isinstance(results, list) and results:
        # Case A: Intercepted JSON/List
        last_item = results[-1]
        if isinstance(last_item, dict):
            if last_item.get("type") == "file":
                # Case B: Direct file (TA download) - Read it for preview
                file_path = last_item.get("file_path")
                if file_path and os.path.exists(file_path):
                    try:
                        if file_path.endswith('.csv'):
                            df = pd.read_csv(file_path, nrows=10)
                        elif file_path.endswith('.xlsx'):
                            df = pd.read_excel(file_path, nrows=10)
                    except: pass
            else:
                headers = last_item.get("header", []) or last_item.get("headers", [])
                rows = last_item.get("rows", []) or last_item.get("results", [])
                if rows:
                    df = pd.DataFrame(rows, columns=headers)
    
    if df is None or df.empty:
        logger.warning("No data found for preview.")
        return False

    console.print("\n" + "─" * 50)
    console.print("[bold yellow]🔍 Data Preview (Top 10 Rows):[/bold yellow]\n")

    # Limit to 10 columns for display
    display_cols = list(df.columns[:10])
    table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
    
    for col in display_cols:
        table.add_column(str(col), overflow="fold")
        
    for _, row in df.head(10).iterrows():
        table.add_row(*[str(val) for val in row[:10]])
    
    console.print(table)
    console.print("─" * 50 + "\n")
    logger.info(f"[*] Total Stats: [bold]{len(df)}[/bold] rows and [bold]{len(df.columns)}[/bold] columns found.")
    return True

def run_task(task_config, interactive=False):
    """
    Run a single task configuration.
    """
    engine_name = task_config.get("engine", "ta")
    region = task_config.get("region", "china")
    sql_text = task_config.get("sql")
    sql_file = task_config.get("file")
    mailto = task_config.get("mailto")
    formats = task_config.get("formats", ["xlsx"])
    task_name = task_config.get("name", f"{engine_name}_export")
    show_browser = task_config.get("show", False)

    try:
        engine = get_engine(engine_name, region)
        
        # Determine SQL content
        sql_content = sql_text
        file_recipients = []
        if not sql_content and sql_file:
            if os.path.exists(sql_file):
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                file_recipients = parse_email_recipients(sql_content)
            else:
                logger.error(f"SQL file not found: {sql_file}")
                return

        if not sql_content:
            logger.error(f"No SQL content for task: {task_name}")
            return

        # Execute
        logger.info(f"🚀 Running task: {task_name} ({engine_name})...")
        if engine_name == "ta":
            results = engine.fetch(sql_content, headless=not show_browser)
        else:
            results = engine.fetch(sql_content)

        # Export
        final_file_paths = []
        if results is not None:
            # Handle Interactivity (Preview -> Confirm -> Rename -> Format)
            if interactive:
                # 1. Preview
                display_preview(results)
                
                # 2. Confirm Download
                confirm = console.input("\n[?] Download? (y/n, default y): ").lower().strip()
                if confirm == 'n':
                    logger.info("[*] Canceled download.")
                    return
                
                # 3. Rename
                custom_name = console.input(f"[?] File prefix (Default: '{task_name}'): ").strip()
                if custom_name:
                    task_name = custom_name
                
                # 4. Format Selection
                console.print("\n" + "-"*30)
                console.print("[?] Select Format:")
                console.print("   1. Excel (.xlsx)")
                console.print("   2. CSV (.csv)")
                console.print("   3. Text (.txt)")
                console.print("   4. All formats")
                choice = console.input(">> ").strip()
                
                if choice == '1': formats = ['xlsx']
                elif choice == '2': formats = ['csv']
                elif choice == '3': formats = ['txt']
                elif choice == '4': formats = ['xlsx', 'csv', 'txt']
                # if invalid or empty, keeps default 'formats' from config

            # Check if engine returned a direct file path (TA download mode)
            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict) and results[0].get("type") == "file":
                original_file = results[0].get("file_path")
                final_file_paths = [original_file]
                
                # If user requested formats (including csv for renaming), convert/re-export
                if len(formats) > 0:
                    try:
                        logger.info(f"Applying filename and formats to downloaded data...")
                        df_tmp = pd.read_csv(original_file)
                        # Export all requested formats with the new task_name/prefix
                        converted_paths = export_data(df_tmp, filename_prefix=task_name, formats=formats)
                        final_file_paths = converted_paths
                        # Optional: remove original ugly-named file to keep output clean
                        try: os.remove(original_file)
                        except: pass
                    except Exception as conv_err:
                        logger.warn(f"Failed to apply formatting: {conv_err}")
            else:
                final_file_paths = export_data(results, filename_prefix=task_name, formats=formats)
            
            if final_file_paths:
                # Email Notification
                recipient_str = mailto or ",".join(file_recipients)
                if recipient_str:
                    recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]
                    subject = f"Data Report: {task_name}"
                    body = (f"Hello,\n\nYour data report has been generated.\n\n"
                            f"Task: {task_name}\n"
                            f"Engine: {engine_name}\n"
                            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    send_emails(
                        smtp_server=settings.SMTP_SERVER,
                        smtp_port=settings.SMTP_PORT,
                        sender_email=settings.SENDER_EMAIL,
                        sender_password=settings.SENDER_PASSWORD,
                        recipient_emails=recipients,
                        subject=subject,
                        body=body,
                        attachment_paths=final_file_paths
                    )
        else:
            logger.warn(f"No results for task: {task_name}")

    except Exception as e:
        logger.error(f"Error executing task {task_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="FiveCross Unified Data Client")
    # Single task arguments
    parser.add_argument("--engine", type=str, choices=["ta", "odps", "holo"], help="Data engine to use")
    parser.add_argument("--region", type=str, choices=["china", "global"], default="china", help="Region for Ali engines")
    parser.add_argument("--sql", type=str, help="Direct SQL statement")
    parser.add_argument("--file", type=str, help="Path to SQL file")
    parser.add_argument("--mailto", type=str, help="Recipient emails (comma separated)")
    parser.add_argument("--formats", type=str, default="xlsx", help="Export formats (comma separated, e.g., xlsx,csv)")
    parser.add_argument("--show", action="store_true", help="Show browser (TA engine only)")
    parser.add_argument("--login", action="store_true", help="Perform login (TA engine only)")
    
    # Batch task argument
    parser.add_argument("--task", type=str, help="Path to JSON task configuration file")
    
    args = parser.parse_args()
    
    # 1. Handle Login
    if args.login:
        engine = get_engine(args.engine or "ta", args.region)
        if hasattr(engine, 'login'):
            engine.login(headless=False)
        return

    # 2. Handle Batch Tasks
    if args.task:
        if not os.path.exists(args.task):
            logger.error(f"Task file not found: {args.task}")
            return
        
        with open(args.task, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
        
        if isinstance(tasks, list):
            for task_config in tasks:
                run_task(task_config)
        else:
            run_task(tasks)
        return

    # 3. Handle Single CLI Task
    if args.engine:
        formats = [f.strip() for f in args.formats.split(",")]
        task_config = {
            "engine": args.engine,
            "region": args.region,
            "sql": args.sql,
            "file": args.file,
            "mailto": args.mailto,
            "formats": formats,
            "show": args.show
        }
        # Ad-hoc runs via CLI are interactive by default (unless it's a batch task)
        run_task(task_config, interactive=True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
