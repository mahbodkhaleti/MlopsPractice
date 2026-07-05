import pandas as pd


def validate_summary(summary: pd.DataFrame) -> None:
    """
    Validate the neighbourhood summary dataframe.

    Checks:
    - Output is not empty
    - Required output columns exist
    - No PII columns exist
    - neighbourhood is not null
    - num_listings > 0
    - avg_price >= 0
    - availability_365_avg between 0 and 365

    Args:
        summary: Summary dataframe to validate

    Raises:
        ValueError: If any validation check fails
    """
    # Check not empty
    if summary.empty:
        raise ValueError("Output dataframe is empty")

    # Check required columns exist
    required_columns = {
        "neighbourhood", "num_listings", "avg_price", "median_price",
        "avg_minimum_nights", "availability_365_avg", "total_reviews",
        "reviews_per_listing", "tourism_segment", "priority_level"
    }
    missing_columns = required_columns - set(summary.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Check no PII columns exist
    pii_columns = {"host_name", "host_id", "reviewer_name", "reviewer_id", "listing_url", "host_url"}
    leaked_pii = pii_columns & set(summary.columns)
    if leaked_pii:
        raise ValueError(f"PII leaked in columns: {leaked_pii}")

    # Check neighbourhood is not null
    if summary["neighbourhood"].isnull().any():
        raise ValueError("neighbourhood column contains null values")

    # Check num_listings > 0
    if (summary["num_listings"] <= 0).any():
        raise ValueError("num_listings must be > 0")

    # Check avg_price >= 0
    if (summary["avg_price"] < 0).any():
        raise ValueError("avg_price must be >= 0")

    # Check availability_365_avg between 0 and 365
    if (summary["availability_365_avg"] < 0).any() or (summary["availability_365_avg"] > 365).any():
        raise ValueError("availability_365_avg must be between 0 and 365")
