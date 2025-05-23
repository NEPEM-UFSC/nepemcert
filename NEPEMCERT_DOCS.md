# NEPEMCERT - Base de Conhecimento

## Visão Geral do Projeto

NEPEMCERT é uma aplicação em linha de comando (CLI) para geração de certificados em lote. O sistema permite gerar certificados em PDF a partir de templates HTML e dados de participantes em arquivos CSV. A aplicação é modular e oferece funcionalidades como temas personalizados, valores padrão para placeholders e exportação em lote.

## Arquitetura do Sistema

O projeto segue uma arquitetura modular, com separação clara de responsabilidades:

### Principais Módulos

1. **Interface CLI (`cli.py` e `nepemcert.py`)**
   - Fornece a interface de linha de comando para interação com o usuário
   - Implementa menus interativos e comandos diretos

2. **Gerenciador de Templates (`app/template_manager.py`)**
   - Gerencia templates HTML
   - Extrai e valida placeholders
   - Renderiza templates com dados

3. **Gerenciador de PDF (`app/pdf_generator.py`)**
   - Converte HTML em PDF usando xhtml2pdf
   - Gerencia a geração de múltiplos certificados em lote

4. **Gerenciador de Parâmetros (`app/parameter_manager.py`)**
   - Gerencia valores padrão para placeholders
   - Gerencia valores específicos para temas
   - Gerencia valores institucionais

5. **Gerenciador de Temas (`app/theme_manager.py`)**
   - Aplica temas aos templates
   - Gerencia estilos e formatação de certificados

### Outros Componentes

- **CSV Manager (`app/csv_manager.py`)**: Gerencia a importação e processamento de dados CSV
- **Field Mapper (`app/field_mapper.py`)**: Mapeia campos do CSV para placeholders no template
- **ZIP Exporter (`app/zip_exporter.py`)**: Exporta múltiplos certificados em um arquivo ZIP
- **Connectivity Manager (`app/connectivity_manager.py`)**: Gerencia conexões com servidores remotos

## Sistema de Placeholders

O sistema utiliza um mecanismo de substituição de placeholders baseado no Jinja2:

### Tipos de Placeholders

1. **Placeholders padrão**: Valores globais que se aplicam a todos os certificados
2. **Placeholders institucionais**: Valores específicos da instituição (ex: coordenador, diretor)
3. **Placeholders temáticos**: Valores específicos para cada tema
4. **Dados do CSV**: Valores específicos para cada certificado (maior prioridade)

### Prioridade de Substituição

Quando múltiplas fontes definem o mesmo placeholder, a ordem de prioridade é:

1. Dados do CSV (maior prioridade)
2. Placeholders do tema
3. Placeholders institucionais
4. Placeholders padrão (menor prioridade)

## Temas e Estilos

O sistema suporta temas personalizáveis que afetam:

1. **Aparência visual**: cores, fontes, tamanhos, bordas
2. **Imagens de fundo**: diferentes para cada tema
3. **Conteúdo textual**: textos específicos para cada tema

### Temas Pré-definidos

- **Clássico**: Design tradicional com cores azuis
- **Moderno**: Design limpo com esquema de cores contemporâneo
- **Minimalista**: Design simplificado com poucos elementos visuais
- **Acadêmico**: Design formal para instituições de ensino

## Fluxo de Trabalho

### Geração de Certificados

1. Selecionar arquivo CSV com dados dos participantes
2. Selecionar template HTML para certificados
3. Opcionalmente, selecionar um tema
4. Configurar diretório de saída
5. Gerar certificados em PDF
6. Opcionalmente, exportar em ZIP

### Gerenciamento de Configurações

O sistema permite configurar:

1. **Valores institucionais**: informações constantes da instituição
2. **Valores padrão**: texto e formatação padrão para todos os certificados
3. **Valores temáticos**: configurações específicas para cada tema

## Formato do Template

Os templates HTML usam a sintaxe do Jinja2 para placeholders:

```html
<div class="certificate">
    <h1>{{ title_text }}</h1>
    <p>{{ intro_text }} <span class="name">{{ nome }}</span> {{ participation_text }} <strong>{{ evento }}</strong></p>
</div>
```

### Placeholders padrão disponíveis

```json
{
    "background_image": "URL da imagem de fundo",
    "title_text": "Texto do título principal",
    "title_font_size": "Tamanho da fonte do título",
    "title_color": "Cor do título",
    "content_font_size": "Tamanho da fonte do conteúdo",
    "name_font_size": "Tamanho da fonte do nome",
    "name_color": "Cor do nome",
    "intro_text": "Texto introdutório",
    "participation_text": "Texto de participação",
    "location_text": "Texto de localização",
    "date_text": "Texto da data",
    "workload_text": "Texto da carga horária",
    "hours_text": "Texto das horas",
    "coordinator_title": "Título do coordenador",
    "director_title": "Título do diretor"
}
```

## Formato de Dados CSV

O sistema aceita arquivos CSV com as seguintes especificidades:

1. O arquivo CSV deve conter apenas uma coluna com os nomes dos participantes
2. O evento, local, data e carga horária são informados interativamente
3. A ordem do fluxo é:
   - Usuário seleciona "gerar certificado" → "gerar em lote"
   - Passa o caminho do CSV com os participantes
   - Sistema pergunta se o arquivo tem cabeçalho:
     - Se sim, ignora a primeira linha
     - Se não, processa desde a primeira linha
   - Verifica se o arquivo possui apenas uma coluna:
     - Mais que uma: exibe erro
     - Uma: informa o número de participantes e continua
   - Pergunta:
     - Nome do evento
     - Data
     - Local
     - Carga horária
   - Exibe tudo para revisão:
     - Se desejar trocar: exibe menu para selecionar qual informação alterar
   - Pergunta qual tema será usado
   - Revisa parâmetros fixos: nome do coordenador, site de autenticação etc.
   - Após confirmação: inicia a geração de certificados
     - Neste momento, gera um código de autenticação para cada participante
     - O envio para o servidor ainda não está implementado

Formato do CSV de exemplo:
```
csv
nome
"Maria Silva"
"João Pereira"
"Ana Souza"
```

## Comandos CLI Disponíveis

```bash
# Modo interativo
python nepemcert.py interactive

# Gerar certificados diretamente
python nepemcert.py generate <csv_file> <template> --output <output_dir> --zip

# Gerenciar configurações
python nepemcert.py config

# Gerenciar conectividade com servidor
python nepemcert.py server --status
```

## Arquivos de Configuração

### parameters.json

Contém valores padrão para placeholders:

```json
{
    "default_placeholders": { /* valores padrão */ },
    "theme_placeholders": { 
        "theme_name": { /* valores específicos do tema */ }
    },
    "institutional_placeholders": { /* valores institucionais */ }
}
```

## Dicas para Uso Avançado

1. **Mapeamento de Campos Personalizado**:
   - É possível criar mapeamentos personalizados de campos CSV para placeholders

2. **Valores Condicionais**:
   - O sistema suporta lógica condicional nos templates usando Jinja2

3. **Temas Personalizados**:
   - Crie seus próprios temas definindo estilos e valores padrão

4. **Otimização para Lote**:
   - O sistema é otimizado para processar grandes volumes de certificados

## Troubleshooting

### Problemas Comuns

1. **Placeholders não substituídos**:
   - Verifique se os nomes no CSV correspondem exatamente aos placeholders no template
   - Verifique se os placeholders estão no formato correto: `{{ placeholder }}`

2. **Erros de renderização PDF**:
   - O xhtml2pdf tem limitações com certas funcionalidades CSS
   - Evite elementos como flexbox, posicionamento absoluto, etc.

3. **Problemas com caracteres especiais**:
   - Certifique-se de que os arquivos CSV estão codificados em UTF-8
