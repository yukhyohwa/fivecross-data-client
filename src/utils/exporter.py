import pandas as pd
import os
from datetime import datetime
from src.utils.logger import logger

def export_data(results, filename_prefix="data_export", formats=["xlsx"]):
    """
    Export results to multiple formats (xlsx, csv, json).
    Returns a list of generated file paths.
    """
    if results is None:
        return []

    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Prepare DataFrame
    df = None
    if isinstance(results, pd.DataFrame):
        df = results
    elif isinstance(results, list):
        # Check if it's the TA format (intercepted JSON)
        last_item = results[-1]
        if isinstance(last_item, dict):
            headers = last_item.get("header", []) or last_item.get("headers", [])
            rows = last_item.get("rows", []) or last_item.get("results", [])
            if rows:
                df = pd.DataFrame(rows, columns=headers)
    
    if df is None:
        logger.warn("No data available to export.")
        return []

    # 2. Export to each requested format
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_paths = []

    for fmt in formats:
        fmt = fmt.lower().strip()
        filepath = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.{fmt}")
        
        try:
            if fmt == "xlsx":
                df.to_excel(filepath, index=False)
            elif fmt == "csv":
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            elif fmt == "json":
                df.to_json(filepath, orient='records', force_ascii=False, indent=4)
            elif fmt in ["txt", "tsv"]:
                df.to_csv(filepath, sep='\t', index=False, encoding='utf-8-sig')
            else:
                logger.error(f"Unsupported format: {fmt}")
                continue
                
            logger.info(f"✓ Data successfully exported to: {filepath}")
            file_paths.append(filepath)
        except Exception as e:
            logger.error(f"✗ Export to {fmt} failed: {e}")

    return file_paths
