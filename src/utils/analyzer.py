import csv
import os
import time
from src.utils.logger import logger

class LogAnalyzer:
    """
    Core logic for analyzing large CSV logs to find specific IDs.
    Separated from CLI interface for reusability.
    """
    
    # Standard event name headers for different platforms
    EVENT_COLUMN_CANDIDATES = ['#event_name', '$part_event', 'event_name', 'a_typ']

    @staticmethod
    def analyze_csv(csv_path, target_ids):
        """
        Analyzes a CSV file and returns a structured report of ID occurrences.
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Analyzing file: {os.path.basename(csv_path)}")
        logger.info(f"Target IDs: {', '.join(target_ids)}")
        
        start_time = time.time()
        results = {tid: {} for tid in target_ids}
        row_count = 0
        
        try:
            # Use utf-8-sig to handle potential BOM
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                header = next(reader)
                
                # Identify event name columns
                event_indices = [
                    idx for idx, name in enumerate(header) 
                    if name.lower() in [c.lower() for c in LogAnalyzer.EVENT_COLUMN_CANDIDATES]
                ]
                
                # Fallback to index 1 (common convention) if no matches
                if not event_indices:
                    event_indices = [1]
                
                detected_names = [header[i] for i in event_indices if i < len(header)]
                logger.info(f"Monitoring event columns: {detected_names}")
                
                for row in reader:
                    row_count += 1
                    if row_count % 500000 == 0:
                        logger.info(f"Processed {row_count:,} rows...")
                    
                    # Iterate through each column for substring matching
                    for col_idx, cell_value in enumerate(row):
                        if not cell_value:
                            continue
                            
                        for tid in target_ids:
                            if tid in cell_value:
                                # Determine event name
                                event_name = "Unknown"
                                for e_idx in event_indices:
                                    if e_idx < len(row) and row[e_idx].strip():
                                        event_name = row[e_idx]
                                        break
                                        
                                col_name = header[col_idx] if col_idx < len(header) else f"Column_{col_idx}"
                                
                                key = (event_name, col_name)
                                results[tid][key] = results[tid].get(key, 0) + 1
                                
        except Exception as e:
            logger.error(f"Error during CSV analysis: {e}")
            raise

        duration = time.time() - start_time
        return {
            "results": results,
            "metadata": {
                "file": os.path.basename(csv_path),
                "rows": row_count,
                "duration": duration
            }
        }
