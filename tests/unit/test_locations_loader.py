import json

import pytest

from orders_master.config.locations_loader import (
    LocationsConfig,
    get_file_mtime,
    load_locations,
    map_location,
)
from orders_master.exceptions import ConfigError


@pytest.fixture
def temp_locations_json(tmp_path):
    """Fixture to create a temporary localizacoes.json file."""
    p = tmp_path / "localizacoes.json"
    data = {"ilha": "Ilha", "Souto": "Souto", "Colmeias": "Colmeias"}
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_load_locations_valid(temp_locations_json):
    """Test loading a valid localizacoes.json."""
    config = load_locations(get_file_mtime(temp_locations_json), path=temp_locations_json)
    assert isinstance(config, LocationsConfig)
    assert config.root["ilha"] == "Ilha"
    assert config.root["Souto"] == "Souto"


def test_load_locations_schema_validation_fail(tmp_path):
    """Test loading a JSON that fails schema validation (search term too short)."""
    p = tmp_path / "invalid_term.json"
    data = {"il": "Ilha"}  # Term too short (min 3)
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_locations(get_file_mtime(p), path=p)
    assert "Falha na validação do schema" in str(excinfo.value)
    assert "pelo menos 3 caracteres" in str(excinfo.value)


def test_map_location_exact_match():
    """Test exact match mapping."""
    aliases = {"ilha": "Ilha", "Souto": "Souto"}
    assert map_location("ilha", aliases) == "Ilha"
    assert map_location("ILHA", aliases) == "Ilha"
    assert map_location(" Souto ", aliases) == "Souto"


def test_map_location_word_boundary():
    """Test word boundary matching."""
    aliases = {"ilha": "Ilha"}
    # Should match
    assert map_location("Farmácia da Ilha", aliases) == "Ilha"
    assert map_location("ILHA GRANDE", aliases) == "Ilha"

    # Should NOT match (substring but not word boundary)
    assert map_location("Farmácia Vilha", aliases) == "Farmácia Vilha"
    assert map_location("Milhas", aliases) == "Milhas"


def test_map_location_multi_match(caplog):
    """Test multi-match logging warning and first match winning."""
    aliases = {"ilha": "Ilha", "grande ilha": "Grande Ilha"}
    # "Farmácia Grande Ilha" matches both "ilha" and "grande ilha"
    # Order in dict determines which is first.
    # In Python 3.7+, dict insertion order is preserved.
    res = map_location("Farmácia Grande Ilha", aliases)
    assert res in ["Ilha", "Grande Ilha"]
    assert "Múltiplas correspondências de localização" in caplog.text


def test_map_location_fallback():
    """Test fallback to Title Case."""
    aliases = {"ilha": "Ilha"}
    assert map_location("Farmácia Desconhecida", aliases) == "Farmácia Desconhecida"
    assert map_location("farmacia nova", aliases) == "Farmacia Nova"


def test_map_location_empty():
    """Test empty input handling."""
    assert map_location("", {"a": "b"}) == ""
    assert map_location(None, {"a": "b"}) == ""


def test_get_file_mtime_invalidation(tmp_path):
    """Test that different mtime (simulated) allows loading new data."""
    p = tmp_path / "loc.json"
    p.write_text('{"ilha": "Ilha"}', encoding="utf-8")

    mtime1 = 1.0
    config1 = load_locations(mtime1, path=p)
    assert config1.root["ilha"] == "Ilha"

    # Simulate file change and different mtime
    p.write_text('{"ilha": "Nova Ilha"}', encoding="utf-8")
    mtime2 = 2.0

    config2 = load_locations(mtime2, path=p)
    assert config2.root["ilha"] == "Nova Ilha"
