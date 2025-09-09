# 🔄 Sistema de Sincronização Offline - NEPEMCERT

> **Sistema robusto de armazenamento offline e sincronização automática para códigos de autenticação de certificados**

## 🎯 Funcionalidades Principais

✅ **Armazenamento Local Robusto** - SQLite otimizado com verificação de integridade  
✅ **Sincronização Automática** - Monitor contínuo de conectividade e sync em background  
✅ **Sistema de Retry Inteligente** - Backoff exponencial para falhas temporárias  
✅ **Gestão de Pacotes** - Criação automática de pacotes para sincronização manual  
✅ **Ferramentas de Manutenção** - Backup, limpeza e estatísticas detalhadas  
✅ **Interface CLI Completa** - Comandos para todas as operações  

## 🚀 Início Rápido

### 1. Instalação
```bash
# Certifique-se de que as dependências estão instaladas
pip install -r requirements.txt
```

### 2. Verificar Status
```bash
# Ver estatísticas atuais
nepemcert sync --stats
```

### 3. Iniciar Sincronização Automática
```bash
# Modo daemon (recomendado para produção)
nepemcert auto-sync --start --daemon

# Ou modo interativo (para desenvolvimento)
nepemcert auto-sync --start
```

## 📊 Comandos CLI

### Gerenciamento de Sincronização
```bash
nepemcert sync --stats          # Estatísticas detalhadas
nepemcert sync --pending        # Listar certificados pendentes
nepemcert sync --package        # Criar pacote de sincronização
nepemcert sync --cleanup 30     # Limpar registros antigos
nepemcert sync --backup         # Criar backup do banco
```

### Serviço Automático
```bash
nepemcert auto-sync --start --daemon    # Iniciar como daemon
nepemcert auto-sync --status            # Status do serviço
nepemcert auto-sync --force             # Forçar sincronização
nepemcert auto-sync --stop              # Parar serviço
```

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Geração de     │───▶│  OfflineSync     │───▶│  AutoSync       │
│  Certificados   │    │  Manager         │    │  Service        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌─────────────┐            ┌─────────────┐
                       │  SQLite DB  │            │  Servidor   │
                       │  (Local)    │            │  Remoto     │
                       └─────────────┘            └─────────────┘
```

### Componentes

- **OfflineSyncManager**: Gerencia armazenamento local SQLite
- **AutoSyncService**: Serviço de sincronização automática em background
- **CertificateService**: Integrado com sistema offline durante geração

## 📁 Estrutura de Dados

### Localização dos Arquivos
```
nepemcert/
├── data/
│   ├── offline_sync.db                    # Banco principal
│   ├── backups/                           # Backups automáticos
│   │   └── offline_sync_backup_*.db
│   └── sync_packages/                     # Pacotes de sincronização
│       └── sync_package_*.json
```

### Status de Sincronização
- `pending` - Aguardando primeira sincronização
- `syncing` - Em processo de sincronização  
- `synced` - Sincronizado com sucesso
- `failed` - Falha permanente
- `retry` - Aguardando nova tentativa

## 💻 Uso Programático

### Armazenamento Básico
```python
from app.offline_sync_manager import OfflineSyncManager

sync_manager = OfflineSyncManager()

certificate_data = {
    'codigo_autenticacao': 'abc123...',
    'nome_participante': 'Maria Silva',
    'evento': 'Workshop Python',
    # ... outros campos
}

success = sync_manager.store_certificate(certificate_data)
```

### Serviço Automático
```python
from app.auto_sync_service import AutoSyncService

service = AutoSyncService(
    server_url="https://certificados.nepemufsc/.netlify/functions/",
    check_interval=30,
    batch_size=10
)

service.start()  # Inicia sincronização automática
```

## 🔧 Configuração

### Parâmetros Principais

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `check_interval` | 30s | Intervalo de verificação de conectividade |
| `batch_size` | 10 | Certificados por lote de sincronização |
| `max_retry_attempts` | 5 | Máximo de tentativas por certificado |
| `min_sync_interval` | 5s | Intervalo mínimo entre sincronizações |

### Personalizações
```python
# Configuração customizada
service = AutoSyncService(
    server_url="https://seu-servidor.com/api",
    check_interval=60,      # 1 minuto
    batch_size=20,          # 20 certificados por vez
    max_concurrent=5        # 5 threads simultâneas
)
```

## 📈 Monitoramento

### Estatísticas em Tempo Real
```bash
nepemcert sync --stats
```

**Saída exemplo:**
```
📊 Estatísticas de Sincronização Offline

┌─────────────────────┬────────────┐
│ Status              │ Quantidade │
├─────────────────────┼────────────┤
│ 📋 Pendentes        │         42 │
│ ✅ Sincronizados    │        158 │
│ ❌ Falharam         │          3 │
│ 🔄 Aguardando retry │          7 │
│ 📊 Total            │        210 │
└─────────────────────┴────────────┘

📈 Últimas 24h: 25 novos certificados
🔢 Média de tentativas: 1.2
💾 Banco de dados: data/offline_sync.db
```

### Logs e Auditoria
O sistema mantém logs completos de todas as operações:
- Tentativas de sincronização
- Mudanças de conectividade
- Erros e recuperações
- Estatísticas por período

## 🚨 Troubleshooting

### Problemas Comuns

**1. Certificados não sincronizam**
```bash
# Verificar conectividade
nepemcert server --status

# Forçar sincronização
nepemcert auto-sync --force
```

**2. Banco de dados corrompido**
```bash
# Restaurar de backup
nepemcert sync --backup
```

**3. Muitos certificados pendentes**
```bash
# Aumentar batch_size e iniciar daemon
nepemcert auto-sync --start --daemon
```

**4. Espaço em disco insuficiente**
```bash
# Limpar registros antigos (30+ dias)
nepemcert sync --cleanup 30
```

## 🔒 Segurança e Integridade

- **Checksums MD5** para verificação de integridade
- **Transações ACID** no SQLite
- **Backup automático** antes de operações críticas
- **Logs de auditoria** completos
- **Validação de dados** antes da sincronização

## ⚡ Performance

### Otimizações Implementadas
- WAL mode no SQLite para melhor concorrência
- Índices otimizados para consultas frequentes
- Processamento em lotes para eficiência
- Rate limiting inteligente

### Benchmarks Esperados
- **Inserção**: ~1.000 certificados/segundo
- **Consulta**: ~5.000 registros/segundo  
- **Sincronização**: ~100 certificados/segundo (limitado por rede)

## 🎯 Casos de Uso

### 1. Ambiente com Conectividade Instável
- Sistema armazena automaticamente offline
- Sincroniza quando conexão é restaurada
- Retry automático para falhas temporárias

### 2. Geração em Lote Grande
- Certificados são armazenados localmente primeiro
- Sincronização acontece em background
- Não bloqueia o processo de geração

### 3. Backup e Recuperação
- Backups automáticos regulares
- Recuperação completa de dados
- Migração entre ambientes

## 📞 Suporte

Para dúvidas ou problemas:

1. **Verificar logs**: Use `nepemcert sync --stats` para diagnóstico
2. **Documentação completa**: Veja `docs/sincronizacao_offline.md`
3. **Exemplo prático**: Execute `python docs/exemplo_sincronizacao_offline.py`

## 🚀 Próximos Passos

- [ ] Interface web para monitoramento
- [ ] Sincronização incremental
- [ ] Compressão de dados
- [ ] Integração com webhooks
- [ ] Métricas avançadas

---

**💡 Dica**: Para produção, sempre use `nepemcert auto-sync --start --daemon` para manter a sincronização automática ativa em background.
