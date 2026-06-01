from pathlib import Path
from datetime import datetime
import typer
import pandas as pd
from rich.console import Console

from .config import PipelineConfig
from .extract import read_csv_checked
from .transform import build_neighbourhood_summary
from .validate import validate_summary

console = Console()


def run(
    listings_path: str = typer.Option(
        "data/raw/listings_sample.csv",
        help="Path to listings CSV file"
    ),
    segments_path: str = typer.Option(
        "data/raw/neighbourhood_segments.csv",
        help="Path to neighbourhood segments CSV file"
    ),
    output_path: str = typer.Option(
        "data/processed/airbnb_neighbourhood_summary.csv",
        help="Path for output CSV file"
    ),
    report_path: str = typer.Option(
        "reports/hw01_a_run_report.md",
        help="Path for output report file"
    ),
):
    """Run the Airbnb Ops pipeline: extract, transform, validate, and save."""

    config = PipelineConfig(
        listings_path=Path(listings_path),
        segments_path=Path(segments_path),
        output_path=Path(output_path),
        report_path=Path(report_path),
    )

    try:
        console.print("[bold blue]Starting Airbnb Ops pipeline...[/bold blue]")

        # Extract
        console.print("[cyan]Extracting data...[/cyan]")
        listings = read_csv_checked(config.listings_path)
        segments = read_csv_checked(config.segments_path)
        console.print(f"  ✓ Loaded {len(listings)} listings")
        console.print(f"  ✓ Loaded {len(segments)} segments")

        # Transform
        console.print("[cyan]Transforming data...[/cyan]")
        summary = build_neighbourhood_summary(listings, segments)
        console.print(f"  ✓ Created {len(summary)} neighbourhood summaries")

        # Validate
        console.print("[cyan]Validating output...[/cyan]")
        validate_summary(summary)
        console.print("  ✓ All validations passed")

        # Save output
        console.print("[cyan]Saving outputs...[/cyan]")
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(config.output_path, index=False)
        console.print(f"  ✓ Saved to {config.output_path}")

        # Generate report
        console.print("[cyan]Generating report...[/cyan]")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_content = f"""# HW01-A Run Report

**Timestamp:** {timestamp}

## Summary

- **Input listings:** {len(listings)}
- **Input segments:** {len(segments)}
- **Output neighbourhoods:** {len(summary)}

## Data Quality

- **Listings with reviews:** {(listings['number_of_reviews'] > 0).sum()}
- **Neighbourhoods processed:** {len(summary)}

## Output

- **File:** {config.output_path}
- **Rows:** {len(summary)}
- **Columns:** {len(summary.columns)}

## Validation Status

✓ All validation checks passed

"""
        config.report_path.parent.mkdir(parents=True, exist_ok=True)
        config.report_path.write_text(report_content)
        console.print(f"  ✓ Saved to {config.report_path}")

        console.print("[bold green]✓ Pipeline completed successfully![/bold green]")

    except Exception as e:
        console.print(f"[bold red]✗ Pipeline failed: {str(e)}[/bold red]")
        raise typer.Exit(code=1)


app = typer.Typer()
app.command()(run)

if __name__ == "__main__":
    app()
