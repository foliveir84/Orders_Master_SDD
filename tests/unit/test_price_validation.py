import pandas as pd

from orders_master.business_logic.price_validation import flag_price_anomalies
from orders_master.constants import Columns


def test_price_anomalies():
    # Criação de um DataFrame de teste com os cenários do critério de aceitação
    data = {Columns.P_CUSTO: [0, -5, 5, 5, 5, 5], Columns.PVP: [10, 10, 0, -1, 3, 10]}

    # 0: P.CUSTO = 0 -> True
    # 1: P.CUSTO = -5 -> True
    # 2: PVP = 0 -> True
    # 3: PVP = -1 -> True
    # 4: PVP = 3, P.CUSTO = 5 (margem negativa) -> True
    # 5: PVP = 10, P.CUSTO = 5 (válido) -> False

    df = pd.DataFrame(data)

    # Executa a função
    df_result = flag_price_anomalies(df)

    # Verifica que o dataframe original não foi mutado
    assert Columns.PRICE_ANOMALY not in df.columns

    # Verifica a coluna resultante
    anomalies = df_result[Columns.PRICE_ANOMALY].tolist()

    assert anomalies[0] is True
    assert anomalies[1] is True
    assert anomalies[2] is True
    assert anomalies[3] is True
    assert anomalies[4] is True
    assert anomalies[5] is False
