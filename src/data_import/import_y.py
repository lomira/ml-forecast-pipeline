import pandas as pd


def import_y(filepath):
    """
    Imports CSV data with two columns:
    - First column: date in D/M/Y format with / separator only
    - Second column: numeric values

    Args:
        filepath (str): Path to the CSV file

    Returns:
        pandas.DataFrame: DataFrame with 'date' and 'y' columns
        Returns None on errors
    """
    try:
        # Read CSV without parsing dates
        df = pd.read_csv(filepath, sep=";")

        if df.shape[1] != 2:
            raise ValueError(f"Expected 2 columns, found {df.shape[1]}")

        df.columns = ["date", "y"]

        # Strict date validation with D/M/Y format
        try:
            df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="raise")
        except ValueError:
            raise ValueError("Date format must be D/M/Y with / separator")

        # Validate numeric data
        df["y"] = pd.to_numeric(df["y"], errors="coerce")

        if df["y"].isna().any():
            raise ValueError("All values in second column must be numeric")

        return df
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return None
    except Exception as e:
        if isinstance(e, ValueError) or isinstance(e, Exception):
            raise
        print(f"An unexpected error occurred: {e}")
        return None
