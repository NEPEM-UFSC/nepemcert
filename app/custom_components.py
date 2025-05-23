import streamlit as st

def card(title, content, icon=None, color="#1E3A8A"):
    """
    Renderiza um card customizado com título, conteúdo e ícone opcional.
    
    Args:
        title: Título do card
        content: Conteúdo do card (pode ser texto ou uma função que retorna elementos Streamlit)
        icon: Ícone opcional (emoji)
        color: Cor do card
    """
    st.markdown(f"""
    <div style="
        border-left: 5px solid {color};
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
        <h3 style="color: {color}; margin-top: 0;">
            {f"{icon} " if icon else ""}{title}
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Se content for uma função, executá-la, caso contrário, mostrar como texto
    if callable(content):
        content()
    else:
        st.markdown(content)

def success_button(label, key=None):
    """Botão personalizado com estilo de sucesso"""
    return st.markdown(f"""
    <style>
    div[data-testid="stButton"][aria-describedby="{key}"] button {{
        background-color: #10b981;
        color: white;
    }}
    div[data-testid="stButton"][aria-describedby="{key}"] button:hover {{
        background-color: #059669;
    }}
    </style>
    """, unsafe_allow_html=True)

def danger_button(label, key=None):
    """Botão personalizado com estilo de perigo/alerta"""
    return st.markdown(f"""
    <style>
    div[data-testid="stButton"][aria-describedby="{key}"] button {{
        background-color: #ef4444;
        color: white;
    }}
    div[data-testid="stButton"][aria-describedby="{key}"] button:hover {{
        background-color: #dc2626;
    }}
    </style>
    """, unsafe_allow_html=True)

def info_box(message, type="info"):
    """
    Cria uma caixa de informação mais bonita que os alertas padrão.
    
    Args:
        message: Mensagem a ser exibida
        type: Tipo de caixa (info, success, warning, error)
    """
    colors = {
        "info": {"bg": "#EFF6FF", "border": "#3B82F6", "icon": "ℹ️"},
        "success": {"bg": "#ECFDF5", "border": "#10B981", "icon": "✅"},
        "warning": {"bg": "#FFFBEB", "border": "#F59E0B", "icon": "⚠️"},
        "error": {"bg": "#FEF2F2", "border": "#EF4444", "icon": "❌"}
    }
    
    style = colors.get(type, colors["info"])
    
    st.markdown(f"""
    <div style="
        background-color: {style['bg']};
        border-left: 5px solid {style['border']};
        border-radius: 4px;
        padding: 15px;
        margin: 10px 0;">
        <div style="display: flex; align-items: center;">
            <div style="font-size: 24px; margin-right: 10px;">{style['icon']}</div>
            <div>{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_title(title, description=None):
    """
    Cria um título de seção estilizado com descrição opcional.
    
    Args:
        title: Título da seção
        description: Descrição opcional
    """
    st.markdown(f"""
    <h2 style="
        color: #1E3A8A;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 8px;
        margin-top: 30px;
        margin-bottom: 5px;
        font-size: 1.5em;">
        {title}
    </h2>
    """, unsafe_allow_html=True)
    
    if description:
        st.markdown(f"""
        <p style="
            color: #6B7280;
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1em;">
            {description}
        </p>
        """, unsafe_allow_html=True)
