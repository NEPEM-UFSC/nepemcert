# NEPEMCERT: Guia para Criação de Temas

Este documento fornece orientações para criação e personalização de temas para o sistema NEPEMCERT de geração de certificados.

## Sobre os Temas

Os temas no NEPEMCERT permitem personalizar a aparência visual dos certificados gerados, modificando cores, fontes e elementos decorativos sem alterar a estrutura ou o layout do certificado.

## Estrutura de um Tema

Um tema é definido em um arquivo JSON com extensão `.json` na pasta `themes/`. Cada tema contém propriedades específicas que controlam a aparência visual do certificado.

### Exemplo de Estrutura de Tema

```json
{
  "font_family": "Times, 'Times New Roman', serif",
  "heading_color": "#003366",
  "text_color": "#333333",
  "background_color": "#fffff8",
  "border_color": "#8c7853",
  "border_width": "4px",
  "border_style": "double",
  "name_color": "#003366",
  "title_color": "#003366",
  "event_name_color": "#003366",
  "link_color": "#003366",
  "title_text": "Certificado de Excelência",
  "intro_text": "Certifica-se que",
  "participation_text": "participou com distinção do evento",
  "footer_style": "classic",
  "signature_color": "#000033",
  "background_image": null
}
```

## Propriedades Permitidas em um Tema

### Propriedades Visuais (Cores e Estilos)

| Propriedade | Descrição | Exemplo |
|-------------|-----------|---------|
| `font_family` | Define a família de fonte principal | `"Arial, sans-serif"` |
| `heading_color` | Cor dos cabeçalhos | `"#1a5276"` |
| `text_color` | Cor do texto principal | `"#333333"` |
| `background_color` | Cor de fundo do certificado | `"#ffffff"` |
| `border_color` | Cor da borda do certificado | `"#dddddd"` |
| `border_width` | Largura da borda | `"4px"` |
| `border_style` | Estilo da borda (solid, dashed, dotted, double) | `"solid"` |
| `name_color` | Cor do nome do participante | `"#1a4971"` |
| `title_color` | Cor do título do certificado | `"#1a5276"` |
| `event_name_color` | Cor do nome do evento | `"#1a5276"` |
| `link_color` | Cor dos links no certificado | `"#1a5276"` |
| `signature_color` | Cor da assinatura | `"#333333"` |
| `footer_style` | Estilo do rodapé (classic, modern, minimalist, formal, clean) | `"classic"` |

### Propriedades de Conteúdo (Textos Padrão)

| Propriedade | Descrição | Exemplo |
|-------------|-----------|---------|
| `title_text` | Texto do título do certificado | `"CERTIFICADO DE PARTICIPAÇÃO"` |
| `intro_text` | Texto introdutório antes do nome | `"Certificamos que"` |
| `participation_text` | Texto após o nome | `"participou do evento"` |

### Propriedade de Imagem de Fundo

| Propriedade | Descrição | Exemplo |
|-------------|-----------|---------|
| `background_image` | Imagem de fundo codificada em base64 ou null | `null` |

## ⚠️ Restrições Importantes

1. **Não altere o tamanho das fontes** - Isso pode quebrar o layout do certificado. As seguintes propriedades **NÃO** devem ser incluídas no tema:
   - `title_font_size`
   - `content_font_size`
   - `name_font_size`
   - `signature_text_size`
   - `heading_size`
   - `text_size`
   - `margin`

2. **Não modifique o posicionamento dos elementos** - O sistema mantém o posicionamento original do template.

## Como Criar um Novo Tema

### Método 1: Usar a Interface do NEPEMCERT

1. Execute o NEPEMCERT em modo interativo
2. Selecione a opção "Gerenciar temas"
3. Escolha "Criar novo tema"
4. Siga as instruções para personalizar as cores e fontes

### Método 2: Criar Manualmente

1. Crie um arquivo JSON na pasta `themes/`
2. Nomeie o arquivo com padrão snake_case, por exemplo: `meu_tema_personalizado.json`
3. Edite o arquivo com as propriedades desejadas (veja o exemplo acima)
4. Reinicie o NEPEMCERT para que o tema seja carregado

### Usar um Tema Existente como Base

Uma boa prática é começar a partir de um tema existente:

1. Copie um dos arquivos de tema em `themes/`
2. Renomeie-o com um novo nome
3. Modifique as propriedades desejadas
4. Salve o arquivo

## Famílias de Fontes Suportadas

É recomendável usar apenas fontes seguras que estão disponíveis em todos os sistemas:

- `"Arial, sans-serif"`
- `"Helvetica, Arial, sans-serif"`
- `"Times, 'Times New Roman', serif"`
- `"Palatino, 'Times New Roman', serif"`
- `"Georgia, serif"`
- `"Courier, monospace"`

## Cores

As cores podem ser definidas em formato hexadecimal (#RRGGBB) ou usando nomes de cores CSS:

- Hexadecimal: `"#1a5276"`
- Nome da cor: `"blue"`, `"red"`, etc.

## Exemplos de Temas

O sistema vem com vários temas pré-definidos que você pode usar como referência:

1. **Acadêmico Clássico** (`academico_classico.json`) - Estilo formal para certificados acadêmicos
2. **Contemporâneo Elegante** (`contemporaneo_elegante.json`) - Design moderno com cores suaves
3. **Diplomático Oficial** (`diplomatico_oficial.json`) - Aparência oficial e solene
4. **Executivo Premium** (`executivo_premium.json`) - Estilo corporativo profissional
5. **Minimalista Moderno** (`minimalista_moderno.json`) - Design clean e minimalista

## Solução de Problemas

Se você encontrar problemas com seus temas:

1. **Verifique o formato JSON** - Certifique-se de que o JSON é válido
2. **Use apenas propriedades permitidas** - Evite adicionar propriedades que alteram o layout
3. **Use fontes seguras** - Escolha apenas fontes que estão amplamente disponíveis

## Testando seu Tema

Após criar um tema, você pode testá-lo usando o modo de depuração:

```
python nepemcert.py debug-themes templates/certificado_v1_basico.html
```

Isso irá gerar certificados com todos os temas disponíveis, incluindo o seu novo tema.
