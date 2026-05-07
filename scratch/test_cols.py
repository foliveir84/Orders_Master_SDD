import pandas as pd
from orders_master.constants import Columns
from orders_master.aggregation.aggregator import aggregate

def test_missing_cols():
    # Simulate df_raw
    df_raw = pd.DataFrame({
        Columns.CODIGO: [1001, 1001],
        Columns.DESIGNACAO: ["A", "A"],
        Columns.LOCALIZACAO: ["L1", "L2"],
        "PVP": [10.0, 10.0],
        "P.CUSTO": [5.0, 5.0],
        Columns.STOCK: [2, 3],
        "Jan": [5, 6],
        Columns.T_UNI: [10, 10],
        Columns.DIR: ["X", "X"],
        Columns.DPR: ["Y", "Y"],
        Columns.DATA_OBS: ["Z", "Z"],
        Columns.TIME_DELTA: [1, 1],
        Columns.MEDIA: [5.0, 5.0],
        Columns.PROPOSTA: [3, 2]
    })
    master = pd.DataFrame({
        Columns.CODIGO: [1001],
        Columns.DESIGNACAO: ["A Master"],
        Columns.MARCA: ["M1"]
    })
    
    # Run aggregate Detailed
    df_agg_det = aggregate(df_raw, detailed=True, master_products=master)
    print("Detailed cols:", df_agg_det.columns.tolist())

    # Run aggregate Grouped
    df_agg_grp = aggregate(df_raw, detailed=False, master_products=master)
    print("Grouped cols:", df_agg_grp.columns.tolist())

if __name__ == "__main__":
    test_missing_cols()
