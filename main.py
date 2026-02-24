import sys
import os
import argparse
from datetime import datetime
from src.config import settings
from src.utils.logger import logger
from src.utils.exporter import save_to_excel
from src.utils.mailer import send_email_with_attachment

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

def main():
    parser = argparse.ArgumentParser(description="FiveCross Unified Data Client")
    parser.add_argument("--engine", type=str, choices=["ta", "odps", "holo"], default="ta", help="Data engine to use")
    parser.add_argument("--region", type=str, choices=["china", "global"], default="china", help="Region for Ali engines")
    parser.add_argument("--sql", type=str, help="Direct SQL statement")
    parser.add_argument("--file", type=str, help="Path to SQL file")
    parser.add_argument("--mailto", type=str, help="Recipient emails (comma separated)")
    parser.add_argument("--show", action="store_true", help="Show browser (TA engine only)")
    parser.add_argument("--login", action="store_true", help="Perform login (TA engine only)")
    
    args = parser.parse_args()
    
    try:
        engine = get_engine(args.engine, args.region)
        
        if args.login and args.engine == "ta":
            engine.login(headless=False)
            return

        # Prepare SQL
        sql_content = None
        file_recipients = []
        
        if args.sql:
            sql_content = args.sql
        else:
            # Determine default file if --file is not provided
            target_file = args.file
            if not target_file:
                if args.engine == "ta":
                    target_file = os.path.join("queries", "adhoc_ta.sql")
                else:
                    target_file = os.path.join("queries", "adhoc_ali.sql")
                logger.info(f"No file specified, using default for {args.engine}: {target_file}")

            if os.path.exists(target_file):
                with open(target_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                file_recipients = parse_email_recipients(sql_content)
            else:
                logger.error(f"File not found: {target_file}")
                return
        
        if not sql_content:
            logger.error("No SQL input provided. Use --sql or --file.")
            return

        # Execute
        logger.info(f"Starting execution using engine: {args.engine}...")
        if args.engine == "ta":
            results = engine.fetch(sql_content, headless=not args.show)
        else:
            results = engine.fetch(sql_content)

        # Export
        final_file_path = None
        if results is not None:
            if isinstance(results, list) and len(results) > 0 and isinstance(results[0], dict) and results[0].get("type") == "file":
                final_file_path = results[0].get("file_path")
            else:
                final_file_path = save_to_excel(results, filename_prefix=f"{args.engine}_export")
            
            if final_file_path:
                logger.info(f"Data saved to: {final_file_path}")
                
                # Email Notification: Priority: CLI arg > SQL comment > .env
                recipient_str = args.mailto or ",".join(file_recipients) or os.getenv("MAILTO")
                if recipient_str:
                    recipients = [r.strip() for r in recipient_str.split(",") if r.strip()]
                    subject = f"Data Report [{args.engine.upper()}]: {os.path.basename(final_file_path)}"
                    body = f"Hello,\n\nYour data report has been generated successfully.\n\nEngine: {args.engine}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    send_email_with_attachment(
                        smtp_server=settings.SMTP_SERVER,
                        smtp_port=settings.SMTP_PORT,
                        sender_email=settings.SENDER_EMAIL,
                        sender_password=settings.SENDER_PASSWORD,
                        recipient_emails=recipients,
                        subject=subject,
                        body=body,
                        attachment_path=final_file_path
                    )
        else:
            logger.warn("No results captured.")

    except Exception as e:
        logger.error(f"Critical error during execution: {e}")

if __name__ == "__main__":
    main()
