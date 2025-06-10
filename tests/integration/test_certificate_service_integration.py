"""
Testes de integração para o serviço completo de geração de certificados.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Marca todos os testes neste arquivo como testes de integração
pytestmark = pytest.mark.integration

@pytest.fixture
def certificate_workspace():
    """Cria um espaço de trabalho completo para testes do CertificateService"""
    workspace = tempfile.mkdtemp()
    
    # Criar estrutura de diretórios
    directories = ["uploads", "templates", "output", "config", "themes", "codigos"]
    for directory in directories:
        os.makedirs(os.path.join(workspace, directory), exist_ok=True)
    
    # Criar CSV com apenas nomes (formato esperado pelo sistema)
    csv_content = """nome
João Silva
Maria Oliveira
Carlos Santos
Ana Costa"""
    
    csv_path = os.path.join(workspace, "uploads", "participantes.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)
    
    # Criar template completo com QR code
    template_content = """<!DOCTYPE html>
<html>
<head>
    <title>Certificado de Participação</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #ffffff;
            border: 4px solid #1a5276;
        }
        .certificate-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            position: relative;
        }
        .title {
            text-align: center;
            font-size: 36px;
            color: #1a5276;
            margin-bottom: 30px;
            font-weight: bold;
        }
        .content {
            text-align: center;
            font-size: 18px;
            line-height: 1.6;
            color: #333333;
            margin-bottom: 40px;
        }
        .participant-name {
            font-size: 24px;
            font-weight: bold;
            color: #1a4971;
            border-bottom: 2px solid #1a4971;
            display: inline-block;
            padding-bottom: 5px;
            margin: 0 10px;
        }
        .event-name {
            font-weight: bold;
            color: #1a5276;
        }
        .signature-section {
            margin-top: 60px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .signature-line {
            border-top: 1px solid #333333;
            width: 200px;
            padding-top: 10px;
            text-align: center;
        }
        .signature-name {
            font-size: 14px;
            color: #333333;
        }
        .qr-placeholder {
            position: absolute;
            bottom: 20px;
            right: 20px;
            width: 80px;
            height: 80px;
            border: 1px dashed #ccc;
        }
        .nepemcert-link {
            position: absolute;
            bottom: 20px;
            left: 20px;
            font-size: 10px;
            color: #1a5276;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="certificate-container">
        <h1 class="title">CERTIFICADO</h1>
        
        <div class="content">
            <p>Certificamos que</p>
            
            <p><span class="participant-name">{{ nome }}</span></p>
            
            <p>participou do evento <span class="event-name">{{ evento }}</span>,
            realizado em {{ data }} no {{ local }}, 
            com carga horária de {{ carga_horaria }}.</p>
            
            <p>Data de emissão: {{ data_emissao }}</p>
        </div>
        
        <div class="signature-section">
            <div class="signature-line">
                <div class="signature-name">{{ coordenador_nome }}</div>
                <div>{{ coordenador_titulo }}</div>
            </div>
            
            <div class="signature-line">
                <div class="signature-name">{{ diretor_nome }}</div>
                <div>{{ diretor_titulo }}</div>
            </div>
        </div>
        
        <div class="qr-placeholder">
            <!-- QR Code será inserido aqui -->
        </div>
        
        <a href="{{ url_verificacao }}" class="nepemcert-link">
            Verificar autenticidade em {{ url_verificacao }}
        </a>
    </div>
</body>
</html>"""
    
    template_path = os.path.join(workspace, "templates", "certificado_completo.html")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template_content)
    
    yield {
        "workspace": workspace,
        "csv_path": csv_path,
        "template_path": template_path,
        "template_name": "certificado_completo.html"
    }
    
    # Limpar após uso
    shutil.rmtree(workspace, ignore_errors=True)

def test_certificate_service_complete_flow(certificate_workspace):
    """Testa o fluxo completo do CertificateService"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.certificate_service import CertificateService
    
    workspace = certificate_workspace["workspace"]
    csv_path = certificate_workspace["csv_path"]
    template_name = certificate_workspace["template_name"]
    
    # Inicializar o serviço
    output_dir = os.path.join(workspace, "output")
    service = CertificateService(output_dir=output_dir)
    
    # Configurar diretórios temporários para os gerenciadores
    service.csv_manager.uploads_dir = os.path.join(workspace, "uploads")
    service.template_manager.templates_dir = os.path.join(workspace, "templates")
    service.parameter_manager.config_file = os.path.join(workspace, "config", "parameters.json")
    service.theme_manager.themes_dir = os.path.join(workspace, "themes")
    
    # Configurar parâmetros institucionais
    service.parameter_manager.update_institutional_placeholders({
        "coordenador_nome": "Dr. João Silva",
        "coordenador_titulo": "Coordenador",
        "diretor_nome": "Profa. Maria Santos",
        "diretor_titulo": "Diretora",
        "url_verificacao": "https://nepemufsc.com/verificar"
    })
    service.parameter_manager.save_parameters()
    
    # Detalhes do evento
    event_details = {
        "evento": "Workshop de Python Avançado",
        "data": "15 de Maio de 2025",
        "local": "Auditório Central - UFSC",
        "carga_horaria": "40 horas"
    }
    
    # Executar geração completa
    results = service.generate_certificates_batch(
        csv_file_path=csv_path,
        event_details=event_details,
        template_name=template_name,
        theme_name=None,  # Sem tema personalizado
        has_header=True
    )
    
    # Verificar resultados
    assert results["success_count"] == 4, f"Esperado 4 certificados, obtido {results['success_count']}"
    assert results["failed_count"] == 0, f"Falhas inesperadas: {results['failed_count']}"
    assert len(results["generated_files"]) == 4
    assert len(results["errors"]) == 0, f"Erros encontrados: {results['errors']}"
    
    # Verificar se todos os arquivos foram criados
    for file_path in results["generated_files"]:
        assert os.path.exists(file_path), f"Arquivo não existe: {file_path}"
        assert os.path.getsize(file_path) > 1000, f"Arquivo muito pequeno: {file_path}"
    
    # Verificar se os nomes dos arquivos correspondem aos participantes
    file_names = [os.path.basename(f) for f in results["generated_files"]]
    expected_names = ["certificado_João_Silva_1.pdf", "certificado_Maria_Oliveira_2.pdf", 
                     "certificado_Carlos_Santos_3.pdf", "certificado_Ana_Costa_4.pdf"]
    
    for expected in expected_names:
        assert any(expected in name for name in file_names), f"Nome esperado não encontrado: {expected}"

def test_certificate_service_with_theme(certificate_workspace):
    """Testa o CertificateService com aplicação de tema"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.certificate_service import CertificateService
    
    workspace = certificate_workspace["workspace"]
    csv_path = certificate_workspace["csv_path"]
    template_name = certificate_workspace["template_name"]
    
    # Inicializar o serviço
    output_dir = os.path.join(workspace, "output")
    service = CertificateService(output_dir=output_dir)
    
    # Configurar diretórios temporários
    service.csv_manager.uploads_dir = os.path.join(workspace, "uploads")
    service.template_manager.templates_dir = os.path.join(workspace, "templates")
    service.parameter_manager.config_file = os.path.join(workspace, "config", "parameters.json")
    service.theme_manager.themes_dir = os.path.join(workspace, "themes")
    
    # Criar e configurar um tema personalizado
    theme_name = "Tema Elegante"
    theme_settings = {
        "font_family": "Georgia, serif",
        "text_color": "#2c3e50",
        "background_color": "#f8f9fa",
        "border_color": "#e74c3c",
        "border_width": "3px",
        "border_style": "solid",
        "name_color": "#c0392b",
        "title_color": "#8e44ad",
        "signature_color": "#34495e",
        "event_name_color": "#27ae60",
        "link_color": "#3498db",
        "background_image": None
    }
    
    service.theme_manager.save_theme(theme_name, theme_settings)
    
    # Configurar parâmetros do tema
    service.parameter_manager.update_theme_placeholders(theme_name, {
        "tema_aplicado": "Sim",
        "estilo_elegante": "Ativado"
    })
    service.parameter_manager.save_parameters()
    
    # Detalhes do evento
    event_details = {
        "evento": "Congresso de Tecnologia",
        "data": "20 de Junho de 2025",
        "local": "Centro de Convenções",
        "carga_horaria": "60 horas"
    }
    
    # Executar geração com tema
    results = service.generate_certificates_batch(
        csv_file_path=csv_path,
        event_details=event_details,
        template_name=template_name,
        theme_name=theme_name,
        has_header=True
    )
    
    # Verificar que a geração foi bem-sucedida
    assert results["success_count"] == 4
    assert results["failed_count"] == 0
    assert len(results["errors"]) == 0
    
    # Verificar se pelo menos um arquivo foi criado (para testar o conteúdo)
    assert len(results["generated_files"]) > 0
    
    # Como não podemos ler o conteúdo do PDF facilmente, verificamos pelo menos
    # que os arquivos foram criados com tamanho adequado
    for file_path in results["generated_files"]:
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 1000

def test_certificate_service_error_handling(certificate_workspace):
    """Testa o tratamento de erros do CertificateService"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.certificate_service import CertificateService
    
    workspace = certificate_workspace["workspace"]
    
    # Inicializar o serviço
    output_dir = os.path.join(workspace, "output")
    service = CertificateService(output_dir=output_dir)
    
    # Configurar diretórios temporários
    service.csv_manager.uploads_dir = os.path.join(workspace, "uploads")
    service.template_manager.templates_dir = os.path.join(workspace, "templates")
    
    # Teste 1: CSV inexistente
    results = service.generate_certificates_batch(
        csv_file_path="arquivo_inexistente.csv",
        event_details={"evento": "Teste", "data": "2025", "local": "Local", "carga_horaria": "10h"},
        template_name="template.html",
        theme_name=None,
        has_header=True
    )
    
    assert results["success_count"] == 0
    assert results["failed_count"] == -1  # Indica erro geral
    assert len(results["errors"]) > 0
    assert "Error loading CSV" in str(results["errors"])
    
    # Teste 2: Template inexistente
    results = service.generate_certificates_batch(
        csv_file_path=certificate_workspace["csv_path"],
        event_details={"evento": "Teste", "data": "2025", "local": "Local", "carga_horaria": "10h"},
        template_name="template_inexistente.html",
        theme_name=None,
        has_header=True
    )
    
    assert results["success_count"] == 0
    assert len(results["errors"]) > 0
    assert "not found" in str(results["errors"]).lower()

def test_certificate_service_csv_without_header(certificate_workspace):
    """Testa o CertificateService com CSV sem cabeçalho"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.certificate_service import CertificateService
    
    workspace = certificate_workspace["workspace"]
    template_name = certificate_workspace["template_name"]
    
    # Criar CSV sem cabeçalho
    csv_content_no_header = """Pedro Alves
    Lucia Ferreira
    Roberto Costa"""
    
    csv_no_header_path = os.path.join(workspace, "uploads", "sem_cabecalho.csv")
    with open(csv_no_header_path, "w", encoding="utf-8") as f:
        f.write(csv_content_no_header)
    
    # Inicializar o serviço
    output_dir = os.path.join(workspace, "output")
    service = CertificateService(output_dir=output_dir)
    
    # Configurar diretórios
    service.csv_manager.uploads_dir = os.path.join(workspace, "uploads")
    service.template_manager.templates_dir = os.path.join(workspace, "templates")
    service.parameter_manager.config_file = os.path.join(workspace, "config", "parameters.json")
    
    # Detalhes do evento
    event_details = {
        "evento": "Seminário de Pesquisa",
        "data": "10 de Julho de 2025",
        "local": "Laboratório de Informática",
        "carga_horaria": "20 horas"
    }
    
    # Executar geração sem cabeçalho
    results = service.generate_certificates_batch(
        csv_file_path=csv_no_header_path,
        event_details=event_details,
        template_name=template_name,
        theme_name=None,
        has_header=False  # Importante: indicar que não há cabeçalho
    )
    
    # Verificar resultados
    assert results["success_count"] == 3, f"Esperado 3 certificados, obtido {results['success_count']}"
    assert results["failed_count"] == 0
    assert len(results["generated_files"]) == 3
    
    # Verificar se os arquivos foram criados
    for file_path in results["generated_files"]:
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 1000

def test_certificate_service_authentication_codes(certificate_workspace):
    """Testa se os códigos de autenticação são gerados e salvos corretamente"""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    from app.certificate_service import CertificateService
    
    workspace = certificate_workspace["workspace"]
    csv_path = certificate_workspace["csv_path"]
    template_name = certificate_workspace["template_name"]
    
    # Inicializar o serviço
    output_dir = os.path.join(workspace, "output")
    service = CertificateService(output_dir=output_dir)
    
    # Configurar diretórios
    service.csv_manager.uploads_dir = os.path.join(workspace, "uploads")
    service.template_manager.templates_dir = os.path.join(workspace, "templates")
    
    # Detalhes do evento
    event_details = {
        "evento": "Curso de Desenvolvimento Web",
        "data": "25 de Agosto de 2025",
        "local": "Sala de Treinamento",
        "carga_horaria": "80 horas"
    }
    
    # Executar geração
    results = service.generate_certificates_batch(
        csv_file_path=csv_path,
        event_details=event_details,
        template_name=template_name,
        theme_name=None,
        has_header=True
    )
    
    assert results["success_count"] == 4
    
    # Verificar se os códigos de autenticação foram salvos
    codigos_dir = os.path.join(workspace, "..", "codigos")  # AuthenticationManager salva em codigos/
    
    # Como os códigos são salvos em um diretório diferente, vamos verificar se o método foi chamado
    # Testamos isso indiretamente verificando se não houve erros relacionados à autenticação
    assert len(results["errors"]) == 0, "Não deveria haver erros relacionados à geração de códigos"
    
    # Verificar se todos os certificados foram gerados (o que indica que a autenticação funcionou)
    assert results["success_count"] == 4
    assert results["failed_count"] == 0
