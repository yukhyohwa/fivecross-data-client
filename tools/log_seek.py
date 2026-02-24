import os
import sys
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add project root to sys.path to allow imports from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.analyzer import LogAnalyzer
from src.utils.logger import logger

console = Console()

def find_latest_csv(base_dir):
    """Finds the most recently modified CSV in output or subdirs."""
    csv_files = []
    for root, _, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith('.csv'):
                path = os.path.join(root, f)
                csv_files.append((path, os.path.getmtime(path)))
    
    if not csv_files:
        return None
    
    return sorted(csv_files, key=lambda x: x[1], reverse=True)[0][0]

def main():
    parser = argparse.ArgumentParser(description="FiveCross Log Seeker - Locate IDs in massive CSV logs.")
    parser.add_argument("ids", nargs="*", help="IDs to search for (space separated)")
    parser.add_argument("--path", help="Path to specific CSV file. If omitted, finds latest in output/")
    
    args = parser.parse_args()
    
    # Configuration
    target_ids = args.ids if args.ids else ['78128243', '90000730'] # Maintain your defaults
    
    csv_path = args.path
    if not csv_path:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        csv_path = find_latest_csv(output_dir)
        if not csv_path:
            # Check local queries mapping or examples
            csv_path = find_latest_csv(os.getcwd())

    if not csv_path:
        console.print("[bold red]Error:[/bold red] No CSV files found in output/ or current directory.")
        sys.exit(1)

    with console.status(f"[bold green]Analyzing {os.path.basename(csv_path)}..."):
        try:
            report = LogAnalyzer.analyze_csv(csv_path, target_ids)
        except Exception as e:
            console.print(f"[bold red]Failed:[/bold red] {e}")
            sys.exit(1)

    # Print Pretty Report
    results = report["results"]
    meta = report["metadata"]

    console.print(Panel(
        f"[bold blue]File:[/bold blue] {meta['file']}\n"
        f"[bold blue]Rows:[/bold blue] {meta['rows']:,}\n"
        f"[bold blue]Time:[/bold blue] {meta['duration']:.2f} seconds",
        title="[bold white]Analysis Summary[/bold white]",
        expand=False
    ))

    for tid, locations in results.items():
        table = Table(title=f"Occurrences for ID: [bold yellow]{tid}[/bold yellow]", show_header=True, header_style="bold magenta")
        table.add_column("Event Name", style="dim")
        table.add_column("Column Name")
        table.add_column("Count", justify="right")

        if not locations:
            table.add_row("[red]NOT FOUND[/red]", "-", "0")
        else:
            for (event, col), count in sorted(locations.items(), key=lambda x: x[1], reverse=True):
                table.add_row(event, col, str(count))
        
        console.print(table)
        console.print("")

if __name__ == "__main__":
    main()
