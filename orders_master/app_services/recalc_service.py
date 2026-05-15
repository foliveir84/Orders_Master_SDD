"""
Serviço de recálculo dinâmico — TASK-23.

Implementa ``recalculate_proposal`` que permite actualizar as propostas
sem re-processar os ficheiros originais, garantindo performance < 500ms.
"""

from typing import Any

import pandas as pd

from orders_master.aggregation.aggregator import aggregate
from orders_master.business_logic.averages import weighted_average
from orders_master.business_logic.proposals import (
    compute_base_proposal,
    compute_shortage_proposal,
)
from orders_master.constants import Columns, GroupLabels


def recalculate_proposal(  # noqa: PLR0913
    df_detailed: pd.DataFrame,
    detailed_view: bool,
    df_master_products: pd.DataFrame,
    months: float,
    weights: tuple[float, ...],
    use_previous_month: bool = False,
    marcas: list[str] | None = None,
    scope_context: Any | None = None,
) -> pd.DataFrame:
    """
    Executa o pipeline de cálculo sobre os dados detalhados e agrupa conforme a vista.

    Args:
        df_detailed: DataFrame com os dados brutos por loja (pós-ingestão).
        detailed_view: Se True, gera vista com linhas por loja + Grupo.
        df_master_products: Tabela mestre para injecção de marcas/designações.
        months: Meses de previsão para a proposta.
        weights: Pesos para a média ponderada.
        use_previous_month: Se True, ignora o mês mais recente na média.
        marcas: Lista opcional de marcas para filtrar.
        scope_context: Objecto ScopeContext para actualizar métricas na UI.

    Returns:
        DataFrame processado e agregado pronto para exibição.
    """
    if df_detailed.empty:
        return df_detailed.copy()

    df_work = df_detailed.copy()

    # 0. Filtro por Marcas (TASK-26)
    if marcas:
        valid_cnps = df_master_products[df_master_products[Columns.MARCA].isin(marcas)][Columns.CODIGO]
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
    df_agg = aggregate(df_work, detailed_view, df_master_products)

    # 4.1 Garantir que as linhas Grupo sobrevivem ao filtro de marcas
    if marcas and detailed_view and Columns.LOCALIZACAO in df_agg.columns and Columns.MARCA in df_agg.columns:
        df_agg = df_agg[
            (df_agg[Columns.LOCALIZACAO] == GroupLabels.GROUP_ROW)
            | (df_agg[Columns.MARCA].isin(marcas))
        ].copy()

    # 5. Actualizar ScopeContext (TASK-33)
    if scope_context is not None:
        from orders_master.constants import GroupLabels

        # Contagem de produtos (excluir linhas 'Grupo' se vista detalhada)
        if detailed_view and Columns.LOCALIZACAO in df_agg.columns:
            scope_context.n_produtos = len(
                df_agg[df_agg[Columns.LOCALIZACAO] != GroupLabels.GROUP_ROW]
            )
        else:
            scope_context.n_produtos = len(df_agg)

        scope_context.n_farmacias = df_work[Columns.LOCALIZACAO].nunique()
        scope_context.meses = months
        scope_context.modo = "Detalhada" if detailed_view else "Agrupada"

        # Identificar janela de meses (PRD §5.4.2)
        if Columns.T_UNI in df_work.columns:
            idx_loc = df_work.columns.get_loc(Columns.T_UNI)
            if isinstance(idx_loc, int):
                offset = 2 if use_previous_month else 1
                first_idx = idx_loc - offset - 3
                last_idx = idx_loc - offset

                if first_idx >= 0 and last_idx < len(df_work.columns):
                    scope_context.primeiro_mes = str(df_work.columns[first_idx])
                    scope_context.ultimo_mes = str(df_work.columns[last_idx])

    return df_agg
