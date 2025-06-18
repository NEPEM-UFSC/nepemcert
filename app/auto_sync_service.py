#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serviço de sincronização automática para códigos de autenticação.
Monitora a conectividade e sincroniza automaticamente quando possível.
"""

import time
import threading
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .offline_sync_manager import OfflineSyncManager, SyncStatus, CertificateRecord
from .connectivity_manager import ConnectivityManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncPriority(Enum):
    """Prioridades de sincronização."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


@dataclass
class SyncTask:
    """Representa uma tarefa de sincronização."""
    certificate_record: CertificateRecord
    priority: SyncPriority
    created_at: datetime
    attempts: int = 0
    
    def __lt__(self, other):
        """Comparação para fila de prioridade."""
        return (self.priority.value, self.created_at) < (other.priority.value, other.created_at)


class AutoSyncService:
    """
    Serviço de sincronização automática que roda em background.
    
    Características:
    - Monitoramento contínuo de conectividade
    - Sincronização automática quando conectado
    - Retry com backoff exponencial
    - Rate limiting para não sobrecarregar o servidor
    - Callback hooks para notificações
    """
    
    def __init__(self, 
                 server_url: str = "https://nepemufsc.com/api",
                 check_interval: int = 30,
                 batch_size: int = 10,
                 max_concurrent: int = 3):
        """
        Inicializa o serviço de sincronização automática.
        
        Args:
            server_url (str): URL base da API do servidor.
            check_interval (int): Intervalo de verificação em segundos.
            batch_size (int): Tamanho do lote para sincronização.
            max_concurrent (int): Máximo de threads simultâneas.
        """
        self.server_url = server_url.rstrip('/')
        self.check_interval = check_interval
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        
        # Managers
        self.offline_manager = OfflineSyncManager()
        self.connectivity_manager = ConnectivityManager()
        
        # Estado do serviço
        self._running = False
        self._connected = False
        self._last_connectivity_check = None
        self._sync_thread = None
        self._stop_event = threading.Event()
        
        # Rate limiting
        self._last_sync_time = None
        self.min_sync_interval = 5  # segundos entre sincronizações
        
        # Callbacks
        self._on_sync_success: List[Callable] = []
        self._on_sync_error: List[Callable] = []
        self._on_connectivity_change: List[Callable] = []
        
        # Estatísticas
        self.stats = {
            'total_synced': 0,
            'total_failed': 0,
            'last_sync_time': None,
            'service_start_time': None,
            'connectivity_checks': 0
        }
        
        logger.info("AutoSyncService inicializado")
    
    def add_callback(self, event: str, callback: Callable):
        """
        Adiciona callback para eventos do serviço.
        
        Args:
            event (str): Tipo do evento ('sync_success', 'sync_error', 'connectivity_change').
            callback (Callable): Função a ser chamada.
        """
        callback_map = {
            'sync_success': self._on_sync_success,
            'sync_error': self._on_sync_error,
            'connectivity_change': self._on_connectivity_change
        }
        
        if event in callback_map:
            callback_map[event].append(callback)
            logger.info(f"Callback adicionado para evento: {event}")
        else:
            logger.warning(f"Evento desconhecido: {event}")
    
    def start(self):
        """Inicia o serviço de sincronização automática."""
        if self._running:
            logger.warning("Serviço já está rodando")
            return
        
        self._running = True
        self._stop_event.clear()
        self.stats['service_start_time'] = datetime.now()
        
        # Iniciar thread principal
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        
        logger.info("AutoSyncService iniciado")
    
    def stop(self):
        """Para o serviço de sincronização automática."""
        if not self._running:
            return
        
        self._running = False
        self._stop_event.set()
        
        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=10)
        
        logger.info("AutoSyncService parado")
    
    def _sync_loop(self):
        """Loop principal de sincronização."""
        logger.info("Loop de sincronização iniciado")
        
        while self._running and not self._stop_event.is_set():
            try:
                # Verificar conectividade
                self._check_connectivity()
                
                # Sincronizar se conectado e se há dados pendentes
                if self._connected and self._should_sync():
                    self._perform_sync_batch()
                
                # Aguardar próximo ciclo
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de sincronização: {e}")
                self._stop_event.wait(5)  # Aguardar um pouco antes de tentar novamente
        
        logger.info("Loop de sincronização finalizado")
    
    def _check_connectivity(self):
        """Verifica conectividade com o servidor."""
        try:
            # Não verificar conectividade muito frequentemente
            now = datetime.now()
            if (self._last_connectivity_check and 
                now - self._last_connectivity_check < timedelta(seconds=self.check_interval)):
                return
            
            self._last_connectivity_check = now
            self.stats['connectivity_checks'] += 1
            
            # Usar o connectivity manager
            result = self.connectivity_manager.check_connection()
            new_connected = result['status'] == 'Conectado'
            
            # Detectar mudança de conectividade
            if new_connected != self._connected:
                old_status = "conectado" if self._connected else "desconectado"
                new_status = "conectado" if new_connected else "desconectado"
                
                logger.info(f"Conectividade mudou: {old_status} → {new_status}")
                
                # Chamar callbacks de mudança de conectividade
                for callback in self._on_connectivity_change:
                    try:
                        callback(self._connected, new_connected)
                    except Exception as e:
                        logger.error(f"Erro em callback de conectividade: {e}")
                
                self._connected = new_connected
            
        except Exception as e:
            logger.error(f"Erro ao verificar conectividade: {e}")
            self._connected = False
    
    def _should_sync(self) -> bool:
        """Verifica se deve executar sincronização."""
        # Verificar rate limiting
        if self._last_sync_time:
            time_since_last = (datetime.now() - self._last_sync_time).total_seconds()
            if time_since_last < self.min_sync_interval:
                return False
        
        # Verificar se há dados pendentes
        pending_count = len(self.offline_manager.get_pending_certificates(limit=1))
        return pending_count > 0
    
    def _perform_sync_batch(self):
        """Executa sincronização de um lote de certificados."""
        try:
            self._last_sync_time = datetime.now()
            
            # Obter certificados pendentes
            pending_certs = self.offline_manager.get_pending_certificates(limit=self.batch_size)
            
            if not pending_certs:
                logger.debug("Nenhum certificado pendente para sincronização")
                return
            
            logger.info(f"Iniciando sincronização de {len(pending_certs)} certificados")
            
            success_count = 0
            error_count = 0
            
            for cert in pending_certs:
                try:
                    # Marcar como "sincronizando"
                    self.offline_manager.update_sync_status(
                        cert.codigo_autenticacao, 
                        SyncStatus.SYNCING
                    )
                    
                    # Tentar sincronizar
                    if self._sync_single_certificate(cert):
                        # Sucesso
                        self.offline_manager.update_sync_status(
                            cert.codigo_autenticacao,
                            SyncStatus.SYNCED
                        )
                        success_count += 1
                        self.stats['total_synced'] += 1
                        
                        # Callback de sucesso
                        for callback in self._on_sync_success:
                            try:
                                callback(cert)
                            except Exception as e:
                                logger.error(f"Erro em callback de sucesso: {e}")
                    
                    else:
                        # Falha
                        error_count += 1
                        self.stats['total_failed'] += 1
                        
                        # Determinar próximo status baseado no número de tentativas
                        if cert.sync_attempts >= self.offline_manager.max_retry_attempts:
                            status = SyncStatus.FAILED
                            error_msg = "Máximo de tentativas excedido"
                        else:
                            status = SyncStatus.RETRY
                            error_msg = "Falha temporária, tentativa será repetida"
                        
                        self.offline_manager.update_sync_status(
                            cert.codigo_autenticacao,
                            status,
                            error_msg
                        )
                        
                        # Callback de erro
                        for callback in self._on_sync_error:
                            try:
                                callback(cert, error_msg)
                            except Exception as e:
                                logger.error(f"Erro em callback de erro: {e}")
                
                except Exception as e:
                    logger.error(f"Erro ao sincronizar certificado {cert.codigo_autenticacao}: {e}")
                    error_count += 1
            
            self.stats['last_sync_time'] = datetime.now()
            
            if success_count > 0 or error_count > 0:
                logger.info(f"Sincronização concluída: {success_count} sucessos, {error_count} erros")
            
        except Exception as e:
            logger.error(f"Erro na sincronização em lote: {e}")
    
    def _sync_single_certificate(self, cert: CertificateRecord) -> bool:
        """
        Sincroniza um único certificado com o servidor.
        
        Args:
            cert (CertificateRecord): Certificado a ser sincronizado.
            
        Returns:
            bool: True se sincronizado com sucesso.
        """
        try:
            # Preparar dados para o servidor
            sync_data = {
                'codigo_autenticacao': cert.codigo_autenticacao,
                'nome_participante': cert.nome_participante,
                'evento': cert.evento,
                'data_evento': cert.data_evento,
                'local_evento': cert.local_evento,
                'carga_horaria': cert.carga_horaria,
                'coordenador': cert.coordenador,
                'diretor': cert.diretor,
                'data_geracao': cert.data_geracao,
                'url_verificacao': cert.url_verificacao,
                'template_usado': cert.template_usado,
                'tema_usado': cert.tema_usado,
                'checksum': cert.checksum
            }
            
            # Fazer requisição para o servidor
            url = f"{self.server_url}/certificates/register"
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'NEPEMCERT-AutoSync/1.0'
            }
            
            response = requests.post(
                url,
                json=sync_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.debug(f"Certificado {cert.codigo_autenticacao} sincronizado com sucesso")
                return True
            elif response.status_code == 409:
                # Conflito - certificado já existe no servidor
                logger.info(f"Certificado {cert.codigo_autenticacao} já existe no servidor")
                return True  # Considerar como sucesso
            else:
                logger.warning(f"Falha na sincronização - Status: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Erro de rede na sincronização: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado na sincronização: {e}")
            return False
    
    def force_sync(self) -> Dict[str, int]:
        """
        Força uma sincronização imediata de todos os certificados pendentes.
        
        Returns:
            Dict[str, int]: Resultado da sincronização.
        """
        logger.info("Forçando sincronização imediata")
        
        if not self._connected:
            logger.warning("Não é possível sincronizar - sem conectividade")
            return {'success': 0, 'failed': 0, 'error': 'No connectivity'}
        
        # Resetar rate limiting temporariamente
        original_interval = self.min_sync_interval
        self.min_sync_interval = 0
        
        try:
            # Executar sincronização em lotes até acabar
            total_success = 0
            total_failed = 0
            
            while True:
                pending_certs = self.offline_manager.get_pending_certificates(limit=self.batch_size)
                if not pending_certs:
                    break
                
                # Simular _perform_sync_batch mas de forma síncrona
                for cert in pending_certs:
                    if self._sync_single_certificate(cert):
                        self.offline_manager.update_sync_status(
                            cert.codigo_autenticacao,
                            SyncStatus.SYNCED
                        )
                        total_success += 1
                    else:
                        self.offline_manager.update_sync_status(
                            cert.codigo_autenticacao,
                            SyncStatus.RETRY,
                            "Falha na sincronização forçada"
                        )
                        total_failed += 1
            
            logger.info(f"Sincronização forçada concluída: {total_success} sucessos, {total_failed} falhas")
            
            return {
                'success': total_success,
                'failed': total_failed
            }
            
        finally:
            # Restaurar rate limiting
            self.min_sync_interval = original_interval
    
    def get_service_status(self) -> Dict[str, any]:
        """
        Obtém o status atual do serviço.
        
        Returns:
            Dict[str, any]: Status detalhado do serviço.
        """
        uptime = None
        if self.stats['service_start_time']:
            uptime = (datetime.now() - self.stats['service_start_time']).total_seconds()
        
        return {
            'running': self._running,
            'connected': self._connected,
            'last_connectivity_check': self._last_connectivity_check.isoformat() if self._last_connectivity_check else None,
            'last_sync_time': self.stats['last_sync_time'].isoformat() if self.stats['last_sync_time'] else None,
            'uptime_seconds': uptime,
            'stats': self.stats.copy(),
            'pending_certificates': len(self.offline_manager.get_pending_certificates(limit=1000)),
            'server_url': self.server_url,
            'config': {
                'check_interval': self.check_interval,
                'batch_size': self.batch_size,
                'max_concurrent': self.max_concurrent,
                'min_sync_interval': self.min_sync_interval
            }
        }
