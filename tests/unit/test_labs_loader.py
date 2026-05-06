import json
from pathlib import Path

import pytest

from orders_master.config.labs_loader import LabsConfig, get_file_mtime, load_labs
from orders_master.exceptions import ConfigError


@pytest.fixture
def temp_labs_json(tmp_path):
    """Fixture to create a temporary laboratorios.json file."""
    p = tmp_path / "laboratorios.json"
    data = {"Mylan": ["123", "456"], "Zentiva": ["789"]}
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_load_labs_valid(temp_labs_json):
    """Test loading a valid laboratorios.json."""
    config = load_labs(get_file_mtime(temp_labs_json), path=temp_labs_json)
    assert isinstance(config, LabsConfig)
    assert config.root["Mylan"] == ["123", "456"]
    assert config.root["Zentiva"] == ["789"]


def test_load_labs_malformed_json(tmp_path):
    """Test loading a malformed JSON file."""
    p = tmp_path / "malformed.json"
    p.write_text("{ 'invalid': json }", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_labs(get_file_mtime(p), path=p)
    assert "JSON inválido" in str(excinfo.value)


def test_load_labs_schema_validation_fail(tmp_path):
    """Test loading a JSON that fails schema validation (invalid lab name)."""
    p = tmp_path / "invalid_name.json"
    data = {"m": ["123"]}  # Name too short (min 2)
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        load_labs(get_file_mtime(p), path=p)
    assert "Falha na validação do schema" in str(excinfo.value)


def test_load_labs_duplicate_codes(tmp_path, caplog):
    """Test loading a JSON with duplicate codes in a lab (should dedup and warn)."""
    p = tmp_path / "duplicates.json"
    data = {"Mylan": ["123", "123", "456"]}
    p.write_text(json.dumps(data), encoding="utf-8")

    config = load_labs(get_file_mtime(p), path=p)
    assert config.root["Mylan"] == ["123", "456"]
    assert "Código CLA duplicado '123' encontrado no laboratório 'Mylan'" in caplog.text


def test_load_labs_cross_lab_duplicates(tmp_path, caplog):
    """Test loading a JSON where the same code appears in multiple labs (should warn)."""
    p = tmp_path / "cross_duplicates.json"
    data = {"Mylan": ["123"], "Zentiva": ["123"]}
    p.write_text(json.dumps(data), encoding="utf-8")

    load_labs(get_file_mtime(p), path=p)
    assert "O código CLA '123' aparece em múltiplos laboratórios" in caplog.text


def test_get_file_mtime_nonexistent():
    """Test get_file_mtime for a nonexistent file."""
    assert get_file_mtime(Path("nonexistent.json")) == 0.0


def test_cli_validator(temp_labs_json, monkeypatch):
    """Test the CLI validator in validate.py."""
    from orders_master.config import validate

    # Test success
    # Mock sys.exit to avoid exiting the test process
    exits = []
    monkeypatch.setattr("sys.exit", lambda code: exits.append(code))

    validate.validate_config(str(temp_labs_json))
    assert 0 in exits

    # Test failure
    exits.clear()
    # Need to use the same name 'laboratorios.json' for it to trigger the validator
    invalid_dir = temp_labs_json.parent / "invalid"
    invalid_dir.mkdir()
    p_invalid = invalid_dir / "laboratorios.json"
    p_invalid.write_text("{", encoding="utf-8")
    validate.validate_config(str(p_invalid))
    assert 1 in exits
