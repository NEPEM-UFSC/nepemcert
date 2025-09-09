# Sistema de Sincronização Offline - NEPEMCERT

## Visão Geral

O NEPEMCERT agora possui um sistema robusto de armazenamento offline para códigos de autenticação de certificados. Este sistema permite que os códigos sejam armazenados localmente quando não há conectividade com o servidor e sincronizados automaticamente quando a conexão for restaurada.

## Arquitetura do Sistema

### Componentes Principais

1. **OfflineSyncManager** (`app/offline_sync_manager.py`)
   - Gerencia o armazenamento local em SQLite
   - Controla status de sincronização
   - Cria pacotes para sincronização
   - Mantém integridade de dados com checksums

2. **AutoSyncService** (`app/auto_sync_service.py`)
   - Serviço de sincronização automática em background
   - Monitora conectividade continuamente
   - Sincroniza automaticamente quando conectado
   - Sistema de retry com backoff exponencial

3. **CertificateService** (`app/certificate_service.py`)
   - Integrado com o sistema offline
   - Armazena automaticamente durante geração
   - Mantém compatibilidade com fluxo existente

## Funcionalidades

### 🗄️ Armazenamento Local Robusto

- **Banco SQLite otimizado** com WAL mode para melhor performance
- **Checksums MD5** para verificação de integridade
- **Índices otimizados** para consultas rápidas
- **Estrutura normalizada** com tabelas de log e estatísticas

### 🔄 Sincronização Inteligente

- **Monitoramento automático** de conectividade
- **Sincronização em lotes** para eficiência
- **Rate limiting** para não sobrecarregar o servidor
- **Sistema de prioridades** para certificados urgentes

### 📦 Gestão de Pacotes

- **Criação automática** de pacotes JSON para sincronização
- **Compressão e otimização** de dados
- **Verificação de integridade** com checksums
- **Versionamento** de pacotes

### 🔧 Ferramentas de Manutenção

- **Backup automático** do banco de dados
- **Limpeza de registros antigos** para economizar espaço
- **Estatísticas detalhadas** de sincronização
- **Logs completos** de operações

## Uso via CLI

### Gerenciamento de Sincronização

```bash
# Ver estatísticas de sincronização
nepemcert sync --stats

# Listar certificados pendentes
nepemcert sync --pending

# Criar pacote de sincronização manual
nepemcert sync --package

# Limpar registros sincronizados (mais de 30 dias)
nepemcert sync --cleanup 30

# Criar backup do banco de dados
nepemcert sync --backup
```

### Serviço de Sincronização Automática

```bash
# Iniciar serviço automático
nepemcert auto-sync --start

# Iniciar como daemon (background)
nepemcert auto-sync --start --daemon

# Ver status do serviço
nepemcert auto-sync --status

# Forçar sincronização imediata
nepemcert auto-sync --force

# Parar serviço
nepemcert auto-sync --stop
```

## Uso Programático

### Armazenamento Básico

```python
from app.offline_sync_manager import OfflineSyncManager

# Inicializar gerenciador
sync_manager = OfflineSyncManager()

# Dados do certificado
certificate_data = {
    'codigo_autenticacao': 'abc123...',
    'nome_participante': 'Maria Silva',
    'evento': 'Workshop Python',
    'data_evento': '15/06/2025',
    'local_evento': 'UFSC',
    'carga_horaria': '20',
    'coordenador': 'Prof. João',
    'diretor': 'Prof. Ana',
    'data_geracao': '2025-06-17T10:30:00',
    'url_verificacao': 'https://nepemufsc.com/verificar',
    'qrcode_base64': 'data:image/png;base64,...',
    'template_usado': 'certificado_v1.html',
    'tema_usado': 'contemporaneo'
}

# Armazenar para sincronização posterior
success = sync_manager.store_certificate(certificate_data)
```

### Consulta de Dados

```python
# Obter certificados pendentes
pending_certs = sync_manager.get_pending_certificates(limit=50)

# Obter estatísticas
stats = sync_manager.get_sync_statistics()
print(f"Pendentes: {stats['pending_count']}")
print(f"Sincronizados: {stats['synced_count']}")

# Criar pacote para sincronização
package_path = sync_manager.create_sync_package(max_records=100)
```

### Serviço Automático

```python
from app.auto_sync_service import AutoSyncService

# Configurar serviço
service = AutoSyncService(
    server_url="https://nepemufsc.com/api",
    check_interval=30,  # verificar a cada 30s
    batch_size=10       # sincronizar 10 por vez
)

# Callbacks para monitoramento
def on_sync_success(cert):
    print(f"Sincronizado: {cert.nome_participante}")

def on_connectivity_change(old_status, new_status):
    if new_status:
        print("Conectividade restaurada!")

# Registrar callbacks
service.add_callback('sync_success', on_sync_success)
service.add_callback('connectivity_change', on_connectivity_change)

# Iniciar serviço
service.start()

# O serviço roda em background...

# Parar serviço
service.stop()
```

## Estrutura do Banco de Dados

### Tabela: certificates

| Campo | Tipo | Descrição |
|-------|------|-----------|
| codigo_autenticacao | TEXT (PK) | Código único do certificado |
| nome_participante | TEXT | Nome do participante |
| evento | TEXT | Nome do evento |
| data_evento | TEXT | Data do evento |
| local_evento | TEXT | Local do evento |
| carga_horaria | TEXT | Carga horária |
| coordenador | TEXT | Nome do coordenador |
| diretor | TEXT | Nome do diretor |
| data_geracao | TEXT | Data/hora de geração |
| url_verificacao | TEXT | URL para verificação |
| qrcode_base64 | TEXT | QR Code em base64 |
| template_usado | TEXT | Template utilizado |
| tema_usado | TEXT | Tema aplicado |
| checksum | TEXT | Checksum MD5 dos dados |
| sync_status | TEXT | Status de sincronização |
| sync_attempts | INTEGER | Número de tentativas |
| last_sync_attempt | TEXT | Última tentativa |
| error_message | TEXT | Mensagem de erro |
| created_at | TEXT | Data de criação |
| updated_at | TEXT | Data de atualização |

### Tabela: sync_log

Registra todas as operações de sincronização para auditoria.

### Tabela: sync_stats

Mantém estatísticas agregadas por data.

## Status de Sincronização

- **pending**: Aguardando primeira sincronização
- **syncing**: Em processo de sincronização
- **synced**: Sincronizado com sucesso
- **failed**: Falha permanente (máx. tentativas excedido)
- **retry**: Aguardando nova tentativa

## Configurações

### Parâmetros do OfflineSyncManager

- `max_retry_attempts`: Máximo de tentativas (padrão: 5)
- `base_retry_delay`: Delay base para retry (padrão: 2s)
- `max_retry_delay`: Delay máximo (padrão: 300s)

### Parâmetros do AutoSyncService

- `check_interval`: Intervalo de verificação (padrão: 30s)
- `batch_size`: Tamanho do lote (padrão: 10)
- `max_concurrent`: Threads simultâneas (padrão: 3)
- `min_sync_interval`: Intervalo mínimo entre syncs (padrão: 5s)

## Localizações de Arquivos

```
nepemcert/
├── data/
│   ├── offline_sync.db          # Banco principal
│   ├── backups/                 # Backups automáticos
│   │   └── offline_sync_backup_YYYYMMDD_HHMMSS.db
│   └── sync_packages/           # Pacotes de sincronização
│       └── sync_package_YYYYMMDD_HHMMSS.json
```

## Monitoramento e Logs

### Logs do Sistema

O sistema utiliza o logging padrão do Python. Configure o nível conforme necessário:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Métricas Disponíveis

- Total de certificados armazenados
- Certificados pendentes por status
- Taxa de sucesso de sincronização
- Tempo médio de sincronização
- Estatísticas de conectividade

## Troubleshooting

### Problemas Comuns

1. **Banco de dados corrompido**
   ```bash
   # Restaurar de backup
   nepemcert sync --backup
   ```

2. **Muitos certificados pendentes**
   ```bash
   # Forçar sincronização
   nepemcert auto-sync --force
   ```

3. **Conectividade instável**
   ```bash
   # Ajustar intervalo de verificação
   # Configurar no código: check_interval=60
   ```

4. **Espaço em disco**
   ```bash
   # Limpar registros antigos
   nepemcert sync --cleanup 30
   ```

### Verificação de Integridade

```python
# Verificar checksums
sync_manager = OfflineSyncManager()
pending_certs = sync_manager.get_pending_certificates()

for cert in pending_certs:
    calculated_checksum = sync_manager._calculate_checksum(cert)
    if calculated_checksum != cert.checksum:
        print(f"Checksum inválido para: {cert.codigo_autenticacao}")
```

## Migração e Atualização

### Migração de Dados Existentes

Para migrar códigos existentes do sistema antigo:

```python
# Exemplo de migração
from app.cert_auth_manager import CertAuthenticationManager
from app.offline_sync_manager import OfflineSyncManager

auth_manager = CertAuthenticationManager()
sync_manager = OfflineSyncManager()

# Buscar códigos existentes e migrar
# (implementar conforme estrutura atual)
```

## Integração com API

O sistema está preparado para integração com APIs REST. O formato esperado pelo servidor:

```json
{
    "codigo_autenticacao": "abc123...",
    "nome_participante": "Maria Silva",
    "evento": "Workshop Python",
    "data_evento": "15/06/2025",
    "local_evento": "UFSC",
    "carga_horaria": "20",
    "coordenador": "Prof. João",
    "diretor": "Prof. Ana",
    "data_geracao": "2025-06-17T10:30:00",
    "url_verificacao": "https://nepemufsc.com/verificar",
    "template_usado": "certificado_v1.html",
    "tema_usado": "contemporaneo",
    "checksum": "md5hash..."
}
```

## Segurança

- **Checksums MD5** para verificação de integridade
- **Validação de dados** antes da sincronização
- **Logs de auditoria** completos
- **Backup automático** para recuperação
- **Transações ACID** no SQLite

## Performance

### Otimizações Implementadas

- **WAL mode** no SQLite para melhor concorrência
- **Índices otimizados** para consultas frequentes
- **Processamento em lotes** para eficiência
- **Rate limiting** para não sobrecarregar recursos
- **Cleanup automático** de dados antigos

### Benchmarks Esperados

- **Inserção**: ~1000 certificados/segundo
- **Consulta**: ~5000 registros/segundo
- **Sincronização**: ~100 certificados/segundo (limitado por rede)