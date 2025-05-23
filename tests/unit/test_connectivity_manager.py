"""
Testes para o módulo connectivity_manager.py
"""
import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime

# Marca todos os testes neste arquivo como testes de unidade
pytestmark = pytest.mark.unit

@pytest.fixture
def connectivity_manager():
    """Fixture que retorna uma instância do ConnectivityManager"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from app.connectivity_manager import ConnectivityManager
    
    # Use um diretório temporário para testes
    test_config_dir = "tests/temp_config"
    os.makedirs(test_config_dir, exist_ok=True)
    
    return ConnectivityManager(config_dir=test_config_dir)

def test_init(connectivity_manager):
    """Testa a inicialização do ConnectivityManager."""
    assert connectivity_manager.config_dir == "tests/temp_config"
    assert os.path.exists("tests/temp_config")

def test_default_config(connectivity_manager):
    """Testa a configuração padrão."""
    config = connectivity_manager.config
    
    assert "server_url" in config
    assert "api_key" in config
    assert "username" in config
    assert "password" in config
    assert "connection_status" in config
    assert "auto_sync" in config
    assert config["connection_status"] == "Desconectado"
    assert not config["auto_sync"]

def test_save_load_config(connectivity_manager, tmp_path):
    """Testa salvar e carregar configurações."""
    # Definir valores para salvar
    connectivity_manager.set_server_url("https://teste.com")
    connectivity_manager.set_api_key("chave-teste")
    connectivity_manager.set_credentials("usuario", "senha")
    
    # Salvar configuração
    connectivity_manager.save_config()
    
    # Verificar se o arquivo foi criado
    assert os.path.exists(connectivity_manager.config_file)
    
    # Criar uma nova instância para carregar a configuração
    from app.connectivity_manager import ConnectivityManager
    new_manager = ConnectivityManager(config_dir=connectivity_manager.config_dir)
    
    # Verificar se as configurações foram carregadas corretamente
    assert new_manager.config["server_url"] == "https://teste.com"
    assert new_manager.config["api_key"] == "chave-teste"
    assert new_manager.config["username"] == "usuario"
    assert new_manager.config["password"] == "senha"

def test_check_connection(connectivity_manager):
    """Testa a verificação de conexão."""
    # Com servidor não configurado
    result = connectivity_manager.check_connection()
    assert result["status"] == "Desconectado"
    
    # Com servidor configurado
    connectivity_manager.set_server_url("https://teste.com")
    result = connectivity_manager.check_connection()
    
    # O resultado pode variar devido à aleatoriedade na simulação
    assert result["status"] in ["Conectado", "Desconectado"]
    assert "message" in result
    assert "timestamp" in result

def test_toggle_auto_sync(connectivity_manager):
    """Testa alternar sincronização automática."""
    # Valor inicial deve ser falso
    assert not connectivity_manager.config["auto_sync"]
    
    # Ativar
    result = connectivity_manager.toggle_auto_sync(True)
    assert result is True
    assert connectivity_manager.config["auto_sync"] is True
    
    # Desativar
    result = connectivity_manager.toggle_auto_sync(False)
    assert result is False
    assert connectivity_manager.config["auto_sync"] is False
    
    # Alternar (toggle)
    result = connectivity_manager.toggle_auto_sync()
    assert result is True
    assert connectivity_manager.config["auto_sync"] is True

# Limpar o diretório de configuração após todos os testes
@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_config():
    yield
    import shutil
    if os.path.exists("tests/temp_config"):
        shutil.rmtree("tests/temp_config")
