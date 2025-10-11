"""
Gerenciador de Chaves de API do NEPEMCERT

Este módulo gerencia as chaves de API para autenticação com o servidor
certificados.nepemufsc.com, incluindo:
- Criação de chaves (admin, issuer, reader)
- Armazenamento seguro de chaves em arquivos .key
- Carregamento automático de chaves (autoload)
- Geração de tokens JWT para autenticação
"""

import jwt
import time
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import secrets


class APIKey:
    """Representa uma chave de API"""
    
    def __init__(self, key_id: str, secret: str, role: str, description: str = "", 
                 is_active: bool = True, created_at: Optional[str] = None):
        self.key_id = key_id
        self.secret = secret
        self.role = role
        self.description = description
        self.is_active = is_active
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte a chave para dicionário"""
        return {
            "keyId": self.key_id,
            "secret": self.secret,
            "role": self.role,
            "description": self.description,
            "isActive": self.is_active,
            "createdAt": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'APIKey':
        """Cria uma chave a partir de um dicionário"""
        return cls(
            key_id=data.get("keyId", ""),
            secret=data.get("secret", ""),
            role=data.get("role", ""),
            description=data.get("description", ""),
            is_active=data.get("isActive", True),
            created_at=data.get("createdAt")
        )


class APIKeyManager:
    """
    Gerenciador de chaves de API
    
    Responsável por criar, salvar, carregar e gerenciar chaves de API
    para autenticação com o servidor certificados.nepemufsc.com
    """
    
    # Chaves master para bootstrap (hardcoded conforme exemplo)
    MASTER_KEYS = {
        "admin": {
            "keyId": "masterkey",
            "secret": "1JyBzZOKMnLGLnfpPl3g8jb9iYu3t1ryDgcZnG4lgYJoVyBk",
            "role": "admin"
        },
        "bootstrap": {
            "keyId": "nepemcert-bootstrap",
            "secret": "nepemcert-bootstrap-secret",
            "role": "bootstrap"
        }
    }
    
    VALID_ROLES = ["admin", "issuer", "reader", "bootstrap"]
    
    def __init__(self, keys_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de chaves
        
        Args:
            keys_dir: Diretório para armazenar chaves (padrão: ./keys)
        """
        self.keys_dir = keys_dir or Path.cwd() / "keys"
        self.keys_dir.mkdir(exist_ok=True)
        
        self._loaded_keys: Dict[str, APIKey] = {}
        self._active_key: Optional[APIKey] = None
    
    def save_key_to_file(self, key: APIKey, directory: Optional[Path] = None) -> Path:
        """
        Salva uma chave em um arquivo .key
        
        Args:
            key: Chave a ser salva
            directory: Diretório onde salvar (padrão: self.keys_dir)
        
        Returns:
            Path do arquivo salvo
        """
        save_dir = directory or self.keys_dir
        save_dir = Path(save_dir)
        save_dir.mkdir(exist_ok=True)
        
        # Nome do arquivo baseado no role e timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{key.role}_{key.key_id}_{timestamp}.key"
        file_path = save_dir / filename
        
        # Salvar como JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(key.to_dict(), f, indent=2)
        
        print(f"✅ Chave salva em: {file_path}")
        return file_path
    
    def load_key_from_file(self, file_path: Path) -> Optional[APIKey]:
        """
        Carrega uma chave de um arquivo .key
        
        Args:
            file_path: Caminho do arquivo .key
        
        Returns:
            APIKey ou None se falhar
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            key = APIKey.from_dict(data)
            
            # Validar role
            if key.role not in self.VALID_ROLES:
                print(f"⚠️ Role inválido no arquivo {file_path}: {key.role}")
                return None
            
            return key
        
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {file_path}")
            return None
        except json.JSONDecodeError:
            print(f"❌ Erro ao decodificar JSON do arquivo: {file_path}")
            return None
        except Exception as e:
            print(f"❌ Erro ao carregar chave de {file_path}: {e}")
            return None
    
    def autoload_keys(self, priority_roles: Optional[List[str]] = None) -> Optional[APIKey]:
        """
        Carrega automaticamente chaves do diretório keys/
        
        Args:
            priority_roles: Lista de roles em ordem de prioridade
                           (padrão: ['issuer', 'admin', 'reader'])
        
        Returns:
            Primeira chave encontrada conforme prioridade ou None
        """
        if not self.keys_dir.exists():
            print(f"⚠️ Diretório de chaves não encontrado: {self.keys_dir}")
            return None
        
        priority_roles = priority_roles or ['issuer', 'admin', 'reader']
        
        # Buscar arquivos .key
        key_files = list(self.keys_dir.glob("*.key"))
        
        if not key_files:
            print(f"⚠️ Nenhum arquivo .key encontrado em {self.keys_dir}")
            return None
        
        # Carregar todas as chaves
        self._loaded_keys = {}
        for key_file in key_files:
            key = self.load_key_from_file(key_file)
            if key and key.is_active:
                self._loaded_keys[key.key_id] = key
        
        if not self._loaded_keys:
            print("⚠️ Nenhuma chave ativa encontrada")
            return None
        
        # Selecionar chave por prioridade de role
        for role in priority_roles:
            for key in self._loaded_keys.values():
                if key.role == role:
                    self._active_key = key
                    print(f"✅ Chave {role} carregada: {key.key_id}")
                    return key
        
        # Se não encontrou por prioridade, retorna a primeira
        first_key = list(self._loaded_keys.values())[0]
        self._active_key = first_key
        print(f"✅ Chave carregada: {first_key.key_id} ({first_key.role})")
        return first_key
    
    def generate_jwt_token(self, key: Optional[APIKey] = None, 
                          expiry_hours: int = 1) -> str:
        """
        Gera um token JWT para autenticação
        
        Args:
            key: Chave a ser usada (padrão: chave ativa)
            expiry_hours: Tempo de expiração em horas
        
        Returns:
            Token JWT assinado
        
        Raises:
            ValueError: Se nenhuma chave disponível
        """
        key = key or self._active_key
        
        if not key:
            raise ValueError("Nenhuma chave disponível para gerar token")
        
        payload = {
            'keyId': key.key_id,
            'exp': int(time.time()) + (expiry_hours * 3600),
            'iat': int(time.time())
        }
        
        return jwt.encode(payload, key.secret, algorithm='HS256')
    
    def get_active_key(self) -> Optional[APIKey]:
        """Retorna a chave ativa atual"""
        return self._active_key
    
    def set_active_key(self, key_id: str) -> bool:
        """
        Define uma chave carregada como ativa
        
        Args:
            key_id: ID da chave a ser ativada
        
        Returns:
            True se sucesso
        """
        if key_id in self._loaded_keys:
            self._active_key = self._loaded_keys[key_id]
            print(f"✅ Chave ativa alterada para: {key_id}")
            return True
        
        print(f"❌ Chave não encontrada: {key_id}")
        return False
    
    def list_loaded_keys(self) -> List[Dict[str, Any]]:
        """
        Lista todas as chaves carregadas
        
        Returns:
            Lista de dicionários com informações das chaves
        """
        return [
            {
                "keyId": key.key_id,
                "role": key.role,
                "description": key.description,
                "isActive": key.is_active,
                "createdAt": key.created_at,
                "isCurrent": key == self._active_key
            }
            for key in self._loaded_keys.values()
        ]
    
    def get_master_key(self, role: str = "admin") -> Optional[APIKey]:
        """
        Retorna uma chave master (admin ou bootstrap)
        
        Args:
            role: 'admin' ou 'bootstrap'
        
        Returns:
            APIKey master ou None
        """
        if role not in ["admin", "bootstrap"]:
            return None
        
        master_data = self.MASTER_KEYS[role]
        return APIKey(
            key_id=master_data["keyId"],
            secret=master_data["secret"],
            role=master_data["role"],
            description=f"Master {role} key",
            is_active=True
        )
    
    def create_key_data(self, role: str, is_active: bool = True, 
                       description: str = "") -> Dict[str, Any]:
        """
        Cria os dados para requisição de criação de chave
        
        Args:
            role: Role da chave (admin, issuer, reader)
            is_active: Se a chave está ativa
            description: Descrição da chave
        
        Returns:
            Dicionário com dados da requisição
        """
        if role not in ["admin", "issuer", "reader"]:
            raise ValueError(f"Role inválido: {role}. Use: admin, issuer, reader")
        
        return {
            "role": role,
            "isActive": is_active,
            "description": description or f"Chave {role} criada via NEPEMCERT"
        }
    
    def get_auth_headers(self, key: Optional[APIKey] = None) -> Dict[str, str]:
        """
        Obtém headers de autenticação para requisições
        
        Args:
            key: Chave a ser usada (padrão: chave ativa)
        
        Returns:
            Dicionário com headers
        """
        token = self.generate_jwt_token(key)
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }


# Instância global para facilitar uso
api_key_manager = APIKeyManager()


def autoload_api_key() -> Optional[APIKey]:
    """
    Função de conveniência para autoload de chave
    
    Returns:
        Chave carregada ou None
    """
    return api_key_manager.autoload_keys()


def get_auth_headers() -> Dict[str, str]:
    """
    Função de conveniência para obter headers de autenticação
    
    Returns:
        Headers de autenticação
    """
    return api_key_manager.get_auth_headers()
