import pandas as pd
import pytest

from orders_master.business_logic.averages import load_presets, select_window, weighted_average


def test_select_window():
    # Vendas: V4, V3, V2, V1, V0, T Uni
    df = pd.DataFrame({"V4": [1], "V3": [2], "V2": [3], "V1": [4], "V0": [5], "T Uni": [15]})

    # Normal (offset=1)
    cols = select_window(df, use_previous_month=False, weights_len=4)
    assert cols == ["V0", "V1", "V2", "V3"]

    # Previous month (offset=2)
    cols_prev = select_window(df, use_previous_month=True, weights_len=4)
    assert cols_prev == ["V1", "V2", "V3", "V4"]

    # Out of bounds
    with pytest.raises(AssertionError):
        select_window(df, use_previous_month=True, weights_len=5)


def test_weighted_average():
    df = pd.DataFrame(
        {
            "V4": [0, 0],
            "V3": [10, 0],
            "V2": [20, 10],
            "V1": [30, 20],
            "V0": [40, 30],
            "T Uni": [100, 60],
        }
    )

    weights = (0.4, 0.3, 0.2, 0.1)

    res = weighted_average(df, weights, use_previous_month=False)
    assert isinstance(res, pd.Series)
    assert pytest.approx(res.iloc[0]) == 30.0

    res_prev = weighted_average(df, weights, use_previous_month=True)
    assert pytest.approx(res_prev.iloc[0]) == 20.0


def test_weighted_average_invalid_weights():
    df = pd.DataFrame({"V0": [1], "T Uni": [1]})
    with pytest.raises(AssertionError):
        weighted_average(df, (0.5, 0.5, 0.5), use_previous_month=False)


def test_load_presets(tmp_path):
    yaml_content = """
presets:
  Conservador: [0.5, 0.3, 0.15, 0.05]
  Padrão: [0.4, 0.3, 0.2, 0.1]
  Agressivo: [0.25, 0.25, 0.25, 0.25]
"""
    p = tmp_path / "presets.yaml"
    p.write_text(yaml_content, encoding="utf-8")

    presets = load_presets(p)
    assert len(presets) == 3
    assert presets["Conservador"] == (0.5, 0.3, 0.15, 0.05)
    assert presets["Padrão"] == (0.4, 0.3, 0.2, 0.1)

    for w in presets.values():
        assert abs(sum(w) - 1.0) < 1e-3


def test_real_presets_validity():
    # Verifica se o ficheiro config/presets.yaml obedece à regra de pesos somarem 1.0
    presets = load_presets("config/presets.yaml")
    for name, weights in presets.items():
        assert abs(sum(weights) - 1.0) < 1e-3
