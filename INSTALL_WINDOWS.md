# Instalação no Windows - NEPEMCERT

Este guia fornece instruções específicas para instalar o NEPEMCERT no Windows, incluindo as dependências necessárias para o WeasyPrint.

## Pré-requisitos

- Windows 10 ou Windows 11
- Python 3.13 ou superior (recomendado e desenvolvido em 3.13.3)
- Conda (recomendado) ou pip

## Instalação Passo a Passo

### 1. Configurar o Ambiente Python

#### Opção A: Usando Conda (Recomendado)
```powershell
# Criar ambiente conda
conda create -n nepemcert python=3.10

# Ativar o ambiente
conda activate nepemcert
```

### 2. Instalar Dependências do Sistema (GTK3)

O WeasyPrint depende do GTK3 Runtime para funcionar no Windows.

#### Instalador Oficial
1. Baixe o GTK3 Runtime for Windows:
   - Acesse: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
   - Baixe a versão mais recente (ex: `gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe`)

2. Execute o instalador:
   ```powershell
   # Execute como Administrador
   .\gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe
   ```

3. Siga as instruções do instalador:
   - Aceite os termos de licença
   - Mantenha o diretório padrão de instalação
   - Marque a opção "Add to PATH" se disponível

### 3. Instalar Dependências Python

```powershell
# Certificar-se de que está no ambiente correto
conda activate nepemcert

# Atualizar pip
python -m pip install --upgrade pip

# Instalar dependências do projeto
pip install -r requirements.txt
```

### 4. Verificar Instalação

```powershell
# Testar importação do WeasyPrint
python -c "import weasyprint; print('WeasyPrint instalado com sucesso!')"

# Testar geração de PDF básica
python -c "
from weasyprint import HTML
html = HTML(string='<h1>Teste</h1>')
print('Teste de geração de PDF realizado com sucesso!')
"
```

### 5. Executar o NEPEMCERT

```powershell
# Modo interativo
python nepemcert.py interactive

# Ou usar o arquivo batch
.\nepemcert.bat interactive
```

## Solução de Problemas

### Erro: "DLL load failed while importing _ffi"
**Causa**: GTK3 não está instalado corretamente ou não está no PATH.

**Solução**:
1. Reinstale o GTK3 Runtime
2. Verifique se o diretório de instalação está no PATH:
   ```powershell
   echo $env:PATH
   ```
3. Adicione manualmente se necessário:
   ```powershell
   $env:PATH += ";C:\Program Files\GTK3-Runtime Win64\bin"
   ```

### Erro: "FileNotFoundError: [WinError 2] The system cannot find the file specified"
**Causa**: Bibliotecas GTK não encontradas.

**Solução**:
1. Verifique se o GTK3 está instalado:
   ```powershell
   where gtk-launch
   ```
2. Se não encontrar, reinstale o GTK3 Runtime

### Erro de compilação durante instalação do WeasyPrint
**Causa**: Ferramentas de build não estão disponíveis.

**Solução**:
```powershell
# Instalar Visual Studio Build Tools
choco install visualstudio2022buildtools

# Ou baixar manualmente de:
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
```

### Erro: "ImportError: cannot import name 'HTML' from 'weasyprint'"
**Causa**: Versão incompatível do WeasyPrint.

**Solução**:
```powershell
# Desinstalar e reinstalar versão específica
pip uninstall weasyprint
pip install weasyprint==62.3
```

### Fontes não aparecem corretamente nos PDFs
**Causa**: Fontes do sistema não estão sendo detectadas.

**Solução**:
1. Instale fontes comuns:
   ```powershell
   # Via chocolatey
   choco install fonts-arial fonts-times-new-roman
   ```
2. Ou configure fontes específicas no template HTML

### Performance lenta na geração de PDFs
**Solução**:
1. Use SSD para diretórios temporários
2. Configure variável de ambiente:
   ```powershell
   $env:WEASYPRINT_FONTCONFIG_CACHE = "C:\temp\fontconfig"
   ```

## Configuração Avançada

### Configurar Cache de Fontes
```powershell
# Criar diretório de cache
mkdir C:\temp\fontconfig

# Definir variável de ambiente permanentemente
[Environment]::SetEnvironmentVariable("WEASYPRINT_FONTCONFIG_CACHE", "C:\temp\fontconfig", "User")
```

### Configurar Proxy (se necessário)
```powershell
# Configurar proxy para pip
pip config set global.proxy http://proxy.empresa.com:8080
```

### Script de Instalação Automatizada

Salve o script abaixo como `install-nepemcert.ps1`:

```powershell
# Script de instalação automatizada para NEPEMCERT no Windows
param(
    [switch]$UseChocolatey = $false
)

Write-Host "=== Instalação NEPEMCERT para Windows ===" -ForegroundColor Green

# Verificar se Python está instalado
try {
    $pythonVersion = python --version
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python não encontrado. Instale Python 3.10+ primeiro." -ForegroundColor Red
    exit 1
}

# Criar ambiente conda
Write-Host "Criando ambiente conda..." -ForegroundColor Yellow
conda create -n nepemcert python=3.10 -y
conda activate nepemcert

# Instalar GTK3
if ($UseChocolatey) {
    Write-Host "Instalando GTK3 via Chocolatey..." -ForegroundColor Yellow
    choco install gtk-runtime -y
} else {
    Write-Host "Por favor, baixe e instale o GTK3 Runtime manualmente:" -ForegroundColor Yellow
    Write-Host "https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases" -ForegroundColor Cyan
    Read-Host "Pressione Enter após instalar o GTK3"
}

# Instalar dependências Python
Write-Host "Instalando dependências Python..." -ForegroundColor Yellow
pip install -r requirements.txt

# Testar instalação
Write-Host "Testando instalação..." -ForegroundColor Yellow
try {
    python -c "import weasyprint; print('WeasyPrint OK')"
    Write-Host "Instalação concluída com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "Erro na instalação. Verifique os logs acima." -ForegroundColor Red
}
```

Execute com:
```powershell
# Com chocolatey
.\install-nepemcert.ps1 -UseChocolatey

# Instalação manual do GTK3
.\install-nepemcert.ps1
```

## Atualização

Para atualizar o NEPEMCERT:

```powershell
# Ativar ambiente
conda activate nepemcert

# Atualizar dependências
pip install -r requirements.txt --upgrade

# Testar
python -c "import weasyprint; print('Atualização OK')"
```

## Desinstalação

```powershell
# Remover ambiente conda
conda remove -n nepemcert --all

# Desinstalar GTK3 (opcional)
choco uninstall gtk-runtime
```

## Suporte

Se encontrar problemas:

1. Verifique os logs de erro
2. Consulte a documentação oficial do WeasyPrint: https://doc.courtbouillon.org/weasyprint/
3. Abra uma issue no repositório do projeto

## Versões Testadas

- Windows 11 Professional
- Python 3.10.12
- WeasyPrint 62.3
- GTK3 Runtime 3.24.31
