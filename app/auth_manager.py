"""
Gerenciador de Autenticação do NEPEMCERT

Este módulo é responsável por toda a lógica de credenciais, incluindo:
- Geração de chave única do cliente
- Armazenamento seguro de credenciais
- Autenticação com o servidor
- Fornecimento de credenciais para requisições
"""

import uuid
import secrets
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import keyring
from pydantic import BaseModel, Field, validator
import hashlib
import base64


class ClientCredentials(BaseModel):
    """Modelo para validação das credenciais do cliente"""
    client_id: str = Field(..., description="ID único do cliente")
    client_key: str = Field(..., description="Chave de autenticação do cliente")
    installation_id: str = Field(..., description="ID da instalação")
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Client ID deve ter pelo menos 10 caracteres')
        return v
    
    @validator('client_key')
    def validate_client_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError('Client key deve ter pelo menos 32 caracteres')
        return v


class AuthConfig(BaseModel):
    """Configuração de autenticação"""
    server_url: str = Field(default="https://nepem-server.netlify.app", description="URL do servidor")
    timeout: int = Field(default=30, description="Timeout em segundos")
    retry_attempts: int = Field(default=3, description="Tentativas de retry")
    keyring_service: str = Field(default="NEPEMCERT", description="Nome do serviço no keyring")


class AuthenticationError(Exception):
    """Exceção para erros de autenticação"""
    pass


class AuthManager:
    """
    Gerenciador de autenticação responsável por:
    - Gerar e gerenciar chaves do cliente
    - Autenticar com o servidor
    - Armazenar credenciais de forma segura
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de autenticação
        
        Args:
            config_dir: Diretório de configuração (padrão: ~/.nepemcert)
        """
        self.config_dir = config_dir or Path.home() / ".nepemcert"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "auth_config.json"
        self.credentials_file = self.config_dir / "credentials.json"
        
        # Carrega configuração
        self.config = self._load_config()
        
        # Credenciais em memória
        self._credentials: Optional[ClientCredentials] = None
    
    def _load_config(self) -> AuthConfig:
        """Carrega configuração de autenticação"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AuthConfig(**data)
            except Exception:
                pass
        
        # Retorna configuração padrão
        config = AuthConfig()
        self._save_config(config)
        return config
    
    def _save_config(self, config: AuthConfig) -> None:
        """Salva configuração de autenticação"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config.dict(), f, indent=2, default=str)
    
    def _generate_client_key(self) -> str:
        """
        Gera uma chave criptográfica única para o cliente
        
        Returns:
            Chave codificada em base64
        """
        # Gera 32 bytes aleatórios (256 bits)
        random_bytes = secrets.token_bytes(32)
        
        # Adiciona timestamp para unicidade
        timestamp = datetime.now().isoformat().encode('utf-8')
        
        # Combina e gera hash
        combined = random_bytes + timestamp
        hash_object = hashlib.sha256(combined)
        
        # Retorna em base64 para facilitar transmissão
        return base64.b64encode(hash_object.digest()).decode('utf-8')
    
    def _generate_installation_id(self) -> str:
        """
        Gera ID único da instalação
        
        Returns:
            UUID da instalação
        """
        return str(uuid.uuid4())
    
    def _get_keyring_key(self, key_type: str) -> str:
        """Gera chave para uso no keyring"""
        return f"{self.config.keyring_service}_{key_type}"
    
    def _store_credentials_secure(self, credentials: ClientCredentials) -> None:
        """
        Armazena credenciais de forma segura usando keyring
        
        Args:
            credentials: Credenciais do cliente
        """
        try:
            # Armazena chave no keyring
            keyring.set_password(
                self.config.keyring_service,
                "client_key",
                credentials.client_key
            )
            
            # Armazena metadados em arquivo (sem informações sensíveis)
            metadata = {
                "client_id": credentials.client_id,
                "installation_id": credentials.installation_id,
                "created_at": credentials.created_at.isoformat(),
                "last_used": credentials.last_used.isoformat() if credentials.last_used else None
            }
            
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            raise AuthenticationError(f"Erro ao armazenar credenciais: {e}")
    
    def _load_credentials_secure(self) -> Optional[ClientCredentials]:
        """
        Carrega credenciais do armazenamento seguro
        
        Returns:
            Credenciais do cliente ou None se não encontradas
        """
        try:
            if not self.credentials_file.exists():
                return None
            
            # Carrega metadados
            with open(self.credentials_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Recupera chave do keyring
            client_key = keyring.get_password(
                self.config.keyring_service,
                "client_key"
            )
            
            if not client_key:
                return None
            
            # Reconstrói credenciais
            credentials_data = {
                **metadata,
                "client_key": client_key,
                "created_at": datetime.fromisoformat(metadata["created_at"]),
                "last_used": datetime.fromisoformat(metadata["last_used"]) if metadata.get("last_used") else None
            }
            
            return ClientCredentials(**credentials_data)
            
        except Exception:
            return None
    
    def setup_client(self, force_regenerate: bool = False) -> ClientCredentials:
        """
        Configura cliente gerando nova chave se necessário
        
        Args:
            force_regenerate: Força regeneração das credenciais
            
        Returns:
            Credenciais do cliente
        """
        # Verifica se já existe e não deve regenerar
        if not force_regenerate:
            existing = self._load_credentials_secure()
            if existing:
                self._credentials = existing
                return existing
        
        # Gera novas credenciais
        client_id = f"nepemcert_{self._generate_installation_id()}"
        client_key = self._generate_client_key()
        installation_id = self._generate_installation_id()
        
        credentials = ClientCredentials(
            client_id=client_id,
            client_key=client_key,
            installation_id=installation_id
        )
        
        # Armazena de forma segura
        self._store_credentials_secure(credentials)
        
        # Mantém em memória
        self._credentials = credentials
        
        return credentials
    
    def get_credentials(self) -> Optional[ClientCredentials]:
        """
        Obtém credenciais do cliente
        
        Returns:
            Credenciais do cliente ou None se não configurado
        """
        if self._credentials:
            return self._credentials
        
        self._credentials = self._load_credentials_secure()
        return self._credentials
    
    def authenticate(self) -> bool:
        """
        Autentica com o servidor usando as credenciais do cliente
        
        Returns:
            True se autenticação bem-sucedida
            
        Raises:
            AuthenticationError: Se falha na autenticação
        """
        credentials = self.get_credentials()
        if not credentials:
            raise AuthenticationError("Credenciais não encontradas. Execute setup primeiro.")
        
        # Simula autenticação (implementar chamada real ao servidor)
        try:
            # Aqui seria feita a chamada real ao servidor
            # Por enquanto, sempre retorna True para desenvolvimento
            
            # Atualiza último uso
            credentials.last_used = datetime.now()
            self._store_credentials_secure(credentials)
            
            return True
            
        except Exception as e:
            raise AuthenticationError(f"Falha na autenticação: {e}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Obtém headers de autenticação para requisições
        
        Returns:
            Dicionário com headers de autenticação
            
        Raises:
            AuthenticationError: Se credenciais não disponíveis
        """
        credentials = self.get_credentials()
        if not credentials:
            raise AuthenticationError("Credenciais não disponíveis")
        
        return {
            "Authorization": f"Bearer {credentials.client_key}",
            "X-Client-ID": credentials.client_id,
            "X-Installation-ID": credentials.installation_id,
            "User-Agent": "NEPEMCERT/1.0"
        }
    
    def is_authenticated(self) -> bool:
        """
        Verifica se o cliente está autenticado
        
        Returns:
            True se autenticado
        """
        credentials = self.get_credentials()
        if not credentials:
            return False
        
        # Verifica se credenciais não expiraram (opcional)
        if credentials.last_used:
            expire_time = credentials.last_used + timedelta(days=30)
            if datetime.now() > expire_time:
                return False
        
        return True
    
    def revoke_credentials(self) -> None:
        """Remove credenciais armazenadas"""
        try:
            # Remove do keyring
            keyring.delete_password(
                self.config.keyring_service,
                "client_key"
            )
        except Exception:
            pass
        
        # Remove arquivo de metadados
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        
        # Limpa credenciais em memória
        self._credentials = None
    
    def get_client_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtém informações do cliente para exibição
        
        Returns:
            Dicionário com informações do cliente
        """
        credentials = self.get_credentials()
        if not credentials:
            return None
        
        return {
            "client_id": credentials.client_id,
            "installation_id": credentials.installation_id,
            "created_at": credentials.created_at.strftime("%d/%m/%Y %H:%M"),
            "last_used": credentials.last_used.strftime("%d/%m/%Y %H:%M") if credentials.last_used else "Nunca",
            "is_authenticated": self.is_authenticated()
        }
    
    def update_config(self, **kwargs) -> None:
        """
        Atualiza configuração de autenticação
        
        Args:
            **kwargs: Parâmetros de configuração
        """
        config_dict = self.config.dict()
        config_dict.update(kwargs)
        
        self.config = AuthConfig(**config_dict)
        self._save_config(self.config)


# Instância global para facilitar uso
auth_manager = AuthManager()


def setup_authentication(force_regenerate: bool = False) -> ClientCredentials:
    """
    Função de conveniência para configurar autenticação
    
    Args:
        force_regenerate: Força regeneração das credenciais
        
    Returns:
        Credenciais do cliente
    """
    return auth_manager.setup_client(force_regenerate)


def get_auth_headers() -> Dict[str, str]:
    """
    Função de conveniência para obter headers de autenticação
    
    Returns:
        Headers de autenticação
    """
    return auth_manager.get_auth_headers()


def is_client_authenticated() -> bool:
    """
    Função de conveniência para verificar autenticação
    
    Returns:
        True se autenticado
    """
    return auth_manager.is_authenticated()
