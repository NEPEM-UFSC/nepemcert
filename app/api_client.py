"""
Cliente para a API Netlify/Firebase - certificados.nepemufsc.com

Este módulo fornece interface para interagir com a API do servidor
de certificados, incluindo:
- Criação de chaves de API
- Registro de certificados
- Consulta de certificados
- Gerenciamento de chaves
"""

import requests
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from .api_key_manager import APIKeyManager, APIKey


class APIClientError(Exception):
    """Exceção para erros da API"""
    pass


class CertificateAPIClient:
    """
    Cliente para interagir com a API de certificados
    
    Fornece métodos para criar chaves, registrar certificados e
    consultar dados no servidor certificados.nepemufsc.com
    """
    
    def __init__(self, dev_mode: bool = True, keys_dir: Optional[Path] = None):
        """
        Inicializa o cliente da API
        
        Args:
            dev_mode: Se True, usa servidor local (localhost:8888)
            keys_dir: Diretório de chaves (padrão: ./keys)
        """
        self.dev_mode = dev_mode
        
        if dev_mode:
            self.base_url = "http://localhost:8888/.netlify/functions"
        else:
            self.base_url = "https://certificados.nepemufsc.com/.netlify/functions"
        
        self.key_manager = APIKeyManager(keys_dir)
        self.timeout = 30
        self.retry_attempts = 3
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> Dict:
        """
        Faz uma requisição HTTP para a API
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API (sem barra inicial)
            data: Dados do corpo da requisição
            params: Parâmetros da query string
            headers: Headers customizados
        
        Returns:
            Resposta JSON da API
        
        Raises:
            APIClientError: Se requisição falhar
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Headers padrão
        default_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'NEPEMCERT/1.0'
        }
        
        if headers:
            default_headers.update(headers)
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=default_headers,
                    timeout=self.timeout
                )
                
                # Verificar se a resposta é bem-sucedida
                if response.status_code >= 200 and response.status_code < 300:
                    try:
                        return response.json()
                    except ValueError:
                        return {"success": True, "message": "Operação bem-sucedida"}
                
                # Tentar extrair mensagem de erro
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error', response.text)
                except:
                    error_msg = response.text
                
                raise APIClientError(
                    f"Erro HTTP {response.status_code}: {error_msg}"
                )
            
            except requests.Timeout:
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
                    continue
                raise APIClientError(f"Timeout após {self.retry_attempts} tentativas")
            
            except requests.RequestException as e:
                if attempt < self.retry_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise APIClientError(f"Erro na requisição: {str(e)}")
        
        raise APIClientError("Número máximo de tentativas excedido")
    
    # =========================================================================
    # OPERAÇÕES DE CHAVES DE API
    # =========================================================================
    
    def create_api_key(self, role: str, is_active: bool = True,
                      description: str = "", 
                      auth_key: Optional[APIKey] = None,
                      save_to_file: bool = True) -> Optional[APIKey]:
        """
        Cria uma nova chave de API no servidor
        
        Args:
            role: Role da chave (admin, issuer, reader)
            is_active: Se a chave está ativa
            description: Descrição da chave
            auth_key: Chave para autenticação (admin ou bootstrap)
            save_to_file: Se deve salvar automaticamente em arquivo
        
        Returns:
            APIKey criada ou None se falhar
        
        Raises:
            APIClientError: Se falhar na criação
        """
        # Validar role
        if role not in ["admin", "issuer", "reader"]:
            raise ValueError(f"Role inválido: {role}")
        
        # Obter chave de autenticação
        if not auth_key:
            # Tentar autoload de chave admin/issuer
            auth_key = self.key_manager.autoload_keys(['admin', 'issuer'])
            
            if not auth_key:
                # Usar chave master admin como fallback
                auth_key = self.key_manager.get_master_key('admin')
        
        if not auth_key:
            raise APIClientError("Nenhuma chave de autenticação disponível")
        
        # Preparar dados da requisição
        request_data = {
            "role": role,
            "isActive": is_active,
            "description": description or f"Chave {role} criada via NEPEMCERT"
        }
        
        # Obter headers com JWT
        headers = self.key_manager.get_auth_headers(auth_key)
        
        # Fazer requisição
        try:
            response = self._make_request(
                method="POST",
                endpoint="createKey",
                data=request_data,
                headers=headers
            )
            
            # Verificar se resposta contém chave
            if 'keyId' not in response or 'secret' not in response:
                raise APIClientError("Resposta inválida do servidor")
            
            # Criar objeto APIKey
            new_key = APIKey(
                key_id=response['keyId'],
                secret=response['secret'],
                role=response.get('role', role),
                description=description,
                is_active=is_active
            )
            
            # Salvar em arquivo se solicitado
            if save_to_file:
                self.key_manager.save_key_to_file(new_key)
            
            print(f"✅ Chave {role} criada com sucesso: {new_key.key_id}")
            return new_key
        
        except APIClientError as e:
            print(f"❌ Erro ao criar chave: {e}")
            raise
    
    # =========================================================================
    # OPERAÇÕES DE CERTIFICADOS
    # =========================================================================
    
    def create_certificate(self, certificate_data: Dict[str, Any],
                          auth_key: Optional[APIKey] = None) -> Optional[Dict]:
        """
        Cria (registra) um certificado no servidor
        
        Args:
            certificate_data: Dados do certificado contendo:
                - code (str): Código único do certificado
                - name (str): Nome do participante
                - event (str): Nome do evento
                - date (str, opcional): Data do evento
                - hours (str, opcional): Carga horária
                - description (str, opcional): Descrição adicional
            auth_key: Chave para autenticação (issuer ou admin)
        
        Returns:
            Dados do certificado criado ou None se falhar
        
        Raises:
            APIClientError: Se falhar na criação
        """
        # Validar campos obrigatórios
        required_fields = ['code', 'name', 'event']
        missing_fields = [f for f in required_fields if f not in certificate_data]
        
        if missing_fields:
            raise ValueError(f"Campos obrigatórios faltando: {', '.join(missing_fields)}")
        
        # Obter chave de autenticação
        if not auth_key:
            auth_key = self.key_manager.autoload_keys(['issuer', 'admin'])
        
        if not auth_key:
            raise APIClientError("Nenhuma chave issuer/admin disponível")
        
        # Validar que a chave tem permissão
        if auth_key.role not in ['issuer', 'admin']:
            raise APIClientError(f"Chave {auth_key.role} não tem permissão para criar certificados")
        
        # Obter headers com JWT
        headers = self.key_manager.get_auth_headers(auth_key)
        
        # Fazer requisição
        try:
            response = self._make_request(
                method="POST",
                endpoint="writeCertificate",
                data=certificate_data,
                headers=headers
            )
            
            return response
        
        except APIClientError as e:
            print(f"❌ Erro ao criar certificado {certificate_data.get('code')}: {e}")
            raise
    
    def create_certificates_batch(self, certificates: List[Dict[str, Any]],
                                  auth_key: Optional[APIKey] = None) -> Dict[str, Any]:
        """
        Cria múltiplos certificados em lote
        
        Args:
            certificates: Lista de dicionários com dados dos certificados
            auth_key: Chave para autenticação (issuer ou admin)
        
        Returns:
            Dicionário com estatísticas de criação
        """
        total = len(certificates)
        success = 0
        failed = 0
        errors = []
        
        print(f"\n📋 Iniciando registro de {total} certificados no servidor...")
        print("=" * 60)
        
        for i, cert_data in enumerate(certificates, 1):
            try:
                print(f"[{i}/{total}] Registrando: {cert_data.get('name', 'N/A')}", end="")
                
                result = self.create_certificate(cert_data, auth_key)
                
                if result:
                    success += 1
                    print(" ✅")
                else:
                    failed += 1
                    print(" ❌")
                    errors.append({
                        'certificate': cert_data.get('code'),
                        'error': 'Falha no registro'
                    })
            
            except Exception as e:
                failed += 1
                print(f" ❌ - {str(e)}")
                errors.append({
                    'certificate': cert_data.get('code'),
                    'error': str(e)
                })
        
        # Resumo
        print("\n" + "=" * 60)
        print("📊 RESUMO DO REGISTRO EM LOTE")
        print("=" * 60)
        print(f"Total: {total}")
        print(f"✅ Sucesso: {success}")
        print(f"❌ Falhas: {failed}")
        
        if errors:
            print(f"\n⚠️ Erros detectados:")
            for err in errors[:5]:  # Mostrar primeiros 5 erros
                print(f"  - {err['certificate']}: {err['error']}")
        
        return {
            'total': total,
            'success': success,
            'failed': failed,
            'errors': errors
        }
    
    def get_certificate(self, code: str) -> Optional[Dict]:
        """
        Busca um certificado pelo código (não requer autenticação)
        
        Args:
            code: Código do certificado
        
        Returns:
            Dados do certificado ou None se não encontrado
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="getCertificate",
                params={'code': code}
            )
            
            if response and response.get('found'):
                print(f"✅ Certificado encontrado: {code}")
                print(f"   Nome: {response.get('name')}")
                print(f"   Evento: {response.get('event')}")
                return response
            else:
                print(f"❌ Certificado não encontrado: {code}")
                return None
        
        except APIClientError as e:
            print(f"❌ Erro ao buscar certificado {code}: {e}")
            return None
    
    # =========================================================================
    # UTILITÁRIOS
    # =========================================================================
    
    def test_connection(self) -> bool:
        """
        Testa conexão com o servidor
        
        Returns:
            True se conectado
        """
        try:
            # Fazer health check no endpoint dedicado
            self._make_request(
                method="GET",
                endpoint="health"
            )
            return True
        except:
            return False
    
    def setup_initial_keys(self) -> Dict[str, Optional[APIKey]]:
        """
        Configura chaves iniciais (issuer e reader) usando chave master
        
        Returns:
            Dicionário com as chaves criadas
        """
        print("\n🔑 Configurando chaves iniciais do NEPEMCERT...")
        print("=" * 60)
        
        master_key = self.key_manager.get_master_key('admin')
        
        results = {
            'issuer': None,
            'reader': None
        }
        
        # Criar chave issuer
        try:
            print("\n1. Criando chave ISSUER...")
            issuer_key = self.create_api_key(
                role="issuer",
                is_active=True,
                description="Chave de escrita para NEPEMCERT",
                auth_key=master_key,
                save_to_file=True
            )
            results['issuer'] = issuer_key
        except Exception as e:
            print(f"❌ Erro ao criar chave issuer: {e}")
        
        # Criar chave reader
        try:
            print("\n2. Criando chave READER...")
            reader_key = self.create_api_key(
                role="reader",
                is_active=True,
                description="Chave de leitura para NEPEMCERT",
                auth_key=master_key,
                save_to_file=True
            )
            results['reader'] = reader_key
        except Exception as e:
            print(f"❌ Erro ao criar chave reader: {e}")
        
        print("\n" + "=" * 60)
        print("✅ Configuração inicial concluída!")
        
        return results


# Instância global para facilitar uso
certificate_api_client = CertificateAPIClient()


def create_certificate(certificate_data: Dict[str, Any]) -> Optional[Dict]:
    """
    Função de conveniência para criar certificado
    
    Args:
        certificate_data: Dados do certificado
    
    Returns:
        Resposta da API
    """
    return certificate_api_client.create_certificate(certificate_data)


def get_certificate(code: str) -> Optional[Dict]:
    """
    Função de conveniência para buscar certificado
    
    Args:
        code: Código do certificado
    
    Returns:
        Dados do certificado
    """
    return certificate_api_client.get_certificate(code)
