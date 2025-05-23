import os
import sys
import importlib
import streamlit as st

st.set_page_config(
    page_title="Diagnóstico do Sistema",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Diagnóstico do Sistema")
st.write("Esta ferramenta verifica a estrutura do projeto e as dependências.")

# Verificar estrutura de diretórios
st.subheader("Estrutura de Diretórios")
base_dir = os.path.dirname(os.path.abspath(__file__))
st.write(f"Diretório base: {base_dir}")

# Listar diretórios e arquivos
def list_files(directory, level=0):
    result = []
    try:
        for item in os.listdir(directory):
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                result.append(("📁" + "  " * level) + item)
                result.extend(list_files(path, level + 1))
            else:
                result.append(("📄" + "  " * level) + item)
    except Exception as e:
        result.append(f"Erro ao listar {directory}: {str(e)}")
    return result

files = list_files(base_dir)
st.code("\n".join(files))

# Verificar módulos Python
st.subheader("Verificação de Módulos")
modules_to_check = [
    "app.template_manager", 
    "app.csv_manager", 
    "app.pdf_generator", 
    "app.field_mapper",
    "app.zip_exporter", 
    "app.theme_manager", 
    "app.preset_manager"
]

for module_name in modules_to_check:
    try:
        # Tenta importar o módulo
        importlib.import_module(module_name)
        st.success(f"✅ Módulo '{module_name}' importado com sucesso!")
    except ImportError as e:
        st.error(f"❌ Erro ao importar '{module_name}': {str(e)}")
        
        # Verificar se o arquivo existe
        module_path = module_name.replace(".", os.path.sep) + ".py"
        full_path = os.path.join(base_dir, module_path)
        if os.path.exists(full_path):
            st.info(f"O arquivo existe em: {full_path}")
        else:
            st.warning(f"Arquivo não encontrado: {full_path}")

# Verificar Python Path
st.subheader("Python Path")
for path in sys.path:
    st.write(path)

# Sugestões de correção
st.subheader("Possíveis Soluções")
st.markdown("""
1. **Verifique se todos os arquivos de módulo estão no diretório correto**
   - Todos os módulos (template_manager.py, etc.) devem estar no diretório `app/`

2. **Crie um arquivo `__init__.py` no diretório `app/`**
   - Para que o Python reconheça o diretório como um pacote

3. **Verifique se as importações nos módulos estão corretas**
   - Use importações relativas (`from . import xyz`) para módulos dentro do mesmo pacote

4. **Execute a aplicação com o comando correto**
   - Use `streamlit run diagnose.py` para executar esta ferramenta de diagnóstico
   - Use `streamlit run run.py` para executar a aplicação principal
""")

# Botão para tentar corrigir automaticamente
if st.button("Tentar Correção Automática"):
    # Criar __init__.py se não existir
    init_path = os.path.join(base_dir, "app", "__init__.py")
    if not os.path.exists(os.path.dirname(init_path)):
        os.makedirs(os.path.dirname(init_path), exist_ok=True)
        
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            f.write("# Este arquivo marca o diretório como um pacote Python")
        st.success(f"Criado arquivo __init__.py em {init_path}")
    else:
        st.info(f"Arquivo __init__.py já existe em {init_path}")
    
    st.info("Correção automática concluída. Tente executar a aplicação novamente.")

# Adicionar teste de renderização básica do Streamlit
st.subheader("Teste de Renderização do Streamlit")
st.write("Esta seção verifica se o Streamlit está funcionando corretamente.")

# Teste de componentes básicos do Streamlit
st.write("Testando componentes básicos:")

with st.expander("Teste de componentes interativos"):
    st.checkbox("Teste de checkbox")
    st.radio("Teste de radio", options=["Opção 1", "Opção 2"])
    st.selectbox("Teste de selectbox", options=["Selecione uma opção", "Opção 1", "Opção 2"])
    st.slider("Teste de slider", 0, 100, 50)
    st.button("Teste de botão")

# Verificar conteúdo do app.py
st.subheader("Conteúdo do arquivo app.py")
app_path = os.path.join(base_dir, "app", "app.py")

if os.path.exists(app_path):
    try:
        with open(app_path, "r", encoding="utf-8") as f:
            app_content = f.read()
            
        st.code(app_content[:1000] + "... [conteúdo truncado]" if len(app_content) > 1000 else app_content, language="python")
        
        # Verificar se há função main() no app.py
        if "def main():" in app_content:
            st.success("Função 'main()' encontrada no arquivo app.py!")
        else:
            st.warning("Função 'main()' não encontrada no arquivo app.py!")
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo app.py: {str(e)}")
else:
    st.error(f"Arquivo app.py não encontrado em: {app_path}")

# Botão para criar uma aplicação Streamlit mínima
if st.button("Criar aplicação mínima de teste"):
    minimal_app_path = os.path.join(base_dir, "minimal_app.py")
    minimal_content = """import streamlit as st

st.set_page_config(
    page_title="Aplicação Mínima",
    page_icon="🔬",
    layout="wide"
)

def main():
    st.title("🔬 Aplicação Streamlit Mínima")
    st.write("Se você está vendo esta página, o Streamlit está funcionando corretamente!")
    
    # Teste de componentes interativos
    option = st.selectbox("Selecione uma opção:", ["Opção 1", "Opção 2", "Opção 3"])
    st.write(f"Você selecionou: {option}")
    
    if st.button("Clique em mim!"):
        st.success("Botão clicado com sucesso!")

if __name__ == "__main__":
    main()
"""
    
    with open(minimal_app_path, "w", encoding="utf-8") as f:
        f.write(minimal_content)
        
    st.success(f"Aplicação mínima criada em: {minimal_app_path}")
    st.info("Execute `streamlit run minimal_app.py` para testar.")

# Botão para modificar run.py
if st.button("Modificar run.py para modo de depuração"):
    run_path = os.path.join(base_dir, "run.py")
    debug_run_content = """import os
import sys
import streamlit as st

# Adiciona o diretório atual ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configuração da página
st.set_page_config(
    page_title="Modo de Depuração",
    page_icon="🐞",
    layout="wide"
)

# Interface de depuração
st.title("🐞 Modo de Depuração")
st.write("Esta é uma versão simplificada da aplicação para fins de depuração.")

try:
    # Tenta importar componentes individuais
    st.subheader("Importando componentes individuais...")
    
    with st.expander("Detalhes das importações"):
        try:
            st.write("Importando TemplateManager...")
            from app.template_manager import TemplateManager
            st.success("✅ TemplateManager importado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao importar TemplateManager: {str(e)}")
            
        try:
            st.write("Importando CSVManager...")
            from app.csv_manager import CSVManager
            st.success("✅ CSVManager importado com sucesso!")
        except Exception as e:
            st.error(f"❌ Erro ao importar CSVManager: {str(e)}")
            
        # Adicione outros componentes conforme necessário
    
    # Interface básica
    st.subheader("Interface Básica")
    st.write("Se você está vendo isto, o Streamlit está funcionando corretamente!")
    
    # Adicione algumas funcionalidades básicas
    operation = st.sidebar.radio(
        "Escolha uma operação:",
        ["Opção 1", "Opção 2", "Opção 3"]
    )
    
    st.write(f"Você selecionou: {operation}")
    
    if st.button("Clique em mim!"):
        st.success("Botão clicado com sucesso!")
        
except Exception as e:
    st.error(f"Erro durante a execução: {str(e)}")
    st.exception(e)
"""
    
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(debug_run_content)
        
    st.success(f"Arquivo run.py modificado para modo de depuração!")
    st.info("Execute `streamlit run run.py` para testar.")

# Verificar versões
st.subheader("Informações do Ambiente")
st.write(f"Python: {sys.version}")
try:
    import streamlit
    st.write(f"Streamlit: {streamlit.__version__}")
except:
    st.error("Não foi possível determinar a versão do Streamlit.")
