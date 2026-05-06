"""
Testes unitários do Web Styler — TASK-41.

Cobre os critérios de aceitação definidos em tasks.md:
  - Linha Grupo → fundo preto, letra branca, bold em toda a linha.
  - Linha com DATA_OBS → fundo roxo de CÓDIGO até T Uni.
  - Célula Proposta com DIR preenchido → fundo vermelho.
  - Célula DTVAL com validade ≤ 4 meses → fundo laranja.
  - Célula PVP_Médio com price_anomaly → prefixo ⚠️.
  - Precedência: linha Grupo não recebe regras 2-5.
"""

from datetime import datetime

import pandas as pd

from orders_master.constants import Columns, GroupLabels, Highlight
from orders_master.formatting.web_styler import build_styler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NEXT_MONTH = datetime.now()
EXPIRY_SOON = f"{NEXT_MONTH.month:02d}/{NEXT_MONTH.year}"  # ≤ 4 months


def make_row(**kwargs: object) -> dict:
    """Linha base com todos os campos para o teste."""
    defaults: dict = {
        Columns.CODIGO: 2001,
        Columns.DESIGNACAO: "Produto Teste",
        Columns.LOCALIZACAO: "FAR_A",
        Columns.STOCK: 10,
        Columns.PVP_MEDIO: 5.0,
        Columns.P_CUSTO_MEDIO: 3.0,
        Columns.T_UNI: 20,
        Columns.PROPOSTA: 5,
        Columns.DTVAL: "12/2030",
        Columns.DATA_OBS: None,
        Columns.DIR: None,
        Columns.PRICE_ANOMALY: False,
    }
    return {**defaults, **kwargs}


def get_style_for_col(styles_df: pd.DataFrame, row_idx: int, col: str) -> str:
    """Extrai o CSS de uma célula específica do resultado do Styler."""
    if col not in styles_df.columns:
        return ""
    val = styles_df.loc[row_idx, col]
    return str(val) if val else ""


# ---------------------------------------------------------------------------
# Tests — Regra 1: Linha Grupo
# ---------------------------------------------------------------------------


def test_grupo_row_gets_black_background() -> None:
    """Linha Grupo deve ter fundo preto e letra branca em TODA a linha."""
    df = pd.DataFrame(
        [
            make_row(
                **{
                    Columns.LOCALIZACAO: GroupLabels.GROUP_ROW,
                    Columns.DATA_OBS: None,
                    Columns.DIR: None,
                    Columns.PRICE_ANOMALY: False,
                }
            )
        ]
    )
    styler = build_styler(df)
    rendered = styler.to_html()
    # Should contain the Grupo background colour
    assert Highlight.GRUPO_BG.lower().replace("#", "") in rendered.lower()


def test_grupo_row_all_columns_styled() -> None:
    """A linha Grupo deve receber estilo de fundo preto em alguma coluna (toda a linha)."""
    df = pd.DataFrame([make_row(**{Columns.LOCALIZACAO: GroupLabels.GROUP_ROW})])
    styler = build_styler(df)
    rendered = styler.to_html()
    # Black background should appear at least once in the rendered output
    assert "000000" in rendered.lower()


# ---------------------------------------------------------------------------
# Tests — Regra 2: Não Comprar
# ---------------------------------------------------------------------------


def test_nao_comprar_purple_background() -> None:
    """Linha com DATA_OBS preenchido → fundo roxo nas colunas CÓDIGO → T Uni."""
    df = pd.DataFrame([make_row(**{Columns.DATA_OBS: "2026-01-15"})])
    styler = build_styler(df)
    rendered = styler.to_html()
    assert Highlight.NAO_COMPRAR_BG.lower().replace("#", "") in rendered.lower()


def test_nao_comprar_not_applied_to_grupo_row() -> None:
    """Linha Grupo com DATA_OBS NÃO deve receber a cor de Não Comprar."""
    df = pd.DataFrame(
        [
            make_row(
                **{
                    Columns.LOCALIZACAO: GroupLabels.GROUP_ROW,
                    Columns.DATA_OBS: "2026-01-15",
                }
            )
        ]
    )
    styler = build_styler(df)
    rendered = styler.to_html()
    # NAO_COMPRAR_BG should NOT appear (Grupo takes precedence)
    assert Highlight.NAO_COMPRAR_BG.lower().replace("#", "") not in rendered.lower()


# ---------------------------------------------------------------------------
# Tests — Regra 3: Rutura
# ---------------------------------------------------------------------------


def test_rutura_red_background_on_proposta() -> None:
    """Linha com DIR preenchido → Proposta com fundo vermelho."""
    df = pd.DataFrame([make_row(**{Columns.DIR: "2026-01-01"})])
    styler = build_styler(df)
    rendered = styler.to_html()
    assert Highlight.RUTURA_BG.lower().replace("#", "") in rendered.lower()


def test_rutura_not_applied_to_grupo_row() -> None:
    """Linha Grupo com DIR NÃO deve receber a cor de Rutura."""
    df = pd.DataFrame(
        [
            make_row(
                **{
                    Columns.LOCALIZACAO: GroupLabels.GROUP_ROW,
                    Columns.DIR: "2026-01-01",
                }
            )
        ]
    )
    styler = build_styler(df)
    rendered = styler.to_html()
    assert Highlight.RUTURA_BG.lower().replace("#", "") not in rendered.lower()


# ---------------------------------------------------------------------------
# Tests — Regra 4: Validade Curta
# ---------------------------------------------------------------------------


def test_validade_curta_orange_background() -> None:
    """Célula DTVAL com validade ≤ 4 meses → fundo laranja."""
    df = pd.DataFrame([make_row(**{Columns.DTVAL: EXPIRY_SOON})])
    styler = build_styler(df)
    rendered = styler.to_html()
    assert Highlight.VALIDADE_BG.lower().replace("#", "") in rendered.lower()


def test_validade_curta_not_triggered_for_far_date() -> None:
    """DTVAL em 2030 → NÃO deve ter fundo laranja."""
    df = pd.DataFrame([make_row(**{Columns.DTVAL: "12/2030"})])
    styler = build_styler(df)
    rendered = styler.to_html()
    # FFA500 should not appear (date is far in the future)
    assert Highlight.VALIDADE_BG.lower().replace("#", "") not in rendered.lower()


# ---------------------------------------------------------------------------
# Tests — Regra 5: Preço Anómalo
# ---------------------------------------------------------------------------


def test_price_anomaly_warning_prefix() -> None:
    """Célula PVP_Médio com price_anomaly=True → prefixo ⚠️ no valor."""
    df = pd.DataFrame([make_row(**{Columns.PRICE_ANOMALY: True, Columns.PVP_MEDIO: 0.0})])
    styler = build_styler(df)
    rendered = styler.to_html()
    assert "⚠️" in rendered


def test_no_anomaly_no_prefix() -> None:
    """Linha normal (price_anomaly=False) NÃO deve ter prefixo ⚠️."""
    df = pd.DataFrame([make_row(**{Columns.PRICE_ANOMALY: False, Columns.PVP_MEDIO: 5.0})])
    styler = build_styler(df)
    rendered = styler.to_html()
    assert "⚠️" not in rendered


# ---------------------------------------------------------------------------
# Tests — build_styler returns a valid Styler
# ---------------------------------------------------------------------------


def test_build_styler_returns_styler_object() -> None:
    """build_styler deve retornar um objeto Styler válido."""
    df = pd.DataFrame([make_row()])
    styler = build_styler(df)
    assert hasattr(styler, "to_html")
    assert hasattr(styler, "apply")


def test_build_styler_empty_dataframe() -> None:
    """build_styler deve lidar com DataFrame vazio sem erro."""
    df = pd.DataFrame(columns=[Columns.CODIGO, Columns.DESIGNACAO, Columns.LOCALIZACAO])
    styler = build_styler(df)
    assert styler is not None
