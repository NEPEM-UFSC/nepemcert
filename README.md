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