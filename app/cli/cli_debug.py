import os
import sys
import platform
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich import box
import questionary
from contextlib import redirect_stderr
from io import StringIO

# Importações dos módulos da aplicação
from app.template_manager import TemplateManager
from app.theme_manager import ThemeManager
from app.pdf_generator import PDFGenerator
from app.parameter_manager import ParameterManager
from app.cert_auth_manager import CertAuthenticationManager
from app.connectivity_manager import ConnectivityManager
from app.zip_exporter import ZipExporter
from app.certificate_service import CertificateService
from app.utils.app_parameters import APP_VERSION

# Inicializar console e componentes
console = Console()
template_manager = TemplateManager()
theme_manager = ThemeManager()
pdf_generator = PDFGenerator()
parameter_manager = ParameterManager()
auth_manager = CertAuthenticationManager()
connectivity_manager = ConnectivityManager()
zip_exporter = ZipExporter()
certificate_service = CertificateService()

# Versão do aplicativo

# Wrapper functions para questionary
def quiet_select(message, choices, **kwargs):
    """Wrapper para questionary.select que suprime mensagens de erro."""
    try:
        if sys.platform.startswith('win'):
            with redirect_stderr(StringIO()):
                return questionary.select(message, choices, **kwargs).ask()
        else:
            return questionary.select(message, choices, **kwargs).ask()
    except Exception as e:
        console.print(f"[red]Erro ao exibir seleção: {e}[/red]")
        return choices[0] if choices else None

def quiet_confirm(message, **kwargs):
    """Wrapper para questionary.confirm que suprime mensagens de erro."""
    try:
        if sys.platform.startswith('win'):
            with redirect_stderr(StringIO()):
                return questionary.confirm(message, **kwargs).ask()
        else:
            return questionary.confirm(message, **kwargs).ask()
    except Exception as e:
        console.print(f"[red]Erro ao solicitar confirmação: {e}[/red]")
        return kwargs.get('default', False)

def quiet_text(message, **kwargs):
    """Wrapper para questionary.text que suprime mensagens de erro."""
    try:
        if sys.platform.startswith('win'):
            with redirect_stderr(StringIO()):
                return questionary.text(message, **kwargs).ask()
        else:
            return questionary.text(message, **kwargs).ask()
    except Exception as e:
        console.print(f"[red]Erro ao solicitar texto: {e}[/red]")
        return kwargs.get('default', "")

def get_menu_style():
    """Retorna o estilo padrão para menus do questionary."""
    from questionary import Style
    
    return Style([
        ('qmark', 'fg:#ff9d00 bold'),
        ('question', 'bold'),
        ('answer', 'fg:#ff9d00 bold'),
        ('pointer', 'fg:#ff9d00 bold'),
        ('highlighted', 'fg:#ff9d00 bold'),
        ('selected', 'fg:#cc5454'),
        ('separator', 'fg:#cc5454'),
        ('instruction', ''),
        ('text', ''),
        ('disabled', 'fg:#858585 italic')
    ])

def debug_compare_themes():
    """Ferramenta de debug para comparar temas usando dados de exemplo."""
    console.clear()
    console.print("[bold blue]== DEBUG: Comparação de Temas ==[/bold blue]\n")
    console.print("[yellow]Esta ferramenta gera certificados com TODOS os temas disponíveis usando dados de exemplo.[/yellow]")
    console.print("[yellow]Útil para debug e comparação visual dos temas.[/yellow]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[red]❌ Nenhum template disponível.[/red]")
        console.print("Importe um template primeiro antes de usar esta ferramenta.")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template
    template_name = quiet_select(
        "Selecione o template para usar:",
        choices=templates,
        style=get_menu_style()
    )
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[red]❌ Erro ao carregar template: {template_name}[/red]")
        return
      # Gerar código de autenticação para exemplos de temas
    nome_exemplo = "João da Silva Santos"
    evento_exemplo = "Workshop de Tecnologia e Inovação"
    data_exemplo = "15 a 17 de maio de 2025"
    
    # Gerar código de autenticação para o exemplo    
    codigo_autenticacao_exemplo = auth_manager.gerar_codigo_autenticacao(
        nome_participante=nome_exemplo,
        evento=evento_exemplo,
        data_evento=data_exemplo
    )
    # Usa o próprio código de autenticação como código de verificação
    codigo_verificacao_exemplo = codigo_autenticacao_exemplo
    # Gera a URL base para verificação (sem o código)
    url_verificacao_exemplo = "https://certificados.nepemufsc.com"
    # Gera a URL completa para o QR code (com o código como parâmetro)
    qrcode_url_exemplo = auth_manager.gerar_qrcode_data(codigo_autenticacao_exemplo)
    
    # Dados de exemplo fixos para todos os certificados
    sample_data = {
        "nome": nome_exemplo,
        "evento": evento_exemplo,
        "local": "Campus Universitário - Sala de Conferências",
        "data": data_exemplo,
        "carga_horaria": "20",
        "coordenador": "Prof. Dr. Maria Fernanda Costa",
        "diretor": "Prof. Dr. Roberto Andrade Lima",
        "cidade": "Florianópolis",        "data_emissao": "29 de maio de 2025",
        "codigo_autenticacao": codigo_autenticacao_exemplo,
        "codigo_verificacao": codigo_verificacao_exemplo,
        "url_verificacao": url_verificacao_exemplo,
        "url_qrcode": qrcode_url_exemplo,
        "intro_text": "Certificamos que",
        "participation_text": "participou com êxito do",
        "location_text": "realizado em",
        "date_text": "no período de",
        "workload_text": "com carga horária total de",
        "hours_text": "horas",
        "coordinator_title": "Coordenador do Evento",
        "director_title": "Diretor da Instituição",
        "title_text": "CERTIFICADO DE PARTICIPAÇÃO"
    }
    
    # Salvar informações do certificado de exemplo
    auth_manager.salvar_codigo(
        codigo_autenticacao=codigo_autenticacao_exemplo,
        nome_participante=nome_exemplo,
        evento=evento_exemplo,
        data_evento=data_exemplo,
        local_evento=sample_data["local"],
        carga_horaria=sample_data["carga_horaria"]
    )
    
    # Listar temas disponíveis
    available_themes = theme_manager.list_themes()
    
    if not available_themes:
        console.print("[red]❌ Nenhum tema disponível.[/red]")
        input("\nPressione Enter para voltar...")
        return
    
    console.print(f"\n[green]✓ Template carregado: {template_name}[/green]")
    console.print(f"[green]✓ Temas encontrados: {len(available_themes)}[/green]")
    console.print(f"[cyan]Temas: {', '.join(available_themes)}[/cyan]\n")
    
    # Confirmar geração
    confirm = quiet_confirm(
        f"Deseja gerar {len(available_themes)} certificados (um para cada tema)?",
        default=True
    )
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Criar diretório de saída específico para debug
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_output_dir = os.path.join("output", f"debug_themes_{timestamp}")
    os.makedirs(debug_output_dir, exist_ok=True)
    
    console.print(f"\n[blue]📁 Diretório de saída: {debug_output_dir}[/blue]\n")
    
    # Gerar certificados para cada tema
    generated_files = []
    
    with console.status("[bold green]Gerando certificados com diferentes temas...") as status:
        for i, theme_name in enumerate(available_themes, 1):
            try:
                status.update(f"[bold green]Processando tema {i}/{len(available_themes)}: {theme_name}")
                
                # Carregar configurações do tema
                theme_settings = theme_manager.load_theme(theme_name)
                
                if not theme_settings:
                    console.print(f"[yellow]⚠️ Aviso: Tema '{theme_name}' não pôde ser carregado[/yellow]")
                    continue
                
                # Mesclar dados de exemplo com configurações do tema
                merged_data = parameter_manager.merge_placeholders(sample_data.copy(), theme_name)
                
                # Renderizar template com dados
                try:
                    # Salvar template temporariamente
                    temp_template_name = f"temp_debug_{theme_name.replace(' ', '_').lower()}_{timestamp}.html"
                    temp_template_path = os.path.join("templates", temp_template_name)
                    
                    with open(temp_template_path, "w", encoding="utf-8") as f:
                        f.write(template_content)
                      # Gerar QR code adaptado ao tamanho do placeholder no template
                    qr_info = auth_manager.gerar_qrcode_adaptado(codigo_autenticacao_exemplo, template_content)
                    merged_data["qrcode_base64"] = qr_info["qrcode_base64"]
                    
                    # Aplicar tema ao template antes de renderizar
                    themed_template = theme_manager.apply_theme_to_template(template_content, theme_settings)
                    
                    # Renderizar template
                    html_content = template_manager.render_template_from_string(themed_template, merged_data)
                    
                    # Substituir o placeholder do QR code pelo QR code real
                    html_content = auth_manager.substituir_qr_placeholder(html_content, qr_info["qrcode_base64"])
                    
                    # Aplicar tema ao HTML
                    if theme_settings:
                        html_content = theme_manager.apply_theme_to_template(html_content, theme_settings)
                    
                    # Gerar nome do arquivo
                    safe_theme_name = theme_name.replace(" ", "_").replace("ã", "a").replace("é", "e").replace("ô", "o")
                    pdf_filename = f"certificado_tema_{safe_theme_name}.pdf"
                    pdf_path = os.path.join(debug_output_dir, pdf_filename)
                    
                    # Gerar PDF
                    pdf_generator.generate_pdf(html_content, pdf_path, orientation='landscape')
                    generated_files.append((pdf_path, theme_name))
                    
                    console.print(f"[green]✓[/green] {theme_name} → {pdf_filename}")
                    
                except Exception as e:
                    console.print(f"[red]❌ Erro no tema '{theme_name}': {str(e)}[/red]")
                    
                finally:
                    # Limpar arquivo temporário
                    if 'temp_template_path' in locals() and os.path.exists(temp_template_path):
                        os.remove(temp_template_path)
                        
            except Exception as e:
                console.print(f"[red]❌ Erro geral no tema '{theme_name}': {str(e)}[/red")
    
    # Relatório final
    console.print(f"\n[bold green]🎉 Geração concluída![/bold green]")
    console.print(f"[green]✓[/green] Versão do aplicativo: {APP_VERSION}")
    console.print(f"[{'green' if templates else 'yellow'}]{'✓' if templates else '⚠️'}[/{'green' if templates else 'yellow'}] Templates: {len(templates) if templates else 0}")
    console.print(f"[{'green' if available_themes else 'yellow'}]{'✓' if available_themes else '⚠️'}[/{'green' if available_themes else 'yellow'}] Temas: {len(available_themes) if available_themes else 0}")
    
    if generated_files:
        # Mostrar lista dos arquivos gerados
        console.print("[bold]Arquivos gerados:[/bold]")
        for pdf_path, theme_name in generated_files:
            filename = os.path.basename(pdf_path)
            console.print(f"  • [cyan]{filename}[/cyan] ({theme_name})")
        
        # Oferecer opções adicionais
        console.print("\n[bold]Opções adicionais:[/bold]")
        
        action = quiet_select(
            "O que deseja fazer agora?",
            choices=[
                "📁 Abrir diretório de saída",
                "📊 Criar arquivo ZIP com todos os certificados",
                "👁️ Abrir primeiro certificado",
                "↩️ Voltar ao menu"
            ],
            style=get_menu_style()
        )
        
        if action == "📁 Abrir diretório de saída":
            try:
                import subprocess
                os.startfile(debug_output_dir)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", debug_output_dir])  # macOS
                except:
                    subprocess.call(["xdg-open", debug_output_dir])  # Linux
            console.print("[green]✓ Diretório aberto[/green]")
            
        elif action == "📊 Criar arquivo ZIP com todos os certificados":
            zip_filename = f"debug_temas_{timestamp}.zip"
            zip_path = os.path.join(debug_output_dir, zip_filename)
            
            try:
                with console.status("[bold green]Criando arquivo ZIP..."):
                    zip_exporter.create_zip([pdf_path for pdf_path, _ in generated_files], zip_path)
                console.print(f"[green]✓ ZIP criado: {zip_filename}[/green]")
            except Exception as e:
                console.print(f"[red]❌ Erro ao criar ZIP: {str(e)}[/red]")
                
        elif action == "👁️ Abrir primeiro certificado":
            if generated_files:
                first_pdf = generated_files[0][0]
                try:
                    import subprocess
                    os.startfile(first_pdf)  # Windows
                except AttributeError:
                    try:
                        subprocess.call(["open", first_pdf])  # macOS
                    except:
                        subprocess.call(["xdg-open", first_pdf])  # Linux
                console.print("[green]✓ Certificado aberto[/green]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def debug_system_check():
    """Função de debug para verificar o sistema."""
    console.clear()
    console.print("[bold red]== DEBUG: Verificação do Sistema ==[/bold red]\n")
    
    console.print("[yellow]Esta ferramenta verifica o estado geral do sistema NEPEM Cert.[/yellow]\n")
    
    # Verificar diretórios essenciais
    console.print("[bold]📁 Verificando diretórios essenciais...[/bold]")
    
    directories = {
        "Templates": "templates",
        "Output": certificate_service.output_dir, 
        "Config": "config",
        "App": "app"
    }
    
    for name, path in directories.items():
        if os.path.exists(path):
            console.print(f"[green]✓[/green] {name}: {path}")
        else:
            console.print(f"[red]❌[/red] {name}: {path} [red](não encontrado)[/red]")
            try:
                os.makedirs(path, exist_ok=True)
                console.print(f"[yellow]  → Diretório criado automaticamente[/yellow]")
            except Exception as e:
                console.print(f"[red]  → Erro ao criar: {str(e)}[/red]")
    
    # Verificar templates disponíveis
    console.print(f"\n[bold]📄 Verificando templates...[/bold]")
    templates = template_manager.list_templates()
    if templates:
        console.print(f"[green]✓[/green] {len(templates)} template(s) encontrado(s):")
        for template in templates[:5]:  # Mostrar apenas os primeiros 5
            console.print(f"[dim]  • {template}[/dim]")
        if len(templates) > 5:
            console.print(f"[dim]  ... e mais {len(templates) - 5} template(s)[/dim]")
    else:
        console.print("[yellow]⚠️[/yellow] Nenhum template encontrado")
    
    # Verificar temas disponíveis
    console.print(f"\n[bold]🎨 Verificando temas...[/bold]")
    themes = theme_manager.list_themes()
    if themes:
        console.print(f"[green]✓[/green] {len(themes)} tema(s) encontrado(s):")
        for theme in themes:
            console.print(f"[dim]  • {theme}[/dim]")
    else:
        console.print("[yellow]⚠️[/yellow] Nenhum tema encontrado")
    
    # Verificar configurações de parâmetros
    console.print(f"\n[bold]⚙️ Verificando configurações...[/bold]")
    try:
        institutional = parameter_manager.get_institutional_placeholders()
        defaults = parameter_manager.get_default_placeholders()
        
        console.print(f"[green]✓[/green] Parâmetros institucionais: {len(institutional)} configurado(s)")
        console.print(f"[green]✓[/green] Parâmetros padrão: {len(defaults)} configurado(s)")
        
        # Verificar arquivo de configuração
        config_path = parameter_manager.config_file
        if os.path.exists(config_path):
            size = os.path.getsize(config_path)
            console.print(f"[green]✓[/green] Arquivo de configuração: {config_path} ({size} bytes)")
        else:
            console.print(f"[yellow]⚠️[/yellow] Arquivo de configuração não encontrado: {config_path}")
            
    except Exception as e:
        console.print(f"[red]❌[/red] Erro ao verificar configurações: {str(e)}")
    
    # Verificar conectividade
    console.print(f"\n[bold]🌐 Verificando conectividade...[/bold]")
    try:
        conn_info = connectivity_manager.get_connection_status()
        status_color = {
            "Conectado": "green",
            "Desconectado": "red", 
            "Aguardando": "yellow"
        }.get(conn_info["status"], "yellow")
        
        console.print(f"[{status_color}]●[/{status_color}] Status: {conn_info['status']}")
        if "last_check" in conn_info:
            console.print(f"[dim]  Última verificação: {conn_info['last_check']}[/dim]")
            
    except Exception as e:
        console.print(f"[red]❌[/red] Erro ao verificar conectividade: {str(e)}")
    
    # Verificar dependências do sistema
    console.print(f"\n[bold]📦 Verificando dependências...[/bold]")
    
    dependencies = [
        ("pandas", "Processamento de CSV"),
        ("rich", "Interface de usuário"),
        ("questionary", "Menus interativos"),
        ("jinja2", "Templates"),
        ("xhtml2pdf", "Geração de PDF"),
        ("qrcode", "Códigos QR"),
        ("PIL", "Processamento de imagens")
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            console.print(f"[green]✓[/green] {module_name}: {description}")
        except ImportError:
            console.print(f"[red]❌[/red] {module_name}: {description} [red](não encontrado)[/red]")
    
    # Informações do sistema
    console.print(f"\n[bold]💻 Informações do sistema...[/bold]")
    import platform
    console.print(f"[cyan]Python:[/cyan] {platform.python_version()}")
    console.print(f"[cyan]Sistema:[/cyan] {platform.system()} {platform.release()}")
    console.print(f"[cyan]Arquitetura:[/cyan] {platform.machine()}")
    
    # Resumo final
    console.print(f"\n[bold blue]📊 Resumo da verificação:[/bold blue]")
    console.print(f"[green]✓[/green] Sistema operacional: {platform.system()}")
    console.print(f"[green]✓[/green] Versão do aplicativo: {APP_VERSION}")
    console.print(f"[{'green' if templates else 'yellow'}]{'✓' if templates else '⚠️'}[/{'green' if templates else 'yellow'}] Templates: {len(templates) if templates else 0}")
    console.print(f"[{'green' if themes else 'yellow'}]{'✓' if themes else '⚠️'}[/{'green' if themes else 'yellow'}] Temas: {len(themes) if themes else 0}")
    
    console.print("\n[dim]Esta verificação ajuda a identificar problemas de configuração e dependências.[/dim]")
    console.print("[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def debug_generate_certificate_for_theme(tema_nome):
    """
    Gera um certificado de teste para um tema específico.
    
    Args:
        tema_nome (str): Nome do tema para testar
        
    Returns:
        tuple: (sucesso, caminho_do_arquivo, erro)
    """
    try:
        from app.template_manager import TemplateManager
        from app.theme_manager import ThemeManager
        from app.pdf_generator import PDFGenerator
        from app.parameter_manager import ParameterManager
        from app.cert_auth_manager import CertAuthenticationManager
        
        # Inicializar gerenciadores
        template_manager = TemplateManager()
        theme_manager = ThemeManager()
        pdf_generator = PDFGenerator()
        param_manager = ParameterManager()
        auth_manager = CertAuthenticationManager()
        
        # Carregar template padrão
        template_name = "certificado_v1_basico.html"
        template_content = template_manager.load_template(template_name)
        
        if not template_content:
            return False, None, f"Template '{template_name}' não encontrado"
        
        # Carregar tema
        theme_settings = theme_manager.load_theme(tema_nome)
        if not theme_settings:
            return False, None, f"Tema '{tema_nome}' não encontrado"
        
        # Aplicar tema ao template
        themed_template = theme_manager.apply_theme_to_template(template_content, theme_settings)
        
        # Dados de teste
        dados_teste = {
            "nome": "João da Silva Santos",
            "evento": f"Workshop NEPEM - Tema {tema_nome}",
            "local": "Laboratório de Sistemas de Conhecimento - UFSC",
            "data": "10 de Janeiro de 2025",
            "carga_horaria": "40 horas",
            "coordenador": "Prof. Dr. Ricardo Miranda Barcia",
            "cidade": "Florianópolis",
            "data_emissao": "10/01/2025"
        }
        
        # Gerar código de autenticação
        auth_code = auth_manager.gerar_codigo_autenticacao(dados_teste["nome"], dados_teste["evento"])
        dados_teste["codigo_verificacao"] = auth_code
        dados_teste["url_verificacao"] = "https://certificados.nepemufsc.com"
        
        # Mesclar com parâmetros do sistema
        dados_finais = param_manager.merge_placeholders(dados_teste, tema_nome)
        
        # Renderizar template
        html_renderizado = template_manager.render_template_from_string(themed_template, dados_finais)
        
        # Gerar QR code e substituir placeholder
        qrcode_base64 = auth_manager.gerar_qrcode_base64(auth_code)
        html_final = auth_manager.substituir_qr_placeholder(html_renderizado, qrcode_base64)
        
        # Gerar PDF
        nome_arquivo = f"debug_{tema_nome.replace(' ', '_').lower()}.pdf"
        caminho_pdf = pdf_generator.generate_pdf(html_final, nome_arquivo, orientation="landscape")
        
        return True, caminho_pdf, None
        
    except Exception as e:
        return False, None, str(e)
