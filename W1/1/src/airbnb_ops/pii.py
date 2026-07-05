import hashlib
import pandas as pd


DIRECT_PII_COLUMNS = ["host_name", "host_id"]


def pseudonymize_value(value, salt="qbc12") -> str:
    """
    Convert a value to a pseudonymized hash using SHA256.

    Args:
        value: The value to hash
        salt: Salt for hashing (default: 'qbc12')

    Returns:
        Hex string of the SHA256 hash
    """
    value_str = str(value)
    hash_input = f"{value_str}{salt}".encode()
    return hashlib.sha256(hash_input).hexdigest()


def handle_pii(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle PII in the dataframe by:
    - Dropping host_name column
    - Converting host_id to pseudonymized host_key
    - Removing the original host_id column

    Args:
        df: Input dataframe with potential PII

    Returns:
        Dataframe with PII removed and host_id converted to host_key
    """
    df = df.copy()

    # Create host_key from host_id if it exists
    if "host_id" in df.columns:
        df["host_key"] = df["host_id"].apply(lambda x: pseudonymize_value(x))

    # Drop PII columns
    if "host_name" in df.columns:
        df = df.drop(columns=["host_name"])
    if "host_id" in df.columns:
        df = df.drop(columns=["host_id"])

    return df
