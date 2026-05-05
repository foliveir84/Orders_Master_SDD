import pandas as pd
from orders_master.constants import Columns


def clean_designation_vectorized(s: pd.Series) -> pd.Series:
    """
    Limpa e normaliza uma série de designações de produtos de forma vectorizada.
    
    Aplica:
    1. Preenchimento de NAs com string vazia.
    2. Normalização NFD para decompor acentos.
    3. Codificação ASCII para ignorar acentos e descodificação UTF-8.
    4. Remoção de asteriscos.
    5. Remoção de espaços em branco extra.
    6. Formatação Title Case.

    Args:
        s (pd.Series): Série com as designações originais.

    Returns:
        pd.Series: Série com as designações limpas.
    """
    return (
        s.fillna("")
        .astype(str)
        .str.normalize("NFD")
        .str.encode("ascii", "ignore")
        .str.decode("utf-8")
        .str.replace("*", "", regex=False)
        .str.strip()
        .str.title()
    )


def remove_zombie_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove linhas "zombie" (STOCK == 0 AND T Uni == 0) ao nível individual (loja).
    
    Args:
        df (pd.DataFrame): DataFrame com colunas STOCK e T Uni.

    Returns:
        pd.DataFrame: DataFrame sem as linhas zombie individuais.
    """
    mask = (df[Columns.STOCK] != 0) | (df[Columns.T_UNI] != 0)
    return df[mask].copy()


def remove_zombie_aggregated(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove códigos "zombie" (STOCK total == 0 AND T Uni total == 0) ao nível do grupo.
    
    Identifica códigos que, após agregação, não têm stock nem vendas em nenhuma loja,
    e remove todas as linhas associadas a esses códigos.

    Args:
        df (pd.DataFrame): DataFrame (pode ser detalhado ou agrupado).

    Returns:
        pd.DataFrame: DataFrame sem os códigos zombie.
    """
    # Agrupar por código para identificar a situação global do produto
    # Usamos o DataFrame actual para calcular os totais por CÓDIGO
    df_totals = df.groupby(Columns.CODIGO, as_index=False)[[Columns.STOCK, Columns.T_UNI]].sum()
    
    # Identificar códigos onde STOCK e T_UNI são ambos zero
    mask_zombie = (df_totals[Columns.STOCK] == 0) & (df_totals[Columns.T_UNI] == 0)
    codigos_zombie = df_totals.loc[mask_zombie, Columns.CODIGO].unique()
    
    # Filtrar o DataFrame original removendo esses códigos
    return df[~df[Columns.CODIGO].isin(codigos_zombie)].copy()
