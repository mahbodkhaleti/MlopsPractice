from pathlib import Path
import pandas as pd


def read_csv_checked(path: Path) -> pd.DataFrame:
    """
    Read a CSV file and raise FileNotFoundError if the file is missing.

    Args:
        path: Path to the CSV file

    Returns:
        DataFrame containing the CSV data

    Raises:
        FileNotFoundError: If the file does not exist
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)
