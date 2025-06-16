"""
Testes unitários para o Gerenciador de Autenticação (AuthManager).

Este módulo testa:
- Geração de credenciais de cliente
- Armazenamento seguro usando keyring
- Autenticação com servidor
- Validação de dados com Pydantic
- Gerenciamento de configurações
"""

import pytest
import json
import tempfile
import uuid
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta

from app.auth_manager import (
    AuthManager, 
    ClientCredentials, 
    AuthConfig, 
    AuthenticationError,
    setup_authentication,
    get_auth_headers,
    is_client_authenticated
)


@pytest.mark.unit
@pytest.mark.core
class TestClientCredentials:
    """Testes para o modelo ClientCredentials"""
    
    def test_valid_credentials_creation(self):
        """Testa criação de credenciais válidas"""
        credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 32,  # 32 caracteres
            installation_id=str(uuid.uuid4())
        )
        
        assert credentials.client_id == "nepemcert_test_123456789"
        assert len(credentials.client_key) == 32
        assert credentials.installation_id
        assert isinstance(credentials.created_at, datetime)
        assert credentials.last_used is None
    
    def test_invalid_client_id_validation(self):
        """Testa validação de client_id inválido"""
        with pytest.raises(ValueError, match="Client ID deve ter pelo menos 10 caracteres"):
            ClientCredentials(
                client_id="short",
                client_key="a" * 32,
                installation_id=str(uuid.uuid4())
            )
    
    def test_invalid_client_key_validation(self):
        """Testa validação de client_key inválido"""
        with pytest.raises(ValueError, match="Client key deve ter pelo menos 32 caracteres"):
            ClientCredentials(
                client_id="nepemcert_test_123456789",
                client_key="short",
                installation_id=str(uuid.uuid4())
            )
    
    def test_empty_values_validation(self):
        """Testa validação com valores vazios"""
        with pytest.raises(ValueError):
            ClientCredentials(
                client_id="",
                client_key="a" * 32,
                installation_id=str(uuid.uuid4())
            )


@pytest.mark.unit
@pytest.mark.core
class TestAuthConfig:
    """Testes para o modelo AuthConfig"""
    
    def test_default_config_creation(self):
        """Testa criação de configuração padrão"""
        config = AuthConfig()
        
        assert config.server_url == "https://nepem-server.netlify.app"
        assert config.timeout == 30
        assert config.retry_attempts == 3
        assert config.keyring_service == "NEPEMCERT"
    
    def test_custom_config_creation(self):
        """Testa criação de configuração personalizada"""
        config = AuthConfig(
            server_url="https://custom-server.com",
            timeout=60,
            retry_attempts=5,
            keyring_service="CUSTOM_SERVICE"
        )
        
        assert config.server_url == "https://custom-server.com"
        assert config.timeout == 60
        assert config.retry_attempts == 5
        assert config.keyring_service == "CUSTOM_SERVICE"


@pytest.mark.unit
@pytest.mark.core
class TestAuthManager:
    """Testes para a classe AuthManager"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Cria diretório temporário para configurações"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def auth_manager(self, temp_config_dir):
        """Cria instância do AuthManager para testes"""
        return AuthManager(config_dir=temp_config_dir)
    
    def test_auth_manager_initialization(self, auth_manager, temp_config_dir):
        """Testa inicialização do AuthManager"""
        assert auth_manager.config_dir == temp_config_dir
        assert auth_manager.config_file == temp_config_dir / "auth_config.json"
        assert auth_manager.credentials_file == temp_config_dir / "credentials.json"
        assert isinstance(auth_manager.config, AuthConfig)
    
    def test_generate_client_key(self, auth_manager):
        """Testa geração de chave do cliente"""
        key1 = auth_manager._generate_client_key()
        key2 = auth_manager._generate_client_key()
        
        # Chaves devem ser diferentes
        assert key1 != key2
        
        # Devem ter tamanho adequado (base64 de 32 bytes = 44 caracteres)
        assert len(key1) == 44
        assert len(key2) == 44
        
        # Devem ser base64 válido
        import base64
        assert base64.b64decode(key1)
        assert base64.b64decode(key2)
    
    def test_generate_installation_id(self, auth_manager):
        """Testa geração de ID de instalação"""
        id1 = auth_manager._generate_installation_id()
        id2 = auth_manager._generate_installation_id()
        
        # IDs devem ser diferentes
        assert id1 != id2
        
        # Devem ser UUIDs válidos
        assert uuid.UUID(id1)
        assert uuid.UUID(id2)
    
    @patch('keyring.set_password')
    def test_store_credentials_secure(self, mock_set_password, auth_manager):
        """Testa armazenamento seguro de credenciais"""
        credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        auth_manager._store_credentials_secure(credentials)
        
        # Verifica se keyring foi chamado
        mock_set_password.assert_called_once_with(
            "NEPEMCERT",
            "client_key",
            credentials.client_key
        )
        
        # Verifica se arquivo de metadados foi criado
        assert auth_manager.credentials_file.exists()
        
        # Verifica conteúdo do arquivo
        with open(auth_manager.credentials_file, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["client_id"] == credentials.client_id
        assert metadata["installation_id"] == credentials.installation_id
        assert "client_key" not in metadata  # Não deve estar no arquivo
    
    @patch('keyring.set_password')
    def test_store_credentials_secure_error(self, mock_set_password, auth_manager):
        """Testa erro no armazenamento de credenciais"""
        mock_set_password.side_effect = Exception("Keyring error")
        
        credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        with pytest.raises(AuthenticationError, match="Erro ao armazenar credenciais"):
            auth_manager._store_credentials_secure(credentials)
    
    @patch('keyring.get_password')
    def test_load_credentials_secure(self, mock_get_password, auth_manager):
        """Testa carregamento seguro de credenciais"""
        # Prepara dados de teste
        test_client_key = "a" * 44
        test_credentials = {
            "client_id": "nepemcert_test_123456789",
            "installation_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        # Simula arquivo de metadados
        with open(auth_manager.credentials_file, 'w') as f:
            json.dump(test_credentials, f)
        
        # Configura mock do keyring
        mock_get_password.return_value = test_client_key
        
        # Testa carregamento
        credentials = auth_manager._load_credentials_secure()
        
        assert credentials is not None
        assert credentials.client_id == test_credentials["client_id"]
        assert credentials.client_key == test_client_key
        assert credentials.installation_id == test_credentials["installation_id"]
        
        # Verifica se keyring foi chamado
        mock_get_password.assert_called_once_with("NEPEMCERT", "client_key")
    
    @patch('keyring.get_password')
    def test_load_credentials_secure_missing_file(self, mock_get_password, auth_manager):
        """Testa carregamento quando arquivo não existe"""
        credentials = auth_manager._load_credentials_secure()
        assert credentials is None
        mock_get_password.assert_not_called()
    
    @patch('keyring.get_password')
    def test_load_credentials_secure_missing_keyring(self, mock_get_password, auth_manager):
        """Testa carregamento quando chave não está no keyring"""
        # Cria arquivo de metadados
        test_credentials = {
            "client_id": "nepemcert_test_123456789",
            "installation_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        with open(auth_manager.credentials_file, 'w') as f:
            json.dump(test_credentials, f)
        
        # Simula chave não encontrada no keyring
        mock_get_password.return_value = None
        
        credentials = auth_manager._load_credentials_secure()
        assert credentials is None
    
    @patch.object(AuthManager, '_store_credentials_secure')
    def test_setup_client_new(self, mock_store, auth_manager):
        """Testa configuração de novo cliente"""
        credentials = auth_manager.setup_client()
        
        assert credentials is not None
        assert credentials.client_id.startswith("nepemcert_")
        assert len(credentials.client_key) == 44
        assert credentials.installation_id
        
        # Verifica se credenciais foram armazenadas
        mock_store.assert_called_once()
        
        # Verifica se credenciais ficaram em memória
        assert auth_manager._credentials == credentials
    
    @patch.object(AuthManager, '_load_credentials_secure')
    def test_setup_client_existing(self, mock_load, auth_manager):
        """Testa configuração com cliente existente"""
        existing_credentials = ClientCredentials(
            client_id="nepemcert_existing_123",
            client_key="b" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_load.return_value = existing_credentials
        
        credentials = auth_manager.setup_client()
        
        assert credentials == existing_credentials
        assert auth_manager._credentials == existing_credentials
    
    @patch.object(AuthManager, '_load_credentials_secure')
    @patch.object(AuthManager, '_store_credentials_secure')
    def test_setup_client_force_regenerate(self, mock_store, mock_load, auth_manager):
        """Testa regeneração forçada de credenciais"""
        existing_credentials = ClientCredentials(
            client_id="nepemcert_existing_123",
            client_key="b" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_load.return_value = existing_credentials
        
        credentials = auth_manager.setup_client(force_regenerate=True)
        
        # Não deve usar as credenciais existentes
        assert credentials != existing_credentials
        assert credentials.client_id != existing_credentials.client_id
        
        # Deve armazenar novas credenciais
        mock_store.assert_called_once()
    
    def test_get_credentials_cached(self, auth_manager):
        """Testa obtenção de credenciais em cache"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        auth_manager._credentials = test_credentials
        
        credentials = auth_manager.get_credentials()
        assert credentials == test_credentials
    
    @patch.object(AuthManager, '_load_credentials_secure')
    def test_get_credentials_from_storage(self, mock_load, auth_manager):
        """Testa obtenção de credenciais do armazenamento"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_load.return_value = test_credentials
        
        credentials = auth_manager.get_credentials()
        
        assert credentials == test_credentials
        assert auth_manager._credentials == test_credentials
        mock_load.assert_called_once()
    
    def test_authenticate_no_credentials(self, auth_manager):
        """Testa autenticação sem credenciais"""
        with pytest.raises(AuthenticationError, match="Credenciais não encontradas"):
            auth_manager.authenticate()
    
    @patch.object(AuthManager, 'get_credentials')
    @patch.object(AuthManager, '_store_credentials_secure')
    def test_authenticate_success(self, mock_store, mock_get_credentials, auth_manager):
        """Testa autenticação bem-sucedida"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_get_credentials.return_value = test_credentials
        
        result = auth_manager.authenticate()
        
        assert result is True
        
        # Verifica se last_used foi atualizado
        assert test_credentials.last_used is not None
        mock_store.assert_called_once_with(test_credentials)
    
    def test_get_auth_headers_no_credentials(self, auth_manager):
        """Testa obtenção de headers sem credenciais"""
        with pytest.raises(AuthenticationError, match="Credenciais não disponíveis"):
            auth_manager.get_auth_headers()
    
    @patch.object(AuthManager, 'get_credentials')
    def test_get_auth_headers_success(self, mock_get_credentials, auth_manager):
        """Testa obtenção de headers de autenticação"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_get_credentials.return_value = test_credentials
        
        headers = auth_manager.get_auth_headers()
        
        expected_headers = {
            "Authorization": f"Bearer {test_credentials.client_key}",
            "X-Client-ID": test_credentials.client_id,
            "X-Installation-ID": test_credentials.installation_id,
            "User-Agent": "NEPEMCERT/1.0"
        }
        
        assert headers == expected_headers
    
    @patch.object(AuthManager, 'get_credentials')
    def test_is_authenticated_no_credentials(self, mock_get_credentials, auth_manager):
        """Testa verificação de autenticação sem credenciais"""
        mock_get_credentials.return_value = None
        
        assert auth_manager.is_authenticated() is False
    
    @patch.object(AuthManager, 'get_credentials')
    def test_is_authenticated_valid(self, mock_get_credentials, auth_manager):
        """Testa verificação de autenticação válida"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4()),
            last_used=datetime.now()
        )
        
        mock_get_credentials.return_value = test_credentials
        
        assert auth_manager.is_authenticated() is True
    
    @patch.object(AuthManager, 'get_credentials')
    def test_is_authenticated_expired(self, mock_get_credentials, auth_manager):
        """Testa verificação de autenticação expirada"""
        # Credenciais com last_used há 31 dias
        expired_date = datetime.now() - timedelta(days=31)
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4()),
            last_used=expired_date
        )
        
        mock_get_credentials.return_value = test_credentials
        
        assert auth_manager.is_authenticated() is False
    
    @patch('keyring.delete_password')
    def test_revoke_credentials(self, mock_delete_password, auth_manager):
        """Testa revogação de credenciais"""
        # Cria arquivo de credenciais
        test_credentials = {
            "client_id": "nepemcert_test_123456789",
            "installation_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }
        
        with open(auth_manager.credentials_file, 'w') as f:
            json.dump(test_credentials, f)
        
        # Define credenciais em memória
        auth_manager._credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        auth_manager.revoke_credentials()
        
        # Verifica se keyring foi chamado
        mock_delete_password.assert_called_once_with("NEPEMCERT", "client_key")
        
        # Verifica se arquivo foi removido
        assert not auth_manager.credentials_file.exists()
        
        # Verifica se credenciais em memória foram limpas
        assert auth_manager._credentials is None
    
    @patch.object(AuthManager, 'get_credentials')
    @patch.object(AuthManager, 'is_authenticated')
    def test_get_client_info(self, mock_is_authenticated, mock_get_credentials, auth_manager):
        """Testa obtenção de informações do cliente"""
        test_date = datetime(2024, 1, 15, 10, 30, 0)
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4()),
            created_at=test_date,
            last_used=test_date
        )
        
        mock_get_credentials.return_value = test_credentials
        mock_is_authenticated.return_value = True
        
        info = auth_manager.get_client_info()
        
        expected_info = {
            "client_id": test_credentials.client_id,
            "installation_id": test_credentials.installation_id,
            "created_at": "15/01/2024 10:30",
            "last_used": "15/01/2024 10:30",
            "is_authenticated": True
        }
        
        assert info == expected_info
    
    @patch.object(AuthManager, 'get_credentials')
    def test_get_client_info_no_credentials(self, mock_get_credentials, auth_manager):
        """Testa obtenção de informações sem credenciais"""
        mock_get_credentials.return_value = None
        
        info = auth_manager.get_client_info()
        assert info is None
    
    def test_update_config(self, auth_manager):
        """Testa atualização de configuração"""
        auth_manager.update_config(
            server_url="https://new-server.com",
            timeout=60
        )
        
        assert auth_manager.config.server_url == "https://new-server.com"
        assert auth_manager.config.timeout == 60
        assert auth_manager.config.retry_attempts == 3  # Mantém valor padrão
        
        # Verifica se foi salvo
        assert auth_manager.config_file.exists()


@pytest.mark.unit
@pytest.mark.core
class TestConvenienceFunctions:
    """Testes para funções de conveniência"""
    
    @patch('app.auth_manager.auth_manager')
    def test_setup_authentication(self, mock_auth_manager):
        """Testa função de conveniência setup_authentication"""
        test_credentials = ClientCredentials(
            client_id="nepemcert_test_123456789",
            client_key="a" * 44,
            installation_id=str(uuid.uuid4())
        )
        
        mock_auth_manager.setup_client.return_value = test_credentials
        
        result = setup_authentication(force_regenerate=True)
        
        assert result == test_credentials
        mock_auth_manager.setup_client.assert_called_once_with(True)
    
    @patch('app.auth_manager.auth_manager')
    def test_get_auth_headers_convenience(self, mock_auth_manager):
        """Testa função de conveniência get_auth_headers"""
        expected_headers = {
            "Authorization": "Bearer test_key",
            "X-Client-ID": "test_client_id"
        }
        
        mock_auth_manager.get_auth_headers.return_value = expected_headers
        
        result = get_auth_headers()
        
        assert result == expected_headers
        mock_auth_manager.get_auth_headers.assert_called_once()
    
    @patch('app.auth_manager.auth_manager')
    def test_is_client_authenticated_convenience(self, mock_auth_manager):
        """Testa função de conveniência is_client_authenticated"""
        mock_auth_manager.is_authenticated.return_value = True
        
        result = is_client_authenticated()
        
        assert result is True
        mock_auth_manager.is_authenticated.assert_called_once()


@pytest.mark.unit
@pytest.mark.core
class TestAuthenticationError:
    """Testes para exceção AuthenticationError"""
    
    def test_authentication_error_creation(self):
        """Testa criação de exceção de autenticação"""
        error = AuthenticationError("Teste de erro")
        assert str(error) == "Teste de erro"
        assert isinstance(error, Exception)
