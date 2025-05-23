"""
Aplicativo principal para geração de certificados.
"""
import streamlit as st
import os
from datetime import datetime
import streamlit.components.v1 as components
import pandas as pd
import html

# Importação dos módulos modularizados
from app.template_manager import TemplateManager
from app.csv_manager import CSVManager
from app.pdf_generator import PDFGenerator
from app.field_mapper import FieldMapper
from app.zip_exporter import ZipExporter
from app.theme_manager import ThemeManager
from app.preset_manager import PresetManager

# Inicialização dos gerenciadores
template_manager = TemplateManager()
csv_manager = CSVManager()
pdf_generator = PDFGenerator()
field_mapper = FieldMapper()
zip_exporter = ZipExporter()
theme_manager = ThemeManager()
preset_manager = PresetManager()

# Configurações da página
st.set_page_config(
    page_title="Gerador de Certificados",
    page_icon="🎓",
    layout="wide"
)

# Aplicar estilos personalizados para melhor contraste
st.markdown("""
<style>
    /* Fundo principal branco */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Fontes e cores para melhor contraste */
    body, p, div, span, label {
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #111111;
    }
    
    /* Estilo para cabeçalhos */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Segoe UI', Arial, sans-serif;
        color: #0A1128;
        font-weight: 600;
    }
    
    /* Botões com cores contrastantes */
    .stButton > button {
        background-color: #0A1128;
        color: white;
        border-radius: 6px;
        font-weight: 500;
        border: none;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        background-color: #001F54;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: translateY(-1px);
    }
    
    /* Inputs com texto mais escuro */
    .stTextInput > div > div > input, 
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        color: #111111;
    }
    
    /* Sidebar com fundo mais claro */
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    
    /* Texto da sidebar com contraste apropriado */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] div {
        color: #0A1128;
    }
    
    /* Upload de arquivos com borda visível */
    .stFileUploader > div:first-child {
        border: 2px dashed #0A1128;
        border-radius: 8px;
        padding: 20px 10px;
        text-align: center;
    }
    
    /* Expander com cores de contraste */
    .streamlit-expanderHeader {
        color: #0A1128;
        background-color: #e0e5ec;
        font-weight: 500;
    }
    
    /* Radio button, checkbox e outros elementos interativos */
    .stRadio > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
        color: #111111;
    }
    
    /* Code blocks com cores mais visíveis */
    code {
        color: #0A1128 !important;
        background-color: #f0f2f6 !important;
    }
    
    /* Cores para mensagens */
    .element-container div[data-testid="stAlert"] p {
        color: #111111 !important;
    }
    
    /* Tabs com contraste adequado */
    .stTabs [data-baseweb="tab"] {
        background-color: #e0e5ec;
        color: #0A1128;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0A1128 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Criar diretórios necessários
os.makedirs("uploads", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("presets", exist_ok=True)
os.makedirs("themes", exist_ok=True)

# Interface de usuário
st.title("🎓 Gerador de Certificados")
st.markdown("Upload de arquivos HTML e CSV para geração de certificados em PDF.")

# Menu lateral para navegação
st.sidebar.title("Operações")
operation = st.sidebar.radio(
    "Escolha uma operação:",
    ["Gerar Certificados", "Editar Template", "Personalizar Tema", "Gerenciar Presets"]
)

# Função auxiliar para renderizar HTML preview
def render_html_preview(html_content, height=600):
    html_content = html.escape(html_content)
    iframe = f"""
    <iframe srcdoc="{html_content}" width="100%" height="{height}px" 
    style="border: 1px solid #0A1128; border-radius: 5px;"></iframe>
    """
    return components.html(iframe, height=height+50)

# Lógica para cada operação
if operation == "Gerar Certificados":
    # Verificar se há um preset ativo
    using_preset = st.session_state.get('using_preset', False)
    active_preset = st.session_state.get('active_preset', None)
    
    if using_preset and active_preset:
        st.info(f"Usando preset: {active_preset.get('name')}")
        
        # Opção para desativar o preset
        if st.button("Desativar Preset"):
            st.session_state.using_preset = False
            st.session_state.active_preset = None
            st.experimental_rerun()
        
        # Carregar automaticamente o template e o CSV (se disponível)
        template_name = active_preset.get('template')
        template_path = os.path.join("templates", template_name)
        
        if os.path.exists(template_path):
            st.success(f"Template carregado: {template_name}")
            
            # Mostrar configurações do preset
            with st.expander("Configurações do preset"):
                st.json(active_preset)
            
            # Carregar automaticamente as demais configurações
            column_key = active_preset.get('column_for_filename')
            fields_to_use = active_preset.get('fields_to_use', [])
            preview_row = active_preset.get('preview_row', 0)
            
            # Solicitar upload do CSV para processamento
            csv_file = st.file_uploader("Escolha um arquivo CSV com os dados", type=["csv"])
            if csv_file:
                try:
                    # Processar o CSV
                    csv_path = csv_manager.save_uploaded_file(csv_file, "uploads")
                    df = pd.read_csv(csv_path)
                    st.success(f"Dados carregados: {len(df)} registros encontrados")
                    
                    # Gerar certificados
                    if st.button("Gerar Certificados"):
                        # Mostrar barra de progresso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Limpar diretório de saída
                        pdf_generator.clean_output_directory()
                        
                        # Gerar certificados
                        pdf_files = []
                        pdf_names = []
                        
                        for i, row in df.iterrows():
                            # Atualizar progresso
                            progress = (i + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processando {i+1} de {len(df)}: {row[column_key]}")
                            
                            # Renderizar o template para este registro
                            html_content = template_manager.render_template(template_name, row.to_dict())
                            
                            # Gerar o PDF
                            pdf_filename = f"{row[column_key].replace(' ', '_')}_{i}.pdf"
                            pdf_path = os.path.join("output", pdf_filename)
                            pdf_generator.generate_pdf(html_content, pdf_path)
                            
                            pdf_files.append(pdf_path)
                            pdf_names.append(pdf_filename)
                        
                        # Criar ZIP com todos os certificados
                        if active_preset["additional_options"].get("create_zip", True):
                            zip_data = zip_exporter.create_zip_from_files(pdf_files)
                            
                            # Botão para download do ZIP
                            st.download_button(
                                "Baixar todos os certificados (ZIP)",
                                zip_data,
                                file_name="certificados.zip",
                                mime="application/zip"
                            )
                        
                        # Mostrar links para certificados individuais
                        st.success(f"{len(pdf_files)} certificados gerados com sucesso!")
                        st.write("### Certificados Gerados")
                        
                        # Mostrar os primeiros 5 certificados com preview
                        for i, (pdf_path, pdf_name) in enumerate(zip(pdf_files[:5], pdf_names[:5])):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**{df.iloc[i][column_key]}**")
                            with col2:
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        f"Baixar PDF",
                                        f,
                                        file_name=pdf_name,
                                        mime="application/pdf",
                                        key=f"pdf_{i}"
                                    )
                        
                        if len(pdf_files) > 5:
                            st.info(f"... e mais {len(pdf_files) - 5} certificados")
                
                except Exception as e:
                    st.error(f"Erro ao gerar certificados: {str(e)}")
                    st.exception(e)
    
    # Interface padrão para geração de certificados
    else:
        # Interface para seleção de template e upload de CSV
        st.subheader("Seleção de Template")
        
        templates_dir = "templates"
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
        
        if not template_files:
            st.warning("Nenhum template encontrado. Primeiro crie ou faça upload de um template.")
        else:
            selected_template = st.selectbox("Selecione um template:", template_files)
            template_path = os.path.join(templates_dir, selected_template)
            
            # Mostrar informações sobre o template
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            
            placeholders = template_manager.extract_placeholders(template_content)
            
            with st.expander("Ver placeholders necessários"):
                st.write("Este template requer os seguintes campos:")
                for p in placeholders:
                    st.write(f"- {p}")
            
            # Upload do CSV
            st.subheader("Dados para os Certificados")
            csv_file = st.file_uploader("Escolha um arquivo CSV com os dados", type=["csv"])
            
            if csv_file:
                # Processar o CSV
                csv_path = csv_manager.save_uploaded_file(csv_file, "uploads")
                try:
                    df = pd.read_csv(csv_path)
                    st.success(f"Dados carregados: {len(df)} registros encontrados")
                    
                    # Validar se o CSV contém os campos necessários
                    csv_columns = df.columns.tolist()
                    missing_fields = [p for p in placeholders if p not in csv_columns]
                    
                    if missing_fields:
                        st.warning("⚠️ Os seguintes campos estão faltando no CSV:")
                        for field in missing_fields:
                            st.write(f"- {field}")
                        st.info("Os certificados ainda podem ser gerados, mas estes campos ficarão vazios.")
                    
                    # Configurações de geração
                    st.subheader("Configurações de Geração")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        column_for_filename = st.selectbox(
                            "Coluna para nomear os arquivos PDF:", 
                            csv_columns
                        )
                    
                    with col2:
                        create_zip = st.checkbox("Criar arquivo ZIP com todos os certificados", value=True)
                    
                    # Preview do primeiro certificado
                    st.subheader("Preview")
                    preview_row_num = st.number_input("Linha para preview:", min_value=0, max_value=len(df)-1, value=0)
                    preview_data = df.iloc[preview_row_num].to_dict()
                    
                    try:
                        # Renderizar o HTML
                        preview_html = template_manager.render_template(selected_template, preview_data)
                        
                        # Mostrar preview
                        with st.expander("Ver HTML renderizado", expanded=False):
                            render_html_preview(preview_html, height=500)
                        
                        # Gerar PDF de preview
                        preview_pdf = pdf_generator.generate_pdf(preview_html, None)
                        
                        # Botão para download do preview
                        st.download_button(
                            "Baixar Preview em PDF",
                            preview_pdf,
                            file_name=f"preview_{preview_data.get(column_for_filename, 'certificado')}.pdf",
                            mime="application/pdf"
                        )
                    
                    except Exception as e:
                        st.error(f"Erro ao gerar preview: {str(e)}")
                    
                    # Botão para gerar todos os certificados
                    if st.button("Gerar Todos os Certificados"):
                        # Mostrar barra de progresso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Limpar diretório de saída
                        pdf_generator.clean_output_directory()
                        
                        # Gerar certificados
                        pdf_files = []
                        pdf_names = []
                        
                        for i, row in df.iterrows():
                            # Atualizar progresso
                            progress = (i + 1) / len(df)
                            progress_bar.progress(progress)
                            status_text.text(f"Processando {i+1} de {len(df)}: {row[column_for_filename]}")
                            
                            # Renderizar o template para este registro
                            html_content = template_manager.render_template(selected_template, row.to_dict())
                            
                            # Gerar o PDF
                            pdf_filename = f"{row[column_for_filename].replace(' ', '_')}_{i}.pdf"
                            pdf_path = os.path.join("output", pdf_filename)
                            pdf_generator.generate_pdf(html_content, pdf_path)
                            
                            pdf_files.append(pdf_path)
                            pdf_names.append(pdf_filename)
                        
                        # Criar ZIP com todos os certificados
                        if create_zip:
                            zip_data = zip_exporter.create_zip_from_files(pdf_files)
                            
                            # Botão para download do ZIP
                            st.download_button(
                                "Baixar todos os certificados (ZIP)",
                                zip_data,
                                file_name="certificados.zip",
                                mime="application/zip"
                            )
                        
                        # Mostrar links para certificados individuais
                        st.success(f"{len(pdf_files)} certificados gerados com sucesso!")
                        
                        # Salvar como preset
                        st.subheader("Salvar como Preset")
                        st.info("Você pode salvar estas configurações como um preset para uso futuro.")
                        
                        preset_name = st.text_input("Nome do preset:")
                        preset_desc = st.text_area("Descrição (opcional):", height=100)
                        
                        if st.button("Salvar Preset") and preset_name:
                            # Criar dados do preset
                            preset_data = {
                                "name": preset_name,
                                "description": preset_desc,
                                "template": selected_template,
                                "csv_columns": csv_columns,
                                "column_for_filename": column_for_filename,
                                "create_zip": create_zip,
                                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # Salvar preset
                            preset_path = preset_manager.save_preset(preset_name, preset_data)
                            st.success(f"Preset '{preset_name}' salvo com sucesso!")
                
                except Exception as e:
                    st.error(f"Erro ao processar o CSV: {str(e)}")
                    st.exception(e)
    
elif operation == "Editar Template":
    st.subheader("Editor de Template HTML")
    
    # Adicionar tab para documentação
    template_tab, docs_tab = st.tabs(["Template", "Documentação"])
    
    with template_tab:
        # Carregar templates existentes ou criar novo
        template_option = st.radio(
            "Deseja usar um template existente ou criar um novo?",
            ["Usar template existente", "Criar novo template"]
        )

        # Área para o CSV de referência para placeholders
        st.subheader("Referência de Colunas CSV (opcional)")
        reference_csv = st.file_uploader("Upload de CSV para referência de campos", type=["csv"], help="Upload de um CSV para facilitar a inserção de placeholders.")
        csv_columns = []
            
        if reference_csv:
            ref_csv_path = csv_manager.save_uploaded_file(reference_csv, "uploads")
            try:
                ref_df = pd.read_csv(ref_csv_path)
                csv_columns = ref_df.columns.tolist()
                st.success(f"CSV de referência carregado: {len(csv_columns)} colunas encontradas")
                with st.expander("Ver colunas disponíveis"):
                    st.write(csv_columns)
            except Exception as e:
                st.error(f"Erro ao ler o CSV: {str(e)}")

        if template_option == "Usar template existente":
            # Listar templates disponíveis
            templates_dir = "templates"
            template_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]

            if not template_files:
                st.warning("Nenhum template encontrado. Faça upload de um template ou crie um novo.")
            else:       
                selected_template = st.selectbox("Selecione um template:", template_files)
                template_path = os.path.join(templates_dir, selected_template)
                        
                with open(template_path, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Extrair placeholders existentes
                existing_placeholders = template_manager.extract_placeholders(template_content)

                # Validar compatibilidade com xhtml2pdf
                html_warnings = template_manager.validate_template_for_xhtml2pdf(template_content)
                if html_warnings:
                    with st.expander("⚠️ Avisos de compatibilidade HTML", expanded=True):
                        st.warning("O template contém elementos que podem não ser bem renderizados pelo gerador de PDF:")
                        for warning in html_warnings:
                            st.write(f"- {warning}")
                        st.info("Recomendação: Para melhor compatibilidade com o gerador de PDF, evite os elementos listados acima.")
                
                # Editor visual de campos
                if csv_columns:
                    st.subheader("Editor de Campos")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### Campos Disponíveis")
                        
                        # Mostrar campos disponíveis no CSV
                        selected_fields = st.multiselect(
                            "Selecione os campos para inserir no template:",
                            csv_columns,
                            default=[col for col in existing_placeholders if col in csv_columns]
                        )

                        # Opção para inserir um placeholder selecionado em uma posição específica
                        insert_field = st.selectbox("Inserir no template:", selected_fields if selected_fields else ["Selecione um campo"])
                        if st.button("Inserir placeholder") and insert_field in csv_columns:
                            placeholder_code = f"{{ {{ {insert_field} }} }}"
                            st.code(placeholder_code, language="html")
                            st.info(f"Copie este código e cole no template onde deseja que o campo '{insert_field}' apareça.")
                        
                    with col2:
                        st.markdown("### Campos usados no template")
                        if existing_placeholders:
                            st.write("Placeholders encontrados:")
                            for placeholder in existing_placeholders:
                                status = "✅" if placeholder in csv_columns else "⚠️"
                                st.write(f"{status} `{{ {{ {placeholder} }} }}`")
                        else:
                            st.write("Nenhum placeholder encontrado no template.")

                        # Verificar campos que estão no template mas não no CSV
                        missing_fields = [p for p in existing_placeholders if p not in csv_columns]
                        if missing_fields and csv_columns:
                            st.warning("⚠️ Os seguintes campos estão no template mas não foram encontrados no CSV:")
                            st.write(", ".join(missing_fields))

                    # Exemplo de como os dados ficariam
                    if csv_columns and len(ref_df) > 0:
                        st.subheader("Visualização de dados")
                        preview_row_num = st.number_input("Linha de exemplo:", min_value=0, max_value=len(ref_df)-1, value=0)
                        example_data = ref_df.iloc[preview_row_num].to_dict()
                        
                        st.markdown("### Dados do CSV (exemplo):")
                        for col in selected_fields:
                            if col in example_data:
                                st.write(f"**{col}:** {example_data[col]}")
                        
                        # Mostrar como os dados substituiriam os placeholders
                        if existing_placeholders:
                            st.markdown("### Exemplo de substituição:")
                            example_html = template_content
                            for col in example_data:
                                placeholder = f"{{ {{ {col} }} }}"
                                if placeholder in example_html:
                                    st.write(f"`{placeholder}` → **{example_data[col]}**")

                # Validar placeholders
                missing_placeholders = template_manager.validate_placeholders_against_csv(existing_placeholders, csv_columns)
                if missing_placeholders:
                    st.warning("⚠️ Os seguintes placeholders no template não têm colunas correspondentes no CSV:")
                    for placeholder in missing_placeholders:
                        st.write(f"- `{{ {{ {placeholder} }} }}` não encontrado no CSV")

                edited_template = st.text_area("Edite o template HTML:", value=template_content, height=400)
                if st.button("Salvar alterações"):
                    with open(template_path, "w", encoding="utf-8") as f:
                        f.write(edited_template)
                    st.success(f"Template '{selected_template}' atualizado com sucesso!")

                # Mostrar ajuda sobre placeholders
                with st.expander("Ajuda sobre placeholders"):
                    st.markdown("""
                    ### Como usar placeholders no template
                    Use a sintaxe `{{ nome_coluna }}` para incluir dados do CSV no seu template.
                    Exemplo:
                    ```html
                    <h1>Certificado de {{ curso }}</h1>
                    <p>Certificamos que <strong>{{ nome }}</strong> concluiu o curso com sucesso.</p>
                    ```
                    Onde `nome` e `curso` são nomes de colunas no seu arquivo CSV.
                    """)

    with docs_tab:
        if template_option == "Usar template existente" and selected_template:
            # Carregar documentação existente
            docs = template_manager.load_template_documentation(selected_template)
            
            st.subheader("Documentação dos Placeholders")
            if docs:
                # Editor de documentação
                edited_docs = {}
                for placeholder in existing_placeholders:
                    desc = docs.get(placeholder, "")
                    edited_docs[placeholder] = st.text_input(
                        f"Descrição para {placeholder}",
                        value=desc,
                        help="Descreva o propósito deste placeholder"
                    )
                
                if st.button("Salvar Documentação"):
                    template_manager.save_template_documentation(selected_template, edited_docs)
                    st.success("Documentação atualizada com sucesso!")
                
                # Validação
                validation = template_manager.validate_template_with_docs(template_content, edited_docs)
                if not validation["valid"]:
                    if validation["missing_docs"]:
                        st.warning(f"Placeholders sem documentação: {', '.join(validation['missing_docs'])}")
                    if validation["extra_docs"]:
                        st.info(f"Documentação para placeholders não utilizados: {', '.join(validation['extra_docs'])}")
            else:
                st.info("Nenhuma documentação encontrada para este template. Crie uma nova.")
                if st.button("Gerar Estrutura de Documentação"):
                    new_docs = {p: "" for p in existing_placeholders}
                    template_manager.save_template_documentation(selected_template, new_docs)
                    st.success("Estrutura de documentação criada! Recarregue a página para editar.")

        else:  # Criar novo template
            new_template_name = st.text_input("Nome do novo template (com extensão .html):")
            if not new_template_name:
                st.info("Digite um nome para o template.")
            elif not new_template_name.endswith('.html'):
                st.warning("O nome do template deve terminar com .html")
            else:
                # Template básico para iniciar
                default_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Certificado</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 40px;
            border: 5px solid #gold;
        }
        h1 {
            color: #1a5276;
        }
        .certificate {
            padding: 20px;
            margin: 20px auto;
            max-width: 800px;
        }
        .recipient {
            font-size: 24px;
            font-weight: bold;
            margin: 20px 0;
        }
        .date {
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="certificate">
        <h1>CERTIFICADO</h1>
        <p>Este certificado é concedido a</p>
        <p class="recipient">{{ nome }}</p>
        <p>pela conclusão do curso</p>
        <h2>{{ curso }}</h2>
        <p>com carga horária de {{ carga_horaria }} horas.</p>
        <p class="date">{{ data }}</p>
    </div>
</body>
</html>"""
            edited_template = st.text_area("Edite o template HTML:", value=default_template, height=400)

            # Adicionar o auxiliar de campos se houver CSV carregado
            if csv_columns:
                st.subheader("Inserir Campos")
                selected_field = st.selectbox("Selecione um campo para inserir:", csv_columns)
                
                if st.button("Gerar código do placeholder"):
                    placeholder_code = f"{{ {{ {selected_field} }} }}"
                    st.code(placeholder_code, language="html")
                    st.info(f"Copie este código e cole no template onde deseja que o campo '{selected_field}' apareça.")
                
                # Preview de dados
                if len(ref_df) > 0:
                    st.subheader("Exemplo de dados")
                    example_row = st.number_input("Linha de exemplo:", min_value=0, max_value=len(ref_df)-1, value=0)
                    st.write(ref_df.iloc[example_row])

            # Validar compatibilidade com xhtml2pdf
            html_warnings = template_manager.validate_template_for_xhtml2pdf(edited_template)
            if html_warnings:
                with st.expander("⚠️ Avisos de compatibilidade HTML", expanded=True):
                    st.warning("O template contém elementos que podem não ser bem renderizados pelo gerador de PDF:")
                    for warning in html_warnings:
                        st.write(f"- {warning}")

            # Extrair e validar placeholders se CSV disponível
            if csv_columns:
                placeholders = template_manager.extract_placeholders(edited_template)
                missing_placeholders = template_manager.validate_placeholders_against_csv(placeholders, csv_columns)
                if missing_placeholders:
                    st.warning("⚠️ Os seguintes placeholders no template não têm colunas correspondentes no CSV:")
                    for placeholder in missing_placeholders:
                        st.write(f"- `{{ {{ {placeholder} }} }}` não encontrado no CSV")

            if st.button("Salvar novo template"):
                template_path = os.path.join("templates", new_template_name)
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(edited_template)
                st.success(f"Novo template '{new_template_name}' criado com sucesso!")

elif operation == "Personalizar Tema":
    st.subheader("Personalização de Temas para Certificados")

    # Carregar templates disponíveis
    templates_dir = "templates"
    template_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]

    if not template_files:
        st.warning("Nenhum template encontrado. Crie ou faça upload de um template primeiro.")
    else:
        selected_template = st.selectbox("Selecione um template para personalizar:", template_files)
        template_path = os.path.join(templates_dir, selected_template)
                
        with open(template_path, "r", encoding="utf-8") as f:
            original_template = f.read()
                
        # Criar diretórios para imagens de fundo se não existirem
        backgrounds_dir = os.path.join("templates", "backgrounds")
        os.makedirs(backgrounds_dir, exist_ok=True)
                
        st.subheader("Opções de Personalização")
                
        # Dividir a tela em colunas
        col1, col2 = st.columns([1, 1])
                
        # Coluna de configurações
        with col1:
            # Opções de fontes
            font_family = st.selectbox(
                "Fonte principal:",
                ["Arial, sans-serif", "Times New Roman, serif", "Courier New, monospace", 
                 "Georgia, serif", "Verdana, sans-serif", "Tahoma, sans-serif"]
            )
                        
            # Cores
            heading_color = st.color_picker("Cor dos títulos:", "#1a5276")
            text_color = st.color_picker("Cor do texto:", "#333333")
            background_color = st.color_picker("Cor de fundo:", "#ffffff")
            border_color = st.color_picker("Cor da borda:", "#dddddd")
                        
            # Tamanhos e margens
            heading_size = st.select_slider("Tamanho dos títulos:",
                                            options=["24px", "28px", "32px", "36px", "40px", "48px"],
                                            value="32px")
            text_size = st.select_slider("Tamanho do texto:",
                                         options=["14px", "16px", "18px", "20px", "22px", "24px"],
                                         value="16px")
            margin = st.slider("Margem (px):", 0, 100, 40)
            border_width = st.slider("Espessura da borda (px):", 0, 10, 1)
                        
            # Upload de imagem de fundo
            st.subheader("Imagem de fundo")
            bg_type = st.radio("Tipo de fundo:", ["Cor sólida", "Imagem de fundo"])
            bg_image_base64 = None
                        
            if bg_type == "Imagem de fundo":
                bg_file = st.file_uploader("Upload de imagem de fundo:", type=['png', 'jpg', 'jpeg'])
                if bg_file:
                    bg_image_base64 = template_manager.get_image_as_base64(bg_file)
                    st.success("Imagem de fundo carregada!")
                        
            # Criar dicionário de configurações do tema
            theme_settings = {
                "font_family": font_family,
                "heading_color": heading_color,
                "text_color": text_color,
                "background_color": background_color,
                "border_color": border_color,
                "border_width": f"{border_width}px",
                "margin": f"{margin}px",
                "heading_size": heading_size,
                "text_size": text_size,
                "background_image": bg_image_base64
            }
                        
            # Botão para aplicar o tema
            if st.button("Aplicar Tema ao Template"):
                themed_template = theme_manager.apply_theme_to_template(original_template, theme_settings)
                # Salvar template com tema aplicado
                themed_template_name = f"themed_{selected_template}"
                themed_template_path = os.path.join(templates_dir, themed_template_name)
                                
                with open(themed_template_path, "w", encoding="utf-8") as f:
                    f.write(themed_template)
                                
                st.success(f"Tema aplicado e salvo como '{themed_template_name}'!")
                
        # Coluna de preview
        with col2:
            st.subheader("Preview do Template com Tema")
                        
            # Aplicar o tema ao template
            themed_template = theme_manager.apply_theme_to_template(original_template, theme_settings)
                        
            # Dados fictícios para preview
            sample_data = {
                "nome": "Nome do Participante",
                "evento": "Nome do Evento",
                "data": "01/01/2023",
                "local": "Local do Evento",
                "carga_horaria": "20",
                "coordenador": "Coordenador do Evento",
                "diretor": "Diretor da Instituição",
                "cidade": "Cidade",
                "data_emissao": "10/01/2023"
            }
                        
            # Para placeholders que não estão no sample_data
            placeholders = template_manager.extract_placeholders(original_template)
            for placeholder in placeholders:
                if placeholder not in sample_data:
                    sample_data[placeholder] = f"Exemplo de {placeholder}"
                        
            # Renderizar o template com dados fictícios
            try:
                # Salvar template temporário
                temp_dir = "temp"
                os.makedirs(temp_dir, exist_ok=True)
                temp_file = os.path.join(temp_dir, "temp_preview.html")
                                
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(themed_template)
                                
                # Renderizar template
                preview_html = template_manager.render_template(temp_file, sample_data)
                                
                # Mostrar preview interativo
                render_html_preview(preview_html)
                                
                # Opção para download do PDF com tema aplicado
                preview_pdf = pdf_generator.generate_pdf(preview_html, None)
                st.download_button(
                    "Download do PDF com este tema", 
                    preview_pdf, 
                    file_name="preview_tema.pdf", 
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro ao gerar preview: {str(e)}")
                st.info("Verifique se o template HTML é válido e se todos os placeholders correspondem aos dados.")
                
            # Exibir o código HTML gerado
            with st.expander("Ver código HTML com tema aplicado"):
                st.code(themed_template, language="html")

elif operation == "Gerenciar Presets":
    st.title("Gerenciamento de Presets")
    
    # Tabs para organizar as funcionalidades
    preset_tab = st.tabs(["Criar Preset", "Carregar Preset", "Excluir Preset"])
    
    # Tab para criar presets
    with preset_tab[0]:
        st.subheader("Criar Novo Preset")
                
        # Campos para configuração do preset
        preset_name = st.text_input("Nome do Preset:")
        preset_description = st.text_area("Descrição (opcional):", height=100)
                
        # Seleção de template
        templates_dir = "templates"
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
                
        if not template_files:
            st.warning("Nenhum template encontrado. Crie ou faça upload de um template primeiro.")
        else:
            selected_template = st.selectbox("Selecione um template:", template_files)
                        
            # Selecionar arquivo CSV para referência
            st.subheader("Dados de Referência (opcional)")
            csv_file = st.file_uploader("Escolha um arquivo CSV de referência", type=["csv"])
                        
            csv_columns = []
            if csv_file:
                csv_path = csv_manager.save_uploaded_file(csv_file, "uploads")
                try:
                    df = pd.read_csv(csv_path)
                    csv_columns = df.columns.tolist()
                    st.success(f"CSV carregado: {len(csv_columns)} colunas encontradas")
                                        
                    # Configuração de campos
                    st.subheader("Configuração de Campos")
                    column_for_filename = st.selectbox("Coluna para nomear os arquivos PDF:", csv_columns)
                    fields_to_use = st.multiselect("Campos para usar no certificado:", csv_columns, default=csv_columns)
                                        
                    # Opções adicionais
                    st.subheader("Opções Adicionais")
                    additional_options = {
                        "pdf_orientation": st.radio("Orientação do PDF:", ["Paisagem", "Retrato"]),
                        "include_timestamp": st.checkbox("Incluir data/hora no nome do arquivo", value=True),
                        "create_individual_pdfs": st.checkbox("Criar PDFs individuais", value=True),
                        "create_zip": st.checkbox("Criar arquivo ZIP", value=True)
                    }
                                        
                    # Preview row para definir linha de exemplo
                    if len(df) > 0:
                        preview_row = st.number_input("Linha de preview:", min_value=0, max_value=len(df)-1, value=0)
                    else:
                        preview_row = 0
                    
                    # Botão para salvar preset
                    if st.button("Salvar Preset"):
                        if not preset_name:
                            st.error("Por favor, insira um nome para o preset.")
                        else:
                            # Criar dicionário com dados do preset
                            preset_data = {
                                "name": preset_name,
                                "description": preset_description,
                                "template": selected_template,
                                "csv_columns": csv_columns,
                                "column_for_filename": column_for_filename,
                                "fields_to_use": fields_to_use,
                                "preview_row": int(preview_row),
                                "additional_options": additional_options,
                                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            # Salvar preset
                            preset_path = preset_manager.save_preset(preset_name, preset_data)
                            st.success(f"Preset '{preset_name}' salvo com sucesso!")
                            
                except Exception as e:
                    st.error(f"Erro ao processar o CSV: {str(e)}")
    
    # Tab para carregar presets
    with preset_tab[1]:
        st.subheader("Carregar Preset Existente")
        
        # Listar presets disponíveis
        available_presets = preset_manager.list_presets()
        
        if not available_presets:
            st.info("Nenhum preset encontrado. Crie um preset primeiro.")
        else:
            selected_preset_name = st.selectbox("Selecione um preset:", available_presets)
            
            # Carregar o preset selecionado
            preset_data = preset_manager.load_preset(selected_preset_name)
            
            if preset_data:
                # Exibir informações do preset
                st.subheader("Informações do Preset")
                st.write(f"**Nome:** {preset_data.get('name')}")
                st.write(f"**Descrição:** {preset_data.get('description', 'Sem descrição')}")
                st.write(f"**Template:** {preset_data.get('template')}")
                st.write(f"**Criado em:** {preset_data.get('created', 'Data desconhecida')}")
                
                # Exibir configurações do preset
                with st.expander("Ver detalhes completos"):
                    st.json(preset_data)
                
                # Botão para usar este preset
                if st.button("Usar Este Preset"):
                    # Armazenar na sessão
                    st.session_state.active_preset = preset_data
                    st.session_state.using_preset = True
                    
                    # Redirecionar para a página de geração
                    st.success("Preset carregado! Vá para a seção 'Gerar Certificados' para usá-lo.")
                    st.info("As configurações deste preset serão aplicadas automaticamente.")
    
    # Tab para excluir presets
    with preset_tab[2]:
        st.subheader("Excluir Preset")
        
        # Listar presets disponíveis
        available_presets = preset_manager.list_presets()
        
        if not available_presets:
            st.info("Nenhum preset encontrado para excluir.")
        else:
            preset_to_delete = st.selectbox("Selecione um preset para excluir:", available_presets)
            
            # Obter informações do preset
            preset_info = preset_manager.get_preset_info(preset_to_delete)
            
            if preset_info:
                st.write(f"**Nome:** {preset_info.get('name')}")
                st.write(f"**Template:** {preset_info.get('template')}")
                st.write(f"**Número de campos:** {preset_info.get('csv_columns')}")
                
                # Confirmação de exclusão
                if st.button("Excluir Preset", key="delete_preset"):
                    confirm = st.checkbox("Confirmar exclusão?")
                    
                    if confirm:
                        success = preset_manager.delete_preset(preset_to_delete)
                        if success:
                            st.success(f"Preset '{preset_to_delete}' excluído com sucesso!")
                        else:
                            st.error("Erro ao excluir preset.")
