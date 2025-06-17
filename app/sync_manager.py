import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class SyncManager:
    """
    Gerenciador de sincronização offline para certificados.
    
    Responsável por:
    - Sincronizar certificados criados pelo cert_auth_manager
    - Processar fila quando conexão for restaurada
    - Verificar certificados pendentes de sincronização
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador de sincronização.
        
        Args:
            db_path: Caminho para o banco SQLite. Se None, usa certs.db padrão.
        """
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "certs.db"
        
        self.db_path = str(db_path)
        self.logger = logging.getLogger(__name__)
    
    def check_pending_certificates(self) -> Dict[str, Any]:
        """
        Verifica se existem certificados pendentes de sincronização.
        
        Returns:
            Dict: Informações sobre certificados pendentes
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Contar certificados não sincronizados
                cursor = conn.execute("SELECT COUNT(*) as total FROM certificates WHERE sincronizado = 0")
                total_pending = cursor.fetchone()[0]
                
                # Contar certificados com muitas tentativas
                cursor = conn.execute("""
                    SELECT COUNT(*) as high_attempts 
                    FROM certificates 
                    WHERE sincronizado = 0 AND tentativas_sync >= 3
                """)
                high_attempts = cursor.fetchone()[0]
                
                # Certificado mais antigo não sincronizado
                cursor = conn.execute("""
                    SELECT data_geracao 
                    FROM certificates 
                    WHERE sincronizado = 0 
                    ORDER BY data_geracao ASC 
                    LIMIT 1
                """)
                oldest_row = cursor.fetchone()
                oldest = oldest_row[0] if oldest_row else None
                
                return {
                    'has_pending': total_pending > 0,
                    'total_pending': total_pending,
                    'high_attempts': high_attempts,
                    'oldest_pending': oldest,
                    'needs_sync': total_pending > 0
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar certificados pendentes: {e}")
            return {
                'has_pending': False,
                'total_pending': 0,
                'high_attempts': 0,
                'oldest_pending': None,
                'needs_sync': False,
                'error': str(e)
            }
    
    def get_pending_certificates(self, limit: Optional[int] = None, max_attempts: int = 5) -> List[Dict[str, Any]]:
        """
        Obtém certificados pendentes de sincronização.
        
        Args:
            limit: Número máximo de certificados a retornar
            max_attempts: Máximo de tentativas para incluir na lista
            
        Returns:
            List[Dict]: Lista de certificados pendentes
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                    SELECT * FROM certificates 
                    WHERE sincronizado = 0 AND tentativas_sync < ?
                    ORDER BY data_geracao ASC
                """
                
                params = [max_attempts]
                
                if limit:
                    query += " LIMIT ?"
                    params.append(limit)
                
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Erro ao obter certificados pendentes: {e}")
            return []
    
    def process_synchronization(self, api_client=None, max_attempts: int = 5) -> Dict[str, int]:
        """
        Processa a sincronização de certificados pendentes.
        
        Args:
            api_client: Cliente da API para envio dos certificados
            max_attempts: Número máximo de tentativas por certificado
            
        Returns:
            Dict: Estatísticas do processamento (success, failed, skipped)
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
        if not api_client:
            self.logger.warning("Cliente da API não fornecido para processamento")
            return stats
        
        # Importar cert_auth_manager para usar os mesmos métodos
        try:
            from .cert_auth_manager import CertAuthenticationManager
            cert_auth = CertAuthenticationManager()
        except ImportError:
            self.logger.error("Não foi possível importar CertAuthenticationManager")
            return stats
        
        # Obter certificados pendentes
        pending_certificates = self.get_pending_certificates(max_attempts=max_attempts)
        
        for cert in pending_certificates:
            codigo = cert['codigo_autenticacao']
            tentativas = cert['tentativas_sync']
            
            # Pular certificados que excederam tentativas
            if tentativas >= max_attempts:
                self.logger.warning(f"Certificado {codigo} excedeu máximo de tentativas")
                stats['skipped'] += 1
                continue
            
            try:
                # Preparar dados para envio
                certificate_data = {
                    'codigo_autenticacao': cert['codigo_autenticacao'],
                    'nome_participante': cert['nome_participante'],
                    'evento': cert['evento'],
                    'data_evento': cert['data_evento'],
                    'local_evento': cert['local_evento'],
                    'carga_horaria': cert['carga_horaria'],
                    'data_geracao': cert['data_geracao'],
                    'url_verificacao': cert['url_verificacao']
                }
                
                # Tentar sincronizar via API
                success = api_client.send_certificate(certificate_data)
                
                if success:
                    # Marcar como sincronizado
                    if cert_auth.mark_as_synchronized(codigo):
                        stats['success'] += 1
                        self.logger.info(f"Certificado sincronizado: {cert['nome_participante']}")
                    else:
                        stats['failed'] += 1
                        self.logger.error(f"Erro ao marcar certificado como sincronizado: {codigo}")
                else:
                    # Atualizar tentativa em caso de falha
                    cert_auth.update_sync_attempt(codigo, "Falha no envio via API")
                    stats['failed'] += 1
                    self.logger.warning(f"Falha ao sincronizar certificado: {codigo}")
                    
            except Exception as e:
                error_msg = f"Erro no processamento: {str(e)}"
                cert_auth.update_sync_attempt(codigo, error_msg)
                stats['failed'] += 1
                self.logger.error(f"Erro ao processar certificado {codigo}: {e}")
        
        # Fechar conexão do cert_auth
        cert_auth.close_connection()
        
        self.logger.info(f"Processamento de sincronização concluído: {stats}")
        return stats
    
    def sync_all_pending(self, api_client=None) -> Dict[str, Any]:
        """
        Sincroniza todos os certificados pendentes em uma operação.
        
        Args:
            api_client: Cliente da API para envio
            
        Returns:
            Dict: Resultado completo da sincronização
        """
        self.logger.info("Iniciando sincronização de todos os certificados pendentes")
        
        # Verificar status inicial
        initial_status = self.check_pending_certificates()
        
        if not initial_status['has_pending']:
            self.logger.info("Nenhum certificado pendente de sincronização")
            return {
                'initial_pending': 0,
                'final_pending': 0,
                'stats': {'success': 0, 'failed': 0, 'skipped': 0},
                'success': True
            }
        
        # Processar sincronização
        stats = self.process_synchronization(api_client)
        
        # Verificar status final
        final_status = self.check_pending_certificates()
        
        result = {
            'initial_pending': initial_status['total_pending'],
            'final_pending': final_status['total_pending'],
            'stats': stats,
            'success': stats['success'] > 0 or initial_status['total_pending'] == 0
        }
        
        self.logger.info(f"Sincronização concluída: {result}")
        return result
    
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Obtém status completo da sincronização.
        
        Returns:
            Dict: Status detalhado da sincronização
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Total de certificados
                cursor = conn.execute("SELECT COUNT(*) as total FROM certificates")
                total = cursor.fetchone()[0]
                
                # Certificados sincronizados
                cursor = conn.execute("SELECT COUNT(*) as synchronized FROM certificates WHERE sincronizado = 1")
                synchronized = cursor.fetchone()[0]
                
                # Certificados pendentes
                cursor = conn.execute("SELECT COUNT(*) as pending FROM certificates WHERE sincronizado = 0")
                pending = cursor.fetchone()[0]
                
                # Certificados com muitas tentativas
                cursor = conn.execute("""
                    SELECT COUNT(*) as high_attempts 
                    FROM certificates 
                    WHERE sincronizado = 0 AND tentativas_sync >= 3
                """)
                high_attempts = cursor.fetchone()[0]
                
                return {
                    'total_certificates': total,
                    'synchronized': synchronized,
                    'pending': pending,
                    'high_attempts': high_attempts,
                    'sync_rate': (synchronized / total * 100) if total > 0 else 100,
                    'db_path': self.db_path
                }
                
        except Exception as e:
            self.logger.error(f"Erro ao obter status de sincronização: {e}")
            return {'error': str(e)}
    
    def reset_failed_attempts(self, max_attempts: int = 3) -> int:
        """
        Reseta tentativas de certificados que falharam múltiplas vezes.
        
        Args:
            max_attempts: Número mínimo de tentativas para considerar reset
            
        Returns:
            int: Número de certificados resetados
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE certificates 
                    SET tentativas_sync = 0, ultimo_erro_sync = NULL
                    WHERE sincronizado = 0 AND tentativas_sync >= ?
                """, (max_attempts,))
                conn.commit()
                
                reset_count = cursor.rowcount
                self.logger.info(f"Resetadas tentativas de {reset_count} certificados")
                return reset_count
                
        except Exception as e:
            self.logger.error(f"Erro ao resetar tentativas: {e}")
            return 0