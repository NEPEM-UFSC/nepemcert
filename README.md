# NEPEM Certificados

Um aplicativo interno para geração de certificados em lote de participação das capacitações e eventos realizados pelo NEPEM-UFSC.

## Características

- Interface de linha de comando interativa
- Geração de certificados em lote a partir de dados CSV
- Gerenciamento de templates HTML
- Template engine robusta e moderna.
- Personalização de certificados com base em dados
- Exportação para PDF e ZIP
- Sincronização com servidor remoto para autenticação.
- Interface moderna usando Rich e questionary

## Requisitos

- Python 3.10 ou superior
- Dependências listadas em requirements.txt

### Instalação no Windows

Este projeto utiliza **WeasyPrint** para geração de PDFs, que requer algumas dependências específicas no Windows:

#### 1. Instale o GTK3 Runtime
WeasyPrint depende do GTK3. Para Windows, baixe e instale:
- [GTK3 Runtime for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases)
- Baixe a versão mais recente do instalador (.exe)
- Execute como administrador e siga as instruções de instalação

#### 2. Instale as dependências Python
Após instalar o GTK3, instale as dependências do projeto:

```powershell
# Ative seu ambiente conda (se estiver usando)
conda activate nepemcert

# Instale as dependências
pip install -r requirements.txt
```

#### 3. Verificação da Instalação
Para verificar se o WeasyPrint foi instalado corretamente:

```powershell
python -c "import weasyprint; print('WeasyPrint instalado com sucesso!')"
```

#### Solução de Problemas - Windows

Se encontrar erros durante a instalação:

1. **Erro de DLL não encontrada**: Certifique-se de que o GTK3 Runtime foi instalado corretamente
2. **Erro de compilação**: Instale as ferramentas de build do Visual Studio:
   ```powershell
   # Instale as Build Tools for Visual Studio
   # Ou instale via chocolatey:
   choco install visualstudio2022buildtools
   ```
3. **Erro de fontes**: O WeasyPrint pode precisar de fontes específicas. Instale fontes comuns do sistema

## Uso

### Interface Interativa

Para iniciar a interface interativa:

```
python nepemcert.py interactive
```

ou simplesmente:

```
nepemcert.bat interactive
```

### Comandos Diretos

Para gerar certificados diretamente:

```
python nepemcert.py generate dados.csv template.html --output certificados
```

Para verificar o status da conexão com o servidor:

```
python nepemcert.py server --status
```

### Ajuda

Para obter ajuda sobre os comandos disponíveis:

```
python nepemcert.py --help
```

Para obter ajuda sobre um comando específico:

```
python nepemcert.py generate --help
```

## Estrutura de Diretórios

- `app/`: Módulos principais da aplicação
- `templates/`: Templates HTML para os certificados
- `uploads/`: Arquivos CSV carregados
- `output/`: Certificados PDF gerados
- `config/`: Arquivos de configuração

## Desenvolvimento

Para executar os testes:

```
python run_tests.py --all
```