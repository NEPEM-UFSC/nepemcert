# Guia de Implementação - API de Certificados

## Casos de Uso Comuns

### 1. Fluxo Completo de Criação de Certificados

Este exemplo demonstra como criar uma chave de API e usar para emitir certificados:

```javascript
// 1. Primeiro, criar uma chave de API (precisa de token admin)
const adminToken = 'your-admin-jwt-token';

async function setupAPI() {
  // Criar chave para emissão de certificados
  const keyResponse = await fetch('/.netlify/functions/createKey', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${adminToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      role: 'issuer',
      isActive: true,
      secret: 'minha-chave-secreta-segura-123'
    })
  });
  
  const keyData = await keyResponse.json();
  console.log('Chave criada:', keyData.id);
  
  // 2. Criar JWT para a nova chave
  const jwt = require('jsonwebtoken');
  const issuerToken = jwt.sign(
    { 
      keyId: keyData.id,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + (60 * 60 * 24) // 24 horas
    },
    'minha-chave-secreta-segura-123'
  );
  
  // 3. Criar certificados usando a nova chave
  const certificates = [
    {
      code: 'WORKSHOP2024-001',
      name: 'Maria Silva',
      event: 'Workshop de React 2024',
      date: '2024-08-15',
      hours: '16',
      description: 'Participação completa no workshop de React com certificação'
    },
    {
      code: 'WORKSHOP2024-002', 
      name: 'João Santos',
      event: 'Workshop de React 2024',
      date: '2024-08-15',
      hours: '16',
      description: 'Participação completa no workshop de React com certificação'
    }
  ];
  
  for (const cert of certificates) {
    const response = await fetch('/.netlify/functions/writeCertificate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${issuerToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(cert)
    });
    
    const result = await response.json();
    console.log(`Certificado ${cert.code} criado:`, result);
  }
}
```

### 2. Sistema de Validação de Certificados para Frontend

```html
<!DOCTYPE html>
<html>
<head>
    <title>Validador de Certificados</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        .certificate { border: 1px solid #ddd; padding: 20px; margin-top: 20px; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Validador de Certificados</h1>
        
        <div class="form-group">
            <label for="code">Código do Certificado:</label>
            <input type="text" id="code" placeholder="Ex: WORKSHOP2024-001">
            <button onclick="validateCertificate()">Validar</button>
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        async function validateCertificate() {
            const code = document.getElementById('code').value.trim();
            const resultDiv = document.getElementById('result');
            
            if (!code) {
                resultDiv.innerHTML = '<p class="error">Por favor, insira o código do certificado.</p>';
                return;
            }
            
            try {
                const response = await fetch(`/.netlify/functions/getCertificate?code=${encodeURIComponent(code)}`);
                const data = await response.json();
                
                if (response.ok) {
                    resultDiv.innerHTML = `
                        <div class="certificate success">
                            <h3>✅ Certificado Válido</h3>
                            <p><strong>Nome:</strong> ${data.name}</p>
                            <p><strong>Evento:</strong> ${data.event}</p>
                            <p><strong>Data:</strong> ${data.date || 'Não informada'}</p>
                            <p><strong>Carga Horária:</strong> ${data.hours || 'Não informada'} horas</p>
                            <p><strong>Descrição:</strong> ${data.description || 'Sem descrição'}</p>
                            <p><strong>Emitido em:</strong> ${new Date(data.timestamp).toLocaleString('pt-BR')}</p>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<p class="error">❌ ${data.message}</p>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<p class="error">❌ Erro ao validar certificado: ${error.message}</p>`;
            }
        }
        
        // Permitir validação com Enter
        document.getElementById('code').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                validateCertificate();
            }
        });
    </script>
</body>
</html>
```

### 3. Script Python para Importação em Massa

```python
import pandas as pd
import requests
import jwt
from datetime import datetime, timedelta
import json

class CertificateBatchProcessor:
    def __init__(self, base_url, key_id, secret):
        self.base_url = base_url
        self.key_id = key_id
        self.secret = secret
        self.token = self._create_token()
    
    def _create_token(self):
        """Cria JWT token para autenticação"""
        payload = {
            'keyId': self.key_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')
    
    def process_csv(self, csv_file, event_name, event_date=None, hours=None):
        """
        Processa arquivo CSV e cria certificados
        
        CSV deve ter colunas: name, email, description (opcional)
        """
        df = pd.read_csv(csv_file)
        results = []
        
        for index, row in df.iterrows():
            # Gerar código único baseado no índice e timestamp
            code = f"{event_name.upper().replace(' ', '')}-{index+1:03d}-{int(datetime.now().timestamp())}"
            
            certificate_data = {
                'code': code,
                'name': row['name'],
                'event': event_name,
                'date': event_date,
                'hours': hours,
                'description': row.get('description', f'Participação no evento {event_name}')
            }
            
            try:
                result = self._create_certificate(certificate_data)
                results.append({
                    'code': code,
                    'name': row['name'],
                    'status': 'success',
                    'message': result.get('message', 'Created successfully')
                })
                print(f"✅ Certificado criado para {row['name']}: {code}")
                
            except Exception as e:
                results.append({
                    'code': code,
                    'name': row['name'],
                    'status': 'error',
                    'message': str(e)
                })
                print(f"❌ Erro ao criar certificado para {row['name']}: {e}")
        
        # Salvar relatório
        results_df = pd.DataFrame(results)
        results_df.to_csv(f'certificate_results_{int(datetime.now().timestamp())}.csv', index=False)
        
        return results
    
    def _create_certificate(self, certificate_data):
        """Cria um certificado individual"""
        response = requests.post(
            f'{self.base_url}/writeCertificate',
            headers={
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            },
            json=certificate_data
        )
        
        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.json().get('message', 'Unknown error')}")
        
        return response.json()
    
    def validate_certificate(self, code):
        """Valida se um certificado existe"""
        response = requests.get(
            f'{self.base_url}/getCertificate',
            params={'code': code}
        )
        return response.ok, response.json()

# Exemplo de uso
if __name__ == "__main__":
    # Configurações
    processor = CertificateBatchProcessor(
        base_url='https://seu-site.netlify.app/.netlify/functions',
        key_id='sua-key-id',
        secret='sua-chave-secreta'
    )
    
    # Processar CSV
    results = processor.process_csv(
        csv_file='participantes.csv',
        event_name='Workshop Python 2024',
        event_date='2024-08-20',
        hours='12'
    )
    
    print(f"\nProcessamento concluído!")
    print(f"Total processados: {len(results)}")
    print(f"Sucessos: {len([r for r in results if r['status'] == 'success'])}")
    print(f"Erros: {len([r for r in results if r['status'] == 'error'])}")
```

### 4. Middleware Express.js para Autenticação

```javascript
const jwt = require('jsonwebtoken');

class CertificateAPIClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }
    
    // Middleware para Express.js
    createAuthMiddleware(keyId, secret) {
        return (req, res, next) => {
            try {
                const token = jwt.sign(
                    { 
                        keyId: keyId,
                        iat: Math.floor(Date.now() / 1000),
                        exp: Math.floor(Date.now() / 1000) + (60 * 30) // 30 minutos
                    },
                    secret
                );
                
                req.certificateToken = token;
                next();
            } catch (error) {
                res.status(500).json({ error: 'Falha na autenticação da API de certificados' });
            }
        };
    }
    
    // Helper para criar certificados
    async createCertificate(token, certificateData) {
        const response = await fetch(`${this.baseUrl}/writeCertificate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(certificateData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erro ao criar certificado');
        }
        
        return await response.json();
    }
    
    // Helper para buscar certificados
    async getCertificate(code) {
        const response = await fetch(`${this.baseUrl}/getCertificate?code=${encodeURIComponent(code)}`);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Erro ao buscar certificado');
        }
        
        return await response.json();
    }
}

// Exemplo de uso com Express.js
const express = require('express');
const app = express();

const certificateAPI = new CertificateAPIClient('https://seu-site.netlify.app/.netlify/functions');

// Middleware de autenticação
app.use('/api/certificates', certificateAPI.createAuthMiddleware('sua-key-id', 'sua-chave-secreta'));

// Rota para criar certificado
app.post('/api/certificates', async (req, res) => {
    try {
        const result = await certificateAPI.createCertificate(req.certificateToken, req.body);
        res.status(201).json(result);
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

// Rota para buscar certificado
app.get('/api/certificates/:code', async (req, res) => {
    try {
        const result = await certificateAPI.getCertificate(req.params.code);
        res.json(result);
    } catch (error) {
        res.status(404).json({ error: error.message });
    }
});
```

### 5. Classe PHP para Integração

```php
<?php

class CertificateAPI {
    private $baseUrl;
    private $keyId;
    private $secret;
    
    public function __construct($baseUrl, $keyId, $secret) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->keyId = $keyId;
        $this->secret = $secret;
    }
    
    private function createToken($expirationMinutes = 60) {
        $header = json_encode(['typ' => 'JWT', 'alg' => 'HS256']);
        $payload = json_encode([
            'keyId' => $this->keyId,
            'iat' => time(),
            'exp' => time() + ($expirationMinutes * 60)
        ]);
        
        $headerEncoded = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($header));
        $payloadEncoded = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($payload));
        
        $signature = hash_hmac('sha256', $headerEncoded . "." . $payloadEncoded, $this->secret, true);
        $signatureEncoded = str_replace(['+', '/', '='], ['-', '_', ''], base64_encode($signature));
        
        return $headerEncoded . "." . $payloadEncoded . "." . $signatureEncoded;
    }
    
    public function createCertificate($certificateData) {
        $token = $this->createToken();
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $this->baseUrl . '/writeCertificate');
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($certificateData));
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Authorization: Bearer ' . $token,
            'Content-Type: application/json'
        ]);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $data = json_decode($response, true);
        
        if ($httpCode >= 400) {
            throw new Exception($data['message'] ?? 'Erro desconhecido');
        }
        
        return $data;
    }
    
    public function getCertificate($code) {
        $url = $this->baseUrl . '/getCertificate?code=' . urlencode($code);
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $data = json_decode($response, true);
        
        if ($httpCode >= 400) {
            throw new Exception($data['message'] ?? 'Certificado não encontrado');
        }
        
        return $data;
    }
    
    public function validateCertificate($code) {
        try {
            $certificate = $this->getCertificate($code);
            return [
                'valid' => true,
                'certificate' => $certificate
            ];
        } catch (Exception $e) {
            return [
                'valid' => false,
                'error' => $e->getMessage()
            ];
        }
    }
}

// Exemplo de uso
try {
    $api = new CertificateAPI(
        'https://seu-site.netlify.app/.netlify/functions',
        'sua-key-id',
        'sua-chave-secreta'
    );
    
    // Criar certificado
    $certificate = $api->createCertificate([
        'code' => 'PHP-CERT-001',
        'name' => 'João Silva',
        'event' => 'Curso de PHP Avançado',
        'date' => '2024-08-20',
        'hours' => '40'
    ]);
    
    echo "Certificado criado: " . $certificate['id'] . "\n";
    
    // Validar certificado
    $validation = $api->validateCertificate('PHP-CERT-001');
    if ($validation['valid']) {
        echo "Certificado válido para: " . $validation['certificate']['name'] . "\n";
    }
    
} catch (Exception $e) {
    echo "Erro: " . $e->getMessage() . "\n";
}
?>
```

### 6. Monitoramento e Logs

```javascript
// Sistema de logs para monitorar uso da API
class APIMonitor {
    constructor(webhookUrl) {
        this.webhookUrl = webhookUrl;
    }
    
    async logAPIUsage(endpoint, method, statusCode, userId = null) {
        const logData = {
            timestamp: new Date().toISOString(),
            endpoint,
            method,
            statusCode,
            userId,
            userAgent: navigator.userAgent
        };
        
        try {
            await fetch(this.webhookUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(logData)
            });
        } catch (error) {
            console.error('Erro ao enviar log:', error);
        }
    }
    
    // Wrapper para requisições com log automático
    async makeAPIRequest(url, options = {}) {
        const startTime = Date.now();
        
        try {
            const response = await fetch(url, options);
            const endTime = Date.now();
            
            await this.logAPIUsage(
                url,
                options.method || 'GET',
                response.status,
                options.userId
            );
            
            console.log(`API Request: ${options.method || 'GET'} ${url} - ${response.status} (${endTime - startTime}ms)`);
            
            return response;
        } catch (error) {
            await this.logAPIUsage(
                url,
                options.method || 'GET',
                0,
                options.userId
            );
            throw error;
        }
    }
}

// Uso
const monitor = new APIMonitor('https://your-webhook-url.com/api-logs');

// Exemplo de uso com monitoramento
async function createCertificateWithLog(certificateData, token, userId) {
    return await monitor.makeAPIRequest('/.netlify/functions/writeCertificate', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(certificateData),
        userId: userId
    });
}
```

## Testes Automatizados

```javascript
// Testes Jest para a API
const jwt = require('jsonwebtoken');

describe('Certificate API', () => {
    const baseUrl = 'https://seu-site.netlify.app/.netlify/functions';
    let adminToken, issuerToken;
    
    beforeAll(() => {
        // Criar tokens de teste
        adminToken = jwt.sign(
            { keyId: 'test-admin-key', iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600 },
            'test-admin-secret'
        );
        
        issuerToken = jwt.sign(
            { keyId: 'test-issuer-key', iat: Math.floor(Date.now() / 1000), exp: Math.floor(Date.now() / 1000) + 3600 },
            'test-issuer-secret'
        );
    });
    
    test('Deve criar um certificado com dados válidos', async () => {
        const certificateData = {
            code: `TEST-${Date.now()}`,
            name: 'João Teste',
            event: 'Evento de Teste',
            date: '2024-08-20',
            hours: '8'
        };
        
        const response = await fetch(`${baseUrl}/writeCertificate`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${issuerToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(certificateData)
        });
        
        expect(response.status).toBe(201);
        const result = await response.json();
        expect(result.message).toContain('successfully');
        expect(result.id).toBe(certificateData.code);
    });
    
    test('Deve buscar um certificado existente', async () => {
        const code = 'TEST-EXISTING';
        
        const response = await fetch(`${baseUrl}/getCertificate?code=${code}`);
        
        if (response.status === 200) {
            const result = await response.json();
            expect(result.code).toBe(code);
            expect(result.name).toBeDefined();
        } else {
            expect(response.status).toBe(404);
        }
    });
    
    test('Deve rejeitar criação sem autenticação', async () => {
        const response = await fetch(`${baseUrl}/writeCertificate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: 'TEST', name: 'Test', event: 'Test' })
        });
        
        expect(response.status).toBe(401);
    });
});
```

Este guia fornece exemplos práticos e casos de uso reais para implementar e usar a API de certificados em diferentes linguagens e cenários.
