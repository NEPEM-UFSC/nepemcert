# NEPEM Certificados - Testes

Este projeto utiliza o pytest para testes de unidade e integração da interface CLI e módulos principais.

## Configuração do ambiente de teste

1. Instale as dependências de desenvolvimento:

```
pip install -r requirements-dev.txt
```

2. Execute os testes usando o script `run_tests.py`:

```
python run_tests.py --all
```

## Opções de execução dos testes

- `--unit`: Executa apenas os testes de unidade
- `--integration`: Executa apenas os testes de integração
- `--all`: Executa todos os testes (padrão)
- `--coverage`: Gera relatório de cobertura de código (HTML e terminal)
- `--cli`: Executa apenas os testes relacionados à interface CLI
- `--core`: Executa apenas os testes dos módulos principais
- `--module NOME`: Executa testes de um módulo específico

## Exemplos de uso

```bash
# Executar apenas testes de unidade
python run_tests.py --unit

# Executar apenas testes de integração
python run_tests.py --integration

# Executar todos os testes com relatório de cobertura
python run_tests.py --all --coverage

# Executar apenas testes da interface CLI
python run_tests.py --cli

# Executar testes do módulo de conectividade
python run_tests.py --module connectivity_manager

# Executar testes de unidade da interface CLI com cobertura
python run_tests.py --unit --cli --coverage
```

## Estrutura dos testes

- `tests/unit/`: Testes de unidade para componentes individuais
  - `test_connectivity_manager.py`: Testes para o gerenciador de conectividade
  - `test_csv_manager.py`: Testes para o gerenciador de CSV
  - `test_field_mapper.py`: Testes para o mapeamento de campos
  - `test_pdf_generator.py`: Testes para o gerador de PDF
  - `test_template_manager.py`: Testes para o gerenciador de templates
  - `test_zip_exporter.py`: Testes para o exportador ZIP
  - `test_cli_commands.py`: Testes para os comandos CLI
  
- `tests/integration/`: Testes de integração
  - `test_app_components.py`: Testes integrados dos componentes da aplicação
  - `test_cli_integration.py`: Testes integrados da interface CLI

## Marcadores de teste

Os testes utilizam marcadores do pytest para melhor organização:

- `@pytest.mark.unit`: Testes de unidade
- `@pytest.mark.integration`: Testes de integração
- `@pytest.mark.slow`: Testes que são lentos para executar
- `@pytest.mark.cli`: Testes relacionados à interface CLI

## Cobertura de testes

Após executar `python run_tests.py --coverage`, um relatório de cobertura HTML será gerado na pasta `htmlcov/`.
Abra o arquivo `htmlcov/index.html` em um navegador para visualizar a cobertura de código.

## Executando testes específicos

Para executar um arquivo de teste específico usando pytest diretamente:

```bash
# Executar um arquivo de teste específico
pytest -v tests/unit/test_connectivity_manager.py

# Executar uma função de teste específica
pytest -v tests/unit/test_cli_commands.py::test_cli_help
```
