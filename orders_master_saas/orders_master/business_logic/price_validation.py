import pandas as pd

from orders_master.constants import Columns


def flag_price_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifies rows with invalid prices and marks them.

    Rules: P.CUSTO <= 0 | PVP <= 0 | PVP < P.CUSTO
    Original DataFrame is not mutated.
    """
    df_out = df.copy()

    # Check if columns exist to prevent KeyError, though schema should guarantee it
    if Columns.P_CUSTO in df_out.columns and Columns.PVP in df_out.columns:
        anomaly_mask = (
            (df_out[Columns.P_CUSTO] <= 0)
            | (df_out[Columns.PVP] <= 0)
            | (df_out[Columns.PVP] < df_out[Columns.P_CUSTO])
        )
        df_out[Columns.PRICE_ANOMALY] = anomaly_mask
    else:
        # If columns missing, set to False safely
        df_out[Columns.PRICE_ANOMALY] = False

    return df_out
