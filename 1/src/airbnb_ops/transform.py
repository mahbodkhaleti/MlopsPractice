import pandas as pd
from .pii import handle_pii


def build_neighbourhood_summary(listings: pd.DataFrame, segments: pd.DataFrame) -> pd.DataFrame:
    """
    Build a neighbourhood-level summary from listings data.

    Steps:
    1. Handle PII in listings
    2. Group by neighbourhood and aggregate
    3. Join with segment metadata
    4. Fill missing segments with 'unknown'

    Args:
        listings: Raw listings dataframe
        segments: Neighbourhood segments dataframe

    Returns:
        Neighbourhood-level summary dataframe
    """
    # Validate input columns
    required_listings_cols = {
        "listing_id", "neighbourhood", "price", "minimum_nights",
        "availability_365", "number_of_reviews", "host_id", "host_name"
    }
    if not required_listings_cols.issubset(listings.columns):
        raise ValueError(f"Missing required columns in listings: {required_listings_cols - set(listings.columns)}")

    # Handle PII
    listings_clean = handle_pii(listings)

    # Group by neighbourhood and aggregate
    summary = listings_clean.groupby("neighbourhood").agg(
        num_listings=("listing_id", "count"),
        avg_price=("price", "mean"),
        median_price=("price", "median"),
        avg_minimum_nights=("minimum_nights", "mean"),
        availability_365_avg=("availability_365", "mean"),
        total_reviews=("number_of_reviews", "sum"),
    ).reset_index()

    # Calculate reviews per listing
    summary["reviews_per_listing"] = summary["total_reviews"] / summary["num_listings"]

    # Join with segment metadata
    summary = summary.merge(
        segments,
        on="neighbourhood",
        how="left"
    )

    # Fill missing segments with 'unknown'
    summary["tourism_segment"] = summary["tourism_segment"].fillna("unknown")
    summary["priority_level"] = summary["priority_level"].fillna("unknown")

    return summary
