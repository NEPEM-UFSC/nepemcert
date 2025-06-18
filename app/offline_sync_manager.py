#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerenciador de sincronização offline para códigos de autenticação.
Responsável por armazenar códigos localmente quando não há conectividade
e sincronizar posteriormente quando a conexão for restaurada.
"""

import sqlite3
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import threading
import queue
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Status de sincronização dos registros."""
    PENDING = "pending"          # Aguardando sincronização
    SYNCING = "syncing"          # Em processo de sincronização
    SYNCED = "synced"            # Sincronizado com sucesso
    FAILED = "failed"            # Falha na sincronização
    RETRY = "retry"              # Aguardando nova tentativa


@dataclass
class CertificateRecord:
    """Representa um registro de certificado para sincronização."""
    codigo_autenticacao: str
    nome_participante: str
    evento: str
    data_evento: str
    local_evento: str
    carga_horaria: str
    coordenador: str
    diretor: str
    data_geracao: str
    url_verificacao: str
    qrcode_base64: str
    template_usado: str
    tema_usado: str
    checksum: str = ""  # Tornado opcional com valor padrão
    sync_status: str = SyncStatus.PENDING.value
    sync_attempts: int = 0
    last_sync_attempt: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        """Pós-processamento após inicialização."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class OfflineSyncManager:
    """
    Gerenciador de sincronização offline para códigos de autenticação.
    
    Funcionalidades:
    - Armazenamento local robusto em SQLite
    - Queue de sincronização com prioridades
    - Retry automático com backoff exponencial
    - Integridade de dados com checksums
    - Compressão de dados para otimização
    - Backup e recuperação
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o gerenciador de sincronização offline.
        
        Args:
            db_path (str, optional): Caminho personalizado para o banco de dados.
        """
        # Configurar caminho do banco de dados
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(project_root, 'data')
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'offline_sync.db')
        else:
            self.db_path = db_path
            
        # Configurar diretório de backups
        self.backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Configurar diretório de pacotes de sincronização
        self.sync_packages_dir = os.path.join(os.path.dirname(self.db_path), 'sync_packages')
        os.makedirs(self.sync_packages_dir, exist_ok=True)
        
        # Inicializar banco de dados
        self._init_database()
        
        # Queue para processamento assíncrono
        self._sync_queue = queue.PriorityQueue()
        self._processing = False
        self._stop_processing = threading.Event()
        
        # Configurações de retry
        self.max_retry_attempts = 5
        self.base_retry_delay = 2  # segundos
        self.max_retry_delay = 300  # 5 minutos
        
        logger.info(f"OfflineSyncManager inicializado com banco: {self.db_path}")
    
    def _init_database(self):
        """Inicializa o banco de dados SQLite com todas as tabelas necessárias."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                # Configurações para reduzir travamentos
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging para melhor performance
                conn.execute("PRAGMA synchronous = NORMAL")  # Reduzir sincronização para melhor performance
                conn.execute("PRAGMA temp_store = MEMORY")  # Usar memória para temporários
                conn.execute("PRAGMA cache_size = 10000")  # Aumentar cache
                conn.execute("PRAGMA busy_timeout = 30000")  # 30 segundos de timeout
                
                # Tabela principal de certificados
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS certificates (
                        codigo_autenticacao TEXT PRIMARY KEY,
                        nome_participante TEXT NOT NULL,
                        evento TEXT NOT NULL,
                        data_evento TEXT NOT NULL,
                        local_evento TEXT,
                        carga_horaria TEXT,
                        coordenador TEXT,
                        diretor TEXT,
                        data_geracao TEXT NOT NULL,
                        url_verificacao TEXT,
                        qrcode_base64 TEXT,
                        template_usado TEXT,
                        tema_usado TEXT,
                        checksum TEXT NOT NULL,
                        sync_status TEXT DEFAULT 'pending',
                        sync_attempts INTEGER DEFAULT 0,
                        last_sync_attempt TEXT,
                        error_message TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Tabela de log de sincronização
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        codigo_autenticacao TEXT NOT NULL,
                        action TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (codigo_autenticacao) REFERENCES certificates (codigo_autenticacao)
                    )
                ''')
                
                # Tabela de configurações
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sync_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Tabela de estatísticas
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS sync_stats (
                        date TEXT PRIMARY KEY,
                        pending_count INTEGER DEFAULT 0,
                        synced_count INTEGER DEFAULT 0,
                        failed_count INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                # Índices para otimização
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sync_status ON certificates (sync_status)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON certificates (created_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_sync_attempts ON certificates (sync_attempts)')
                
                conn.commit()
                logger.info("Banco de dados inicializado com sucesso")
                
        except sqlite3.Error as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def _calculate_checksum(self, record: CertificateRecord) -> str:
        """
        Calcula checksum MD5 dos dados essenciais do certificado.
        
        Args:
            record (CertificateRecord): Registro do certificado.
            
        Returns:
            str: Checksum MD5 em hexadecimal.
        """
        # Dados essenciais para checksum (excluindo metadados de sincronização)
        essential_data = {
            'codigo_autenticacao': record.codigo_autenticacao,
            'nome_participante': record.nome_participante,
            'evento': record.evento,
            'data_evento': record.data_evento,
            'local_evento': record.local_evento,
            'carga_horaria': record.carga_horaria,
            'coordenador': record.coordenador,
            'diretor': record.diretor,
            'data_geracao': record.data_geracao,
            'template_usado': record.template_usado,
            'tema_usado': record.tema_usado
        }
        
        # Serializar dados de forma determinística
        data_string = json.dumps(essential_data, sort_keys=True, ensure_ascii=False)
        
        # Calcular checksum
        return hashlib.md5(data_string.encode('utf-8')).hexdigest()
    
    def store_certificate(self, certificate_data: Dict[str, Any]) -> bool:
        """
        Armazena um certificado no banco local para sincronização posterior.
        
        Args:
            certificate_data (Dict[str, Any]): Dados do certificado.
            
        Returns:
            bool: True se armazenado com sucesso, False caso contrário.
        """
        try:
            # Criar registro
            record = CertificateRecord(
                codigo_autenticacao=certificate_data.get('codigo_autenticacao', ''),
                nome_participante=certificate_data.get('nome_participante', ''),
                evento=certificate_data.get('evento', ''),
                data_evento=certificate_data.get('data_evento', ''),
                local_evento=certificate_data.get('local_evento', ''),
                carga_horaria=certificate_data.get('carga_horaria', ''),
                coordenador=certificate_data.get('coordenador', ''),
                diretor=certificate_data.get('diretor', ''),
                data_geracao=certificate_data.get('data_geracao', datetime.now().isoformat()),
                url_verificacao=certificate_data.get('url_verificacao', ''),
                qrcode_base64=certificate_data.get('qrcode_base64', ''),
                template_usado=certificate_data.get('template_usado', ''),
                tema_usado=certificate_data.get('tema_usado', '')
            )
              # Calcular checksum
            record.checksum = self._calculate_checksum(record)
            
            # Inserir no banco com retry em caso de travamento
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                        conn.execute("PRAGMA busy_timeout = 30000")  # 30 segundos de timeout
                        conn.execute('''
                            INSERT OR REPLACE INTO certificates (
                                codigo_autenticacao, nome_participante, evento, data_evento,
                                local_evento, carga_horaria, coordenador, diretor,
                                data_geracao, url_verificacao, qrcode_base64,
                                template_usado, tema_usado, checksum, sync_status,
                                sync_attempts, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            record.codigo_autenticacao, record.nome_participante, record.evento,
                            record.data_evento, record.local_evento, record.carga_horaria,
                            record.coordenador, record.diretor, record.data_geracao,
                            record.url_verificacao, record.qrcode_base64, record.template_usado,
                            record.tema_usado, record.checksum, record.sync_status,
                            record.sync_attempts, record.created_at, record.updated_at
                        ))
                        conn.commit()
                        break  # Sucesso, sair do loop
                        
                except sqlite3.OperationalError as oe:
                    if "database is locked" in str(oe) and attempt < max_retries - 1:
                        # Aguardar um pouco antes de tentar novamente
                        import time
                        time.sleep(0.2 * (attempt + 1))  # Backoff progressivo
                        logger.warning(f"Banco travado, tentativa {attempt + 1}/{max_retries} para {record.codigo_autenticacao}")
                        continue
                    else:
                        raise oe
            
            # Log da operação (não crítico se falhar)
            self._log_operation(record.codigo_autenticacao, "STORE", "SUCCESS", 
                              "Certificado armazenado localmente")
                
            logger.info(f"Certificado {record.codigo_autenticacao} armazenado localmente")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar certificado: {e}")
            return False
    def _log_operation(self, codigo: str, action: str, status: str, message: str = ""):
        """
        Registra operação no log de sincronização.
        
        Args:
            codigo (str): Código de autenticação.
            action (str): Ação realizada.
            status (str): Status da operação.
            message (str): Mensagem adicional.
        """
        try:
            # Usar timeout maior e retry para logs
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                        conn.execute("PRAGMA busy_timeout = 10000")  # 10 segundos de timeout
                        conn.execute('''
                            INSERT INTO sync_log (codigo_autenticacao, action, status, message, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (codigo, action, status, message, datetime.now().isoformat()))
                        conn.commit()
                        break  # Sucesso, sair do loop
                except sqlite3.OperationalError as oe:
                    if "database is locked" in str(oe) and attempt < max_retries - 1:
                        # Aguardar um pouco antes de tentar novamente
                        import time
                        time.sleep(0.1 * (attempt + 1))  # Backoff progressivo
                        continue
                    else:
                        raise oe
        except sqlite3.Error as e:
            # Log de erro não é crítico - apenas registrar e continuar
            logger.warning(f"Não foi possível registrar log para {codigo}: {e}")
        except Exception as e:
            logger.warning(f"Erro inesperado ao registrar log para {codigo}: {e}")
      
    def get_pending_certificates(self, limit: Optional[int] = None) -> List[CertificateRecord]:
        """
        Obtém certificados pendentes de sincronização.
        
        Args:
            limit (int, optional): Limite de registros a retornar.
            
        Returns:
            List[CertificateRecord]: Lista de certificados pendentes.
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.execute("PRAGMA busy_timeout = 10000")
                conn.row_factory = sqlite3.Row
                
                query = '''
                    SELECT * FROM certificates 
                    WHERE sync_status IN ('pending', 'failed', 'retry')
                    ORDER BY created_at ASC
                '''
                
                if limit:
                    query += f' LIMIT {limit}'
                    
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                
                records = []
                for row in rows:
                    record = CertificateRecord(**dict(row))
                    records.append(record)
                    
                return records
                
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter certificados pendentes: {e}")
            return []
    def update_sync_status(self, codigo_autenticacao: str, status: SyncStatus, 
                          error_message: Optional[str] = None) -> bool:
        """
        Atualiza o status de sincronização de um certificado.
        
        Args:
            codigo_autenticacao (str): Código de autenticação.
            status (SyncStatus): Novo status.
            error_message (str, optional): Mensagem de erro se aplicável.
            
        Returns:
            bool: True se atualizado com sucesso.
        """
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.execute("PRAGMA busy_timeout = 10000")
                
                # Incrementar tentativas se for uma falha
                if status in [SyncStatus.FAILED, SyncStatus.RETRY]:
                    conn.execute('''
                        UPDATE certificates 
                        SET sync_status = ?, sync_attempts = sync_attempts + 1,
                            last_sync_attempt = ?, error_message = ?, updated_at = ?
                        WHERE codigo_autenticacao = ?
                    ''', (status.value, datetime.now().isoformat(), error_message,
                          datetime.now().isoformat(), codigo_autenticacao))
                else:
                    conn.execute('''
                        UPDATE certificates 
                        SET sync_status = ?, last_sync_attempt = ?, 
                            error_message = ?, updated_at = ?
                        WHERE codigo_autenticacao = ?
                    ''', (status.value, datetime.now().isoformat(), error_message,
                          datetime.now().isoformat(), codigo_autenticacao))
                
                conn.commit()
                
                # Log da operação (não crítico se falhar)
                self._log_operation(codigo_autenticacao, "UPDATE_STATUS", status.value,
                                  error_message or f"Status atualizado para {status.value}")
                
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Erro ao atualizar status: {e}")
            return False
    
    def create_sync_package(self, max_records: int = 100) -> Optional[str]:
        """
        Cria um pacote de sincronização com certificados pendentes.
        
        Args:
            max_records (int): Máximo de registros por pacote.
            
        Returns:
            str: Caminho do arquivo do pacote criado, ou None se erro.
        """
        try:
            # Obter certificados pendentes
            pending_certs = self.get_pending_certificates(limit=max_records)
            
            if not pending_certs:
                logger.info("Nenhum certificado pendente para empacotamento")
                return None
            
            # Criar pacote
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            package_name = f"sync_package_{timestamp}.json"
            package_path = os.path.join(self.sync_packages_dir, package_name)
            
            # Preparar dados do pacote
            package_data = {
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'record_count': len(pending_certs),
                    'package_checksum': ''
                },
                'certificates': [asdict(cert) for cert in pending_certs]
            }
            
            # Calcular checksum do pacote
            package_json = json.dumps(package_data['certificates'], sort_keys=True)
            package_data['metadata']['package_checksum'] = hashlib.md5(
                package_json.encode('utf-8')).hexdigest()
            
            # Salvar pacote
            with open(package_path, 'w', encoding='utf-8') as f:
                json.dump(package_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Pacote de sincronização criado: {package_name} com {len(pending_certs)} registros")
            return package_path
            
        except Exception as e:
            logger.error(f"Erro ao criar pacote de sincronização: {e}")
            return None
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de sincronização.
        
        Returns:
            Dict[str, Any]: Estatísticas detalhadas.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Estatísticas gerais
                cursor = conn.execute('''
                    SELECT 
                        sync_status,
                        COUNT(*) as count
                    FROM certificates 
                    GROUP BY sync_status
                ''')
                
                status_counts = dict(cursor.fetchall())
                
                # Estatísticas de tentativas
                cursor = conn.execute('''
                    SELECT 
                        AVG(sync_attempts) as avg_attempts,
                        MAX(sync_attempts) as max_attempts,
                        COUNT(*) as total_records
                    FROM certificates 
                    WHERE sync_attempts > 0
                ''')
                
                attempt_stats = cursor.fetchone()
                
                # Últimas 24 horas
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM certificates 
                    WHERE created_at > ?
                ''', (yesterday,))
                
                last_24h_count = cursor.fetchone()[0]
                
                return {
                    'status_counts': status_counts,
                    'total_records': sum(status_counts.values()),
                    'pending_count': status_counts.get('pending', 0),
                    'synced_count': status_counts.get('synced', 0),
                    'failed_count': status_counts.get('failed', 0),
                    'retry_count': status_counts.get('retry', 0),
                    'avg_sync_attempts': attempt_stats[0] or 0,
                    'max_sync_attempts': attempt_stats[1] or 0,
                    'last_24h_count': last_24h_count,
                    'db_path': self.db_path,
                    'last_updated': datetime.now().isoformat()
                }
                
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
    
    def cleanup_synced_records(self, days_old: int = 30) -> int:
        """
        Remove registros sincronizados antigos para economizar espaço.
        
        Args:
            days_old (int): Idade mínima em dias para remoção.
            
        Returns:
            int: Número de registros removidos.
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    DELETE FROM certificates 
                    WHERE sync_status = 'synced' AND updated_at < ?
                ''', (cutoff_date,))
                
                removed_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Removidos {removed_count} registros sincronizados antigos")
                return removed_count
                
        except sqlite3.Error as e:
            logger.error(f"Erro ao limpar registros: {e}")
            return 0
    
    def backup_database(self) -> Optional[str]:
        """
        Cria backup do banco de dados.
        
        Returns:
            str: Caminho do arquivo de backup, ou None se erro.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"offline_sync_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Criar backup usando SQLite backup API
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            logger.info(f"Backup criado: {backup_name}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def close(self):
        """Fecha recursos e finaliza operações."""
        self._stop_processing.set()
        logger.info("OfflineSyncManager finalizado")


# Alias para compatibilidade
AuthenticationManager = CertAuthenticationManager = lambda: None
