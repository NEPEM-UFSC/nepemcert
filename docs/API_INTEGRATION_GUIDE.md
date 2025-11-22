# Guia de Integração com a API de Certificados

## Visão Geral

O NEPEMCERT agora possui integração completa com a API do servidor `certificados.nepemufsc.com` para registro e consulta de certificados online.

## 🔑 Sistema de Chaves de API

### Tipos de Chaves

O sistema utiliza três tipos de chaves de API:

| Tipo | Permissões | Uso |
|------|-----------|-----|
| **admin** | Criar chaves, gerenciar tudo | Administração do sistema |
| **issuer** | Criar e modificar certificados | Geração de certificados |
| **reader** | Consultar certificados | Verificação pública |

### Chaves Master

O sistema inclui duas chaves master hardcoded para bootstrap:

- **masterkey** (admin): Chave administrativa principal
- **nepemcert-bootstrap** (bootstrap): Permite criar apenas chaves reader

## 📁 Estrutura de Arquivos

```
nepemcert/
├── keys/                    # Diretório de chaves de API
│   ├── issuer_*.key        # Chaves de emissão
│   ├── reader_*.key        # Chaves de leitura
│   └── admin_*.key         # Chaves administrativas
├── app/
│   ├── api_key_manager.py  # Gerenciador de chaves
│   ├── api_client.py       # Cliente da API Netlify
│   └── cli/
│       └── cli_api_keys.py # Interface CLI para chaves
└── requirements.txt        # Inclui PyJWT>=2.8.0
```

## 🚀 Primeiros Passos

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

Isso instalará o PyJWT necessário para autenticação.

### 2. Configurar Chaves Iniciais

Inicie o NEPEMCERT e acesse:

```
Menu Principal → Configurações → 🔑 Gerenciar Chaves de API → 🔑 Configurar Chaves Iniciais
```

Isso criará automaticamente:
- Uma chave **issuer** (para registrar certificados)
- Uma chave **reader** (para consultas)

As chaves serão salvas em `keys/` e carregadas automaticamente nas próximas execuções.

### 3. Verificar Conexão

No menu de chaves, use:
```
🔍 Testar Conexão com Servidor
```

## 💻 Modo de Desenvolvimento

Por padrão, o sistema opera em **modo desenvolvimento** usando:
- **URL**: `http://localhost:8888/.netlify/functions`

Para usar em produção, alterne no menu:
```
⚙️ Configurações da API → 🔄 Alternar Modo (Dev/Prod)
```

Produção usa:
- **URL**: `https://certificados.nepemufsc.com/.netlify/functions`

## 🔄 Fluxo de Geração de Certificados

### Automático (Padrão)

Ao gerar certificados, o sistema:

1. ✅ Gera o PDF localmente
2. ✅ Armazena no banco de dados SQLite local (offline)
3. ⚠️ **Não registra automaticamente na API online**

### Manual (Sincronização)

Para enviar certificados para o servidor:

```python
from app.certificate_service import CertificateService

service = CertificateService(enable_api_sync=True, api_dev_mode=True)

# Dados do certificado
cert_data = {
    "code": "NEPEM2025001",
    "name": "João Silva",
    "event": "Workshop de Python"
}

# Sincronizar com API
service.sync_certificate_to_api(
    auth_code=cert_data["code"],
    participant_name=cert_data["name"],
    event_name=cert_data["event"]
)
```

### Em Lote

```python
certificates_data = [
    {"code": "CERT001", "name": "Maria", "event": "Workshop"},
    {"code": "CERT002", "name": "João", "event": "Workshop"},
]

result = service.sync_certificates_batch_to_api(certificates_data)
print(f"Sucesso: {result['success']}/{result['total']}")
```

## 🔧 API Client - Uso Programático

### Criar Chave de API

```python
from app.api_client import CertificateAPIClient

client = CertificateAPIClient(dev_mode=True)

# Criar chave issuer
new_key = client.create_api_key(
    role="issuer",
    is_active=True,
    description="Chave para sistema X",
    save_to_file=True
)

print(f"Chave criada: {new_key.key_id}")
```

### Registrar Certificado

```python
# Autoload de chave issuer/admin
client.key_manager.autoload_keys()

# Dados do certificado
cert_data = {
    "code": "NEPEM2025001",
    "name": "João Silva",
    "event": "Workshop de Python",
    "date": "2025-10-11",
    "hours": "20h"
}

# Registrar
result = client.create_certificate(cert_data)
```

### Consultar Certificado

```python
# Não requer autenticação
cert = client.get_certificate("NEPEM2025001")

if cert:
    print(f"Participante: {cert['name']}")
    print(f"Evento: {cert['event']}")
```

## 📚 Módulos Criados

### `api_key_manager.py`

**Classes:**
- `APIKey`: Representa uma chave de API
- `APIKeyManager`: Gerencia criação, armazenamento e carregamento de chaves

**Principais métodos:**
- `save_key_to_file()`: Salva chave em arquivo .key
- `load_key_from_file()`: Carrega chave de arquivo
- `autoload_keys()`: Carrega automaticamente chaves do diretório
- `generate_jwt_token()`: Gera token JWT para autenticação
- `get_master_key()`: Retorna chaves master

### `api_client.py`

**Classe:**
- `CertificateAPIClient`: Cliente para API Netlify

**Principais métodos:**
- `create_api_key()`: Cria nova chave no servidor
- `create_certificate()`: Registra certificado individual
- `create_certificates_batch()`: Registra múltiplos certificados
- `get_certificate()`: Consulta certificado por código
- `test_connection()`: Testa conectividade
- `setup_initial_keys()`: Configura chaves iniciais

### `certificate_service.py` (Atualizado)

**Novos métodos:**
- `sync_certificate_to_api()`: Sincroniza certificado individual
- `sync_certificates_batch_to_api()`: Sincroniza múltiplos certificados
- `enable_online_sync()`: Habilita sincronização online
- `disable_online_sync()`: Desabilita sincronização online

## 🔒 Segurança

### Armazenamento de Chaves

As chaves são armazenadas em arquivos JSON no diretório `keys/`:

```json
{
  "keyId": "key_abc123",
  "secret": "secret_xyz789",
  "role": "issuer",
  "description": "Chave para NEPEMCERT",
  "isActive": true,
  "createdAt": "2025-10-11T10:30:00"
}
```

⚠️ **IMPORTANTE:**
- Mantenha o diretório `keys/` fora do controle de versão
- Faça backup seguro das chaves
- Não compartilhe chaves entre instalações

### Autenticação JWT

Cada requisição usa token JWT:

```python
# Token é gerado automaticamente
headers = {
    "Authorization": "Bearer <jwt_token>",
    "Content-Type": "application/json"
}
```

Payload do JWT:
```json
{
  "keyId": "key_abc123",
  "exp": 1728648000,  // Timestamp de expiração
  "iat": 1728644400   // Timestamp de criação
}
```

## 🐛 Troubleshooting

### Chave não encontrada

**Problema:** "Nenhuma chave issuer ou admin encontrada"

**Solução:**
1. Acesse o menu de chaves de API
2. Execute "Configurar Chaves Iniciais"
3. Ou manualmente crie uma chave issuer

### Erro de conexão

**Problema:** "Servidor não acessível"

**Soluções:**
- **Modo Dev:** Certifique-se de que `netlify dev` está rodando
- **Modo Prod:** Verifique conexão com internet
- Teste com: Menu → Chaves de API → Testar Conexão

### Token expirado

**Problema:** "Token JWT expirado"

**Solução:** Os tokens expiram em 1 hora. O sistema regenera automaticamente, mas se persistir:
```python
# Forçar regeneração
key_manager.autoload_keys()  # Recarrega chaves
```

### Erro 401 Unauthorized

**Problema:** Chave sem permissões

**Solução:**
- Verifique se a chave tem o role correto (issuer/admin para criar certificados)
- Verifique se a chave está ativa (`isActive: true`)

## 📊 Comparação: Sistema Antigo vs Novo

| Aspecto | Antigo (`auth_manager.py`) | Novo (`api_client.py`) |
|---------|---------------------------|----------------------|
| **Autenticação** | client_id + client_key | JWT com keyId + secret |
| **Gerenciamento de Chaves** | ❌ Não implementado | ✅ Completo |
| **Registro de Certificados** | ❌ Não implementado | ✅ Implementado |
| **Roles** | ❌ Não | ✅ admin/issuer/reader |
| **URL** | nepem-server.netlify.app | certificados.nepemufsc.com |
| **Armazenamento** | keyring do sistema | Arquivos .key |
| **Autoload** | ❌ Não | ✅ Sim |
| **Interface CLI** | ❌ Não | ✅ Menu completo |

## 📝 Próximos Passos

1. ✅ Instalação do PyJWT
2. ✅ Configuração de chaves iniciais
3. ⚠️ Testar registro de certificados em desenvolvimento
4. ⏳ Migrar para produção quando pronto
5. ⏳ Implementar sincronização automática no fluxo de geração

## 🤝 Compatibilidade

O sistema **mantém compatibilidade** com:
- ✅ Armazenamento local SQLite (offline)
- ✅ Geração de QR codes
- ✅ Sistema de códigos de autenticação existente

O novo sistema **adiciona** capacidade de sincronização online sem quebrar funcionalidades existentes.

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique este guia primeiro
2. Execute diagnóstico: `python diagnose.py`
3. Verifique logs de erro no terminal
4. Teste conexão com servidor

---

**Versão do Guia:** 1.0  
**Data:** 11 de outubro de 2025  
**Compatível com:** NEPEMCERT v1.1.0+
