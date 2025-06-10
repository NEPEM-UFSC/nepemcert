"""
Testes de unidade para o módulo parameter_manager.py
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def temp_config_file(tmp_path):
    """Cria um arquivo de configuração temporário."""
    return tmp_path / "parameters.json"

@pytest.fixture
def parameter_manager(temp_config_file):
    """Fixture que retorna uma instância do ParameterManager com um arquivo de config temporário."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.parameter_manager import ParameterManager
    # Assegurar que o diretório pai do temp_config_file exista
    os.makedirs(temp_config_file.parent, exist_ok=True)
    return ParameterManager(config_file=str(temp_config_file))

def test_init_creates_default_file(temp_config_file):
    """Testa se o ParameterManager cria um arquivo de configuração padrão se não existir."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.parameter_manager import ParameterManager
    
    assert not temp_config_file.exists()
    ParameterManager(config_file=str(temp_config_file))
    assert temp_config_file.exists()
    with open(temp_config_file, 'r') as f:
        data = json.load(f)
        assert "default_placeholders" in data
        assert "theme_placeholders" in data
        assert "institutional_placeholders" in data
        assert "system_settings" in data
        assert "debug_mode" in data["system_settings"]

def test_load_parameters_existing_file(parameter_manager, temp_config_file):
    """Testa o carregamento de parâmetros de um arquivo existente."""
    test_data = {
        "default_placeholders": {"key1": "value1"},
        "theme_placeholders": {"my_theme": {"key2": "value2"}},
        "institutional_placeholders": {"inst_key": "inst_value"},
        "system_settings": {"debug_mode": True}
    }
    with open(temp_config_file, 'w') as f:
        json.dump(test_data, f)
    
    loaded_params = parameter_manager.load_parameters()
    assert loaded_params == test_data

def test_load_parameters_json_error(parameter_manager, temp_config_file):
    """Testa o carregamento de parâmetros com JSON inválido, esperando defaults."""
    with open(temp_config_file, 'w') as f:
        f.write("esto não é json valido {")
    
    # Recriar o manager para forçar o reload com o arquivo corrompido
    from app.parameter_manager import ParameterManager
    manager = ParameterManager(config_file=str(temp_config_file))
    
    assert manager.parameters["default_placeholders"] == {}
    assert manager.parameters["system_settings"]["debug_mode"] is False

def test_save_parameters(parameter_manager, temp_config_file):
    """Testa o salvamento dos parâmetros."""
    parameter_manager.parameters["default_placeholders"]["new_key"] = "new_value"
    parameter_manager.save_parameters()
    
    with open(temp_config_file, 'r') as f:
        data = json.load(f)
        assert data["default_placeholders"]["new_key"] == "new_value"

def test_debug_mode(parameter_manager):
    """Testa getters e setters do modo debug."""
    assert not parameter_manager.get_debug_mode()  # Padrão
    parameter_manager.set_debug_mode(True)
    assert parameter_manager.get_debug_mode()
    parameter_manager.set_debug_mode(False)
    assert not parameter_manager.get_debug_mode()

def test_get_placeholders(parameter_manager):
    """Testa os getters de placeholders."""
    parameter_manager.parameters = {
        "default_placeholders": {"default_key": "default_val"},
        "theme_placeholders": {"test_theme": {"theme_key": "theme_val"}},
        "institutional_placeholders": {"inst_key": "inst_val"},
        "system_settings": {"debug_mode": False}
    }
    assert parameter_manager.get_default_placeholders() == {"default_key": "default_val"}
    assert parameter_manager.get_theme_placeholders("test_theme") == {"theme_key": "theme_val"}
    assert parameter_manager.get_theme_placeholders("non_existent_theme") == {}
    assert parameter_manager.get_institutional_placeholders() == {"inst_key": "inst_val"}

def test_update_placeholders(parameter_manager):
    """Testa os updaters de placeholders."""
    parameter_manager.update_default_placeholders({"new_default": "val_def"})
    assert parameter_manager.parameters["default_placeholders"]["new_default"] == "val_def"
    
    parameter_manager.update_theme_placeholders("new_theme", {"new_theme_key": "val_theme"})
    assert parameter_manager.parameters["theme_placeholders"]["new_theme"]["new_theme_key"] == "val_theme"
    
    parameter_manager.update_institutional_placeholders({"new_inst": "val_inst"})
    assert parameter_manager.parameters["institutional_placeholders"]["new_inst"] == "val_inst"

def test_merge_placeholders(parameter_manager):
    """Testa a mesclagem de placeholders com prioridade correta."""
    parameter_manager.parameters = {
        "default_placeholders": {"p1": "default1", "p2": "default2", "p_all": "default_all"},
        "institutional_placeholders": {"p2": "inst2", "p3": "inst3", "p_all": "inst_all"},
        "theme_placeholders": {"my_theme": {"p3": "theme3", "p4": "theme4", "p_all": "theme_all"}},
        "system_settings": {"debug_mode": False}
    }
    csv_data = {"p4": "csv4", "p5": "csv5", "p_all": "csv_all"}
    
    # Sem tema
    merged = parameter_manager.merge_placeholders(csv_data)
    assert merged["p1"] == "default1"
    assert merged["p2"] == "inst2"  # Institucional sobrepõe default
    assert merged["p3"] == "inst3"
    assert merged["p4"] == "csv4"   # CSV sobrepõe tudo
    assert merged["p5"] == "csv5"
    assert merged["p_all"] == "csv_all"

    # Com tema
    merged_with_theme = parameter_manager.merge_placeholders(csv_data, theme_name="my_theme")
    assert merged_with_theme["p1"] == "default1"
    assert merged_with_theme["p2"] == "inst2"
    assert merged_with_theme["p3"] == "theme3" # Tema sobrepõe institucional
    assert merged_with_theme["p4"] == "csv4"   # CSV sobrepõe tema
    assert merged_with_theme["p5"] == "csv5"
    assert merged_with_theme["p_all"] == "csv_all"

    # CSV data é None
    merged_no_csv = parameter_manager.merge_placeholders(None, theme_name="my_theme")
    assert merged_no_csv["p_all"] == "theme_all"
    assert "p5" not in merged_no_csv
