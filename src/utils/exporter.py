import pandas as pd
import os
from datetime import datetime
from src.utils.logger import logger

def save_to_excel(results, filename_prefix="data_export"):
    """
    Save list of dicts or DataFrame to Excel.
    """
    if not results:
        return None

    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.xlsx")

    try:
        if isinstance(results, pd.DataFrame):
            results.to_excel(filepath, index=False)
        elif isinstance(results, list):
            # Check if it's the TA format (intercepted JSON)
            result = results[-1]
            headers = result.get("header", []) or result.get("headers", [])
            rows = result.get("rows", []) or result.get("results", [])
            
            if rows:
                df = pd.DataFrame(rows, columns=headers)
                df.to_excel(filepath, index=False)
            else:
                return None
        else:
            return None
            
        logger.info(f"✓ Data successfully exported to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"✗ Export failed: {e}")
        return None
