import os
import sys

# Adiciona o diretório atual ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa a aplicação Streamlit
import streamlit as st

# Configurações para deixar o Streamlit mais bonito
st.set_page_config(
    page_title="Gerador de Certificados",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplica o tema personalizado
def apply_custom_style():
    # CSS para melhorar a aparência da interface
    st.markdown("""
    <style>
        /* Fundo principal branco */
        .stApp {
            background-color: #ffffff;
        }
        
        /* Estilo para cabeçalhos com melhor contraste */
        h1, h2, h3 {
            color: #0A1128;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 600;
        }
        
        /* Estilo para o texto normal com maior contraste */
        p, div, label, .stMarkdown {
            color: #1A1A1A;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Estilo para botões */
        .stButton > button {
            background-color: #0A1128;
            color: white;
            border-radius: 6px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            background-color: #001F54;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            transform: translateY(-1px);
        }
        
        /* Estilo para caixas de seleção e inputs */
        .stSelectbox, .stMultiSelect {
            border-radius: 6px;
            color: #1A1A1A;
        }
        
        /* Estilo para radio buttons */
        .stRadio > div {
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 6px;
            margin-bottom: 10px;
            color: #1A1A1A;
        }
        
        /* Estilo para expanders */
        .streamlit-expanderHeader {
            background-color: #e0e5ec;
            border-radius: 6px;
            padding: 10px !important;
            color: #0A1128;
            font-weight: 500;
        }
        
        /* Estilo para sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {
            background-color: #f0f2f6;
        }
        
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] div {
            color: #0A1128;
        }
        
        /* Estilo para tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #e0e5ec;
            border-radius: 4px 4px 0 0;
            padding: 10px 20px;
            border: none;
            color: #0A1128;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0A1128 !important;
            color: white !important;
        }
        
        /* Estilo para cards/containers */
        div[data-testid="stVerticalBlock"] > div {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }
        
        /* Upload de arquivos mais bonito */
        .stFileUploader > div:first-child {
            border: 2px dashed #0A1128;
            border-radius: 8px;
            padding: 20px 10px;
            text-align: center;
        }
        
        /* Estilo para alerts/info boxes */
        .stAlert {
            padding: 20px;
            border-radius: 8px;
            margin: 10px 0;
        }
        
        /* Barra de progresso */
        .stProgress > div > div {
            background-color: #0A1128;
        }
        
        /* Input text, number, etc */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            color: #1A1A1A;
            font-weight: 500;
        }
        
        /* Melhorar contraste de placeholders */
        ::placeholder {
            color: #696969 !important;
            opacity: 1 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# Aplica o estilo personalizado
apply_custom_style()

# CORRIGIDO: Importação direta do conteúdo do app.py com codificação explícita
try:
    # Executa o arquivo app.py diretamente com a codificação UTF-8
    app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'app.py')
    with open(app_path, 'r', encoding='utf-8') as f:  # Especifica a codificação UTF-8
        exec(f.read())
except Exception as e:
    st.error(f"Erro ao carregar a aplicação: {str(e)}")
    st.exception(e)
    
    # Exibir uma interface mínima para diagnóstico
    st.title("🛠️ Diagnóstico do Gerador de Certificados")
    st.write("Ocorreu um erro ao carregar a aplicação principal. Veja detalhes abaixo:")
    
    # Mostra informações de diagnóstico
    st.subheader("Informações do Sistema")
    st.write(f"Python Path: {sys.path}")
    st.write(f"Diretório atual: {os.getcwd()}")
    
    # Verificar arquivos no diretório app
    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app')
    if os.path.exists(app_dir):
        st.write(f"Arquivos no diretório 'app': {os.listdir(app_dir)}")
    else:
        st.error(f"Diretório 'app' não encontrado em: {app_dir}")

# Verifica se o arquivo está sendo executado diretamente
if __name__ == "__main__":
    # Não é necessário fazer nada aqui, pois o código será executado diretamente pela instrução exec acima
    pass
