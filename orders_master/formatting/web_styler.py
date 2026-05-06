"""
Web Styler — TASK-41.

Implementa ``build_styler(df)`` que aplica as 5 regras de ``RULES`` ao
Pandas Styler para renderização web, seguindo PRD §6.1.6.

Precedência: a regra com menor ``precedence`` tem maior prioridade.
Para a linha Grupo (precedência 1) as regras 2-5 não são aplicadas.
"""
import pandas as pd

from orders_master.constants import Columns, GroupLabels
from orders_master.formatting.rules import RULES, HighlightRule


def _css_for_row(row: pd.Series, rule: HighlightRule, target_cols: list[str]) -> list[str]:
    """
    Devolve uma lista de strings CSS, uma por coluna do row.
    Colunas que são alvo da regra recebem ``rule.css_web``; as restantes ficam vazias.
    """
    return [rule.css_web if col in target_cols else "" for col in row.index]


def build_styler(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """
    Constrói o Pandas Styler aplicando as 5 regras de formatação por ordem
    de precedência (menor precedence = maior prioridade).

    Para a linha de Grupo (LOCALIZACAO == 'Grupo'), apenas a regra 1 é aplicada —
    as regras 2-5 são ignoradas para não sobrepor a cor de fundo preta.

    Para a regra "Preço Anómalo" adiciona ainda o prefixo ``⚠️`` ao valor da célula.

    Args:
        df: DataFrame agregado ou detalhado pronto a apresentar.

    Returns:
        pd.io.formats.style.Styler configurado com a formatação condicional.
    """
    styler = df.style

    # Aplicar cada regra por ordem de precedência
    for rule in RULES:
        target_cols = rule.target_cells(df)
        if not target_cols:
            continue

        def _apply_rule(row: pd.Series, _rule: HighlightRule = rule, _targets: list[str] = target_cols) -> list[str]:
            # Linha Grupo → só aplica regra 1 (Grupo); ignora 2-5
            is_grupo = row.get(Columns.LOCALIZACAO) == GroupLabels.GROUP_ROW
            if is_grupo and _rule.precedence > 1:
                return [""] * len(row)

            if _rule.predicate(row):
                return _css_for_row(row, _rule, _targets)
            return [""] * len(row)

        styler = styler.apply(_apply_rule, axis=1)  # type: ignore[arg-type]

    # Regra especial: Preço Anómalo → prefixo ⚠️ na célula de PVP
    price_rule = next((r for r in RULES if r.name == "Preço Anómalo"), None)
    if price_rule is not None:
        pvp_col = (
            Columns.PVP_MEDIO
            if Columns.PVP_MEDIO in df.columns
            else (Columns.PVP if Columns.PVP in df.columns else None)
        )
        if pvp_col is not None and Columns.PRICE_ANOMALY in df.columns:

            def _fmt_anomaly(val: object, row_idx: int, _col: str = pvp_col) -> str:
                row = df.iloc[row_idx]
                if bool(row.get(Columns.PRICE_ANOMALY, False)):
                    return f"⚠️ {val}"
                return str(val) if val is not None else ""

            # Use Styler.format with a positional formatter per cell
            styler = styler.format(
                {pvp_col: lambda v, r=df: (
                    f"⚠️ {v}" if r.loc[r[Columns.PVP_MEDIO if Columns.PVP_MEDIO in r.columns else Columns.PVP] == v].iloc[0:1][Columns.PRICE_ANOMALY].any()
                    else v
                )},
                na_rep="",
            )

    return styler
