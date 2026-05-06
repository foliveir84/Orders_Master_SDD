"""
Serviço de recálculo dinâmico — TASK-23.

Implementa ``recalculate_proposal`` que permite actualizar as propostas
sem re-processar os ficheiros originais, garantindo performance < 500ms.
"""

import pandas as pd

from orders_master.aggregation.aggregator import aggregate
from orders_master.business_logic.averages import weighted_average
from orders_master.business_logic.proposals import (
    compute_base_proposal,
    compute_shortage_proposal,
)
from orders_master.constants import Columns


def recalculate_proposal(  # noqa: PLR0913
    df_detailed: pd.DataFrame,
    detailed_view: bool,
    master_products: pd.DataFrame,
    months: float,
    weights: tuple[float, ...],
    use_previous_month: bool = False,
    marcas: list[str] | None = None,
) -> pd.DataFrame:
    """
    Executa o pipeline de cálculo sobre os dados detalhados e agrupa conforme a vista.

    Args:
        df_detailed: DataFrame com os dados brutos por loja (pós-ingestão).
        detailed_view: Se True, gera vista com linhas por loja + Grupo.
        master_products: Tabela mestre para injecção de marcas/designações.
        months: Meses de previsão para a proposta.
        weights: Pesos para a média ponderada.
        use_previous_month: Se True, ignora o mês mais recente na média.
        marcas: Lista opcional de marcas para filtrar.

    Returns:
        DataFrame processado e agregado pronto para exibição.
    """
    if df_detailed.empty:
        return df_detailed.copy()

    df_work = df_detailed.copy()

    # 0. Filtro por Marcas (TASK-26)
    if marcas:
        valid_cnps = master_products[master_products[Columns.MARCA].isin(marcas)][Columns.CODIGO]
        df_work = df_work[df_work[Columns.CODIGO].isin(valid_cnps)]

    # 1. Limpeza de colunas de cálculo prévias para evitar duplicados
    df_work = df_work.drop(columns=[Columns.MEDIA, Columns.PROPOSTA], errors="ignore").copy()

    # 2. Média Ponderada
    # Aplicado sobre o detalhado para permitir agregação correcta posterior
    df_work[Columns.MEDIA] = weighted_average(df_work, weights, use_previous_month)

    # 2. Proposta Base
    df_work = compute_base_proposal(df_work, months)

    # 3. Proposta de Rutura (TimeDelta deve estar presente se houver integração)
    df_work = compute_shortage_proposal(df_work)

    # 4. Agregação Final (Passos 1-10 do motor de agregação)
    # Nota: aggregator.py foi actualizado para somar MEDIA e PROPOSTA
    return aggregate(df_work, detailed_view, master_products)
