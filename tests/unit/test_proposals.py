"""
Testes unitários para compute_base_proposal — TASK-20.
"""

import pandas as pd

from orders_master.business_logic.proposals import compute_base_proposal
from orders_master.constants import Columns


def make_df(media: float, stock: int) -> pd.DataFrame:
    """Cria um DataFrame mínimo com as colunas Media e STOCK."""
    return pd.DataFrame(
        {
            Columns.MEDIA: [media],
            Columns.STOCK: [stock],
        }
    )


def test_positive_proposal() -> None:
    """Media=10, Meses=2, Stock=5 → Proposta=15."""
    df = make_df(media=10.0, stock=5)
    result = compute_base_proposal(df, meses_previsao=2.0)
    assert result[Columns.PROPOSTA].iloc[0] == 15


def test_negative_proposal_preserved() -> None:
    """Media=10, Meses=1, Stock=15 → Proposta=-5 (negativo mantido)."""
    df = make_df(media=10.0, stock=15)
    result = compute_base_proposal(df, meses_previsao=1.0)
    assert result[Columns.PROPOSTA].iloc[0] == -5


def test_zero_media_zero_stock() -> None:
    """Media=0, Meses=3, Stock=0 → Proposta=0."""
    df = make_df(media=0.0, stock=0)
    result = compute_base_proposal(df, meses_previsao=3.0)
    assert result[Columns.PROPOSTA].iloc[0] == 0


def test_proposta_is_int() -> None:
    """A proposta deve ser do tipo int após arredondamento."""
    df = make_df(media=7.3, stock=3)
    result = compute_base_proposal(df, meses_previsao=1.5)
    assert pd.api.types.is_integer_dtype(result[Columns.PROPOSTA].dtype)


def test_rounding_behaviour() -> None:
    """Proposta é arredondada corretamente (.round(0))."""
    # Media=1.7, Meses=3, Stock=0 → 5.1 → round → 5
    df = make_df(media=1.7, stock=0)
    result = compute_base_proposal(df, meses_previsao=3.0)
    assert result[Columns.PROPOSTA].iloc[0] == 5


def test_original_df_not_mutated() -> None:
    """A função não deve mutar o DataFrame original."""
    df = make_df(media=10.0, stock=5)
    _ = compute_base_proposal(df, meses_previsao=2.0)
    assert Columns.PROPOSTA not in df.columns


def test_multiple_rows() -> None:
    """Cálculo vectorizado com múltiplas linhas."""
    df = pd.DataFrame(
        {
            Columns.MEDIA: [10.0, 5.0, 0.0],
            Columns.STOCK: [5, 10, 0],
        }
    )
    result = compute_base_proposal(df, meses_previsao=2.0)
    expected = [15, 0, 0]  # 10*2-5=15, 5*2-10=0, 0*2-0=0
    assert result[Columns.PROPOSTA].tolist() == expected


def test_fractional_meses() -> None:
    """Previsão com meses fraccionários é suportada."""
    # Media=10, Meses=1.5, Stock=5 → 15-5=10
    df = make_df(media=10.0, stock=5)
    result = compute_base_proposal(df, meses_previsao=1.5)
    assert result[Columns.PROPOSTA].iloc[0] == 10
