#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEPEM Certificados - Programa principal
Aplicativo para geração de certificados em lote via CLI.
"""

import os
import sys
import click
import pandas as pd
from rich.console import Console

# Importar a nova interface CLI
from ui import CLIInterface
from app.certificate_service import CertificateService
from app.template_manager import TemplateManager
from app.parameter_manager import ParameterManager
from app.theme_manager import ThemeManager
from app.connectivity_manager import ConnectivityManager
from app.cert_auth_manager import CertAuthenticationManager
from app.zip_exporter import ZipExporter

# Console Rich para saída formatada
console = Console()


def initialize_app_services():
    """Inicializa todos os serviços da aplicação."""
    services = {}
    
    # Serviços principais
    services["parameter_manager"] = ParameterManager()
    services["template_manager"] = TemplateManager()
    services["theme_manager"] = ThemeManager()
    services["connectivity_manager"] = ConnectivityManager()
    services["auth_manager"] = CertAuthenticationManager()
    services["zip_exporter"] = ZipExporter()
    services["certificate_service"] = CertificateService()
    
    return services


def interactive_mode():
    """Executa o modo interativo usando a nova UI."""
    # Inicializar serviços
    app_services = initialize_app_services()
    
    # Criar interface CLI
    cli_interface = CLIInterface(app_services)
    
    # Loop principal da aplicação
    while True:
        try:
            # Exibir menu principal
            choice = cli_interface.show_main_menu()
            
            if not choice:
                break
            
            # Processar escolha
            if choice == "🚪 Sair":
                if cli_interface.show_exit_confirmation():
                    break
                continue
            
            elif choice == "🔖 Gerar Certificados":
                cli_interface.handle_generator_action(choice)
            
            elif choice == "🎨 Gerenciar Templates":
                template_choice = cli_interface.show_templates_menu()
                if template_choice and template_choice != "↩️ Voltar ao menu principal":
                    cli_interface.handle_template_action(template_choice)
            
            elif choice == "⚙️ Configurações":
                settings_choice = cli_interface.show_settings_menu()
                if settings_choice and settings_choice != "↩️ Voltar ao menu principal":
                    handle_settings_action(app_services, settings_choice)
            
            elif choice == "🔄 Sincronização e Conectividade":
                connectivity_choice = cli_interface.show_connectivity_menu()
                if connectivity_choice and connectivity_choice != "↩️ Voltar ao menu principal":
                    handle_connectivity_action(app_services, connectivity_choice)
            
            elif choice == "❓ Ajuda":
                cli_interface.show_help()
            
            # Comandos de debug
            elif choice.startswith("🐛 DEBUG:"):
                handle_debug_action(app_services, choice)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Operação cancelada pelo usuário.[/yellow]")
            if cli_interface.show_exit_confirmation():
                break
        except Exception as e:
            console.print(f"[bold red]Erro inesperado: {str(e)}[/bold red]")
            console.print("[yellow]Retornando ao menu principal...[/yellow]")


def handle_settings_action(app_services, action):
    """Processa ações de configurações."""
    # Implementação simplificada para as configurações
    console.print(f"[yellow]Ação de configuração '{action}' em desenvolvimento.[/yellow]")
    console.print("[cyan]Use o modo interativo completo para acessar todas as configurações.[/cyan]")
    
    from ui.ui_utils import UIUtils
    ui_utils = UIUtils()
    ui_utils.wait_for_enter()


def handle_connectivity_action(app_services, action):
    """Processa ações de conectividade."""
    conn_manager = app_services["connectivity_manager"]
    
    if action == "🔄 Verificar conexão":
        console.print("[bold blue]Verificando conexão com o servidor...[/bold blue]")
        result = conn_manager.check_connection()
        
        status_color = {
            "Conectado": "green",
            "Desconectado": "red"
        }.get(result["status"], "yellow")
        
        console.print(f"Status: [{status_color}]{result['status']}[/{status_color}]")
        console.print(f"Mensagem: {result['message']}")
        console.print(f"Horário: {result['timestamp']}")
    
    else:
        console.print(f"[yellow]Ação de conectividade '{action}' em desenvolvimento.[/yellow]")
    
    from ui.ui_utils import UIUtils
    ui_utils = UIUtils()
    ui_utils.wait_for_enter()


def handle_debug_action(app_services, action):
    """Processa ações de debug."""
    if "Comparar temas" in action:
        console.print("[bold blue]🐛 DEBUG: Comparação de temas[/bold blue]")
        
        theme_manager = app_services["theme_manager"]
        themes = theme_manager.list_themes()
        
        console.print(f"Temas disponíveis: {len(themes)}")
        for theme in themes:
            console.print(f"  • {theme}")
    
    elif "Verificar sistema" in action:
        console.print("[bold blue]🐛 DEBUG: Verificação do sistema[/bold blue]")
        
        # Verificar serviços
        for service_name, service in app_services.items():
            console.print(f"✓ {service_name}: {type(service).__name__}")
    
    from ui.ui_utils import UIUtils
    ui_utils = UIUtils()
    ui_utils.wait_for_enter()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="1.1.0", prog_name="NEPEM Certificados")
def cli(ctx):
    """NEPEM Certificados - Gerador de certificados em lote via linha de comando."""
    # Se nenhum comando foi especificado, executa o modo interativo
    if ctx.invoked_subcommand is None:
        interactive_mode()


@cli.command()
def interactive():
    """Inicia a interface interativa do gerador de certificados."""
    interactive_mode()


@cli.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.argument("template", type=click.Path(exists=True))
@click.option("--output", "-o", default="output", help="Diretório de saída para os certificados")
@click.option("--zip", "-z", is_flag=True, help="Criar arquivo ZIP com os certificados")
@click.option("--zip-name", default=None, help="Nome do arquivo ZIP")
def generate(csv_file, template, output, zip, zip_name):
    """
    Gera certificados em lote a partir de um arquivo CSV e um template HTML.
    
    CSV_FILE: Caminho para o arquivo CSV com os dados dos participantes.
    TEMPLATE: Caminho para o arquivo de template HTML.
    """
    console.print(f"[bold blue]Gerando certificados...[/bold blue]")
    console.print(f"- Arquivo CSV: [cyan]{csv_file}[/cyan]")
    console.print(f"- Template: [cyan]{template}[/cyan]")
    console.print(f"- Diretório de saída: [cyan]{output}[/cyan]")
    
    try:
        # Criar diretório de saída se não existir
        os.makedirs(output, exist_ok=True)
        
        # Inicializar serviços necessários
        certificate_service = CertificateService(output_dir=output)
        zip_exporter = ZipExporter()
        template_manager = TemplateManager()

        # Preparar template para o serviço
        template_file_name = os.path.basename(template)
        original_template_in_managed_dir = False
        managed_template_path = os.path.join(template_manager.templates_dir, template_file_name)

        try:
            # Verificar se o template já está no diretório gerenciado
            if os.path.abspath(template) == os.path.abspath(managed_template_path):
                original_template_in_managed_dir = True
                console.print(f"[dim]Template '{template_file_name}' já está no diretório gerenciado.[/dim]")
            else:
                with open(template, 'r', encoding='utf-8') as f:
                    original_template_content = f.read()
                template_manager.save_template(template_file_name, original_template_content)
                console.print(f"[green]✓[/green] Template '{template_file_name}' preparado para o serviço.")
        except Exception as e:
            console.print(f"[bold red]Erro ao preparar template '{template}': [/bold red]{str(e)}")
            sys.exit(1)

        # Carregar dados do CSV
        try:
            df = pd.read_csv(csv_file)
            console.print(f"[green]✓[/green] Arquivo CSV '{csv_file}' carregado: {len(df)} registros.")
        except Exception as e:
            console.print(f"[bold red]Erro ao carregar CSV '{csv_file}': [/bold red]{str(e)}")
            # Limpar template temporário
            if not original_template_in_managed_dir and os.path.exists(managed_template_path):
                try:
                    os.remove(managed_template_path)
                except:
                    pass
            sys.exit(1)

        # Parâmetros para geração
        event_data = {}
        theme_name = None
        has_header = True

        console.print(f"Chamando CertificateService para geração em lote...")
        
        # Gerar certificados
        generation_result = certificate_service.generate_certificates_batch(
            csv_file_path=csv_file,
            event_details=event_data,
            template_name=template_file_name,
            theme_name=theme_name,
            has_header=has_header
        )

        # Limpar template temporário
        if not original_template_in_managed_dir and os.path.exists(managed_template_path):
            try:
                os.remove(managed_template_path)
                console.print(f"[dim]Template temporário '{template_file_name}' limpo.[/dim]")
            except Exception as e:
                console.print(f"[yellow]Aviso: Não foi possível limpar o template temporário: {str(e)}[/yellow]")

        # Exibir resultados
        if generation_result["success_count"] > 0:
            console.print(f"[bold green]✓ {generation_result['success_count']} certificados gerados com sucesso![/bold green]")

        if generation_result["failed_count"] > 0:
            console.print(f"[bold red]✗ {generation_result['failed_count']} certificados falharam ao gerar.[/bold red]")

        if generation_result["errors"]:
            console.print("\n[bold yellow]Erros e Avisos durante a geração:[/bold yellow]")
            for error_msg in generation_result["errors"]:
                console.print(f"  [yellow]•[/yellow] {error_msg}")
        
        # Criar arquivo ZIP se solicitado
        if zip and generation_result["generated_files"]:
            if not zip_name:
                from datetime import datetime
                zip_name_default = f"certificados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_name = zip_name_default 
            
            if not zip_name.endswith('.zip'):
                zip_name += '.zip'
                
            zip_path = os.path.join(output, zip_name)
            
            with console.status("[bold green]Criando arquivo ZIP..."):
                try:
                    zip_exporter.create_zip(generation_result["generated_files"], zip_path)
                    console.print(f"[bold green]✓ Arquivo ZIP criado: [/bold green]{zip_path}")
                except Exception as e_zip:
                    console.print(f"[bold red]Erro ao criar arquivo ZIP: {str(e_zip)}[/bold red]")
        elif zip and not generation_result["generated_files"]:
            console.print(f"[yellow]Nenhum certificado foi gerado para empacotar.[/yellow]")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificados: [/bold red]{str(e)}")
        sys.exit(1)


@cli.command()
def config():
    """Gerencia as configurações do aplicativo."""
    console.print("[bold blue]Gerenciando configurações...[/bold blue]")
    console.print("[yellow]Este comando ainda não está completamente implementado.[/yellow]")
    console.print("[cyan]Use o modo interativo para configurar o aplicativo:[/cyan] nepemcert interactive")


@cli.command()
@click.option("--status", is_flag=True, help="Verificar status da conexão")
@click.option("--url", help="Configurar URL do servidor remoto")
def server(status, url):
    """Gerencia a conectividade com o servidor remoto."""
    conn_manager = ConnectivityManager()
    
    if status:
        console.print("[bold blue]Verificando status da conexão...[/bold blue]")
        result = conn_manager.check_connection()
        
        status_color = {
            "Conectado": "green",
            "Desconectado": "red"
        }.get(result["status"], "yellow")
        
        console.print(f"Status: [{status_color}]{result['status']}[/{status_color}]")
        console.print(f"Mensagem: {result['message']}")
        console.print(f"Horário: {result['timestamp']}")
    
    elif url:
        console.print(f"[bold blue]Configurando URL do servidor: [/bold blue]{url}")
        conn_manager.set_server_url(url)
        console.print("[green]URL do servidor configurada com sucesso.[/green]")
    
    else:
        console.print("[bold blue]Gerenciando conectividade com o servidor remoto...[/bold blue]")
        console.print("[yellow]Este comando precisa de mais opções.[/yellow]")
        console.print("[cyan]Use o modo interativo para gerenciar a conectividade:[/cyan] nepemcert interactive")


@cli.command()
@click.argument("template", type=click.Path(exists=True))
@click.option("--output", "-o", default=None, help="Diretório de saída para os certificados (padrão: output/debug_themes_TIMESTAMP)")
@click.option("--zip", "-z", is_flag=True, help="Criar arquivo ZIP com todos os certificados")
def debug_themes(template, output, zip):
    """
    [DEBUG] Gera certificados com TODOS os temas usando dados de exemplo.
    
    TEMPLATE: Caminho para o arquivo de template HTML.
    
    Esta é uma ferramenta de debug que gera um certificado para cada tema disponível
    usando dados de exemplo fixos. Útil para comparar visualmente todos os temas.
    """
    import pandas as pd
    from datetime import datetime
    from app.pdf_generator import PDFGenerator
    from app.zip_exporter import ZipExporter
    from app.parameter_manager import ParameterManager
    from app.template_manager import TemplateManager
    from app.theme_manager import ThemeManager
    from app.cert_auth_manager import CertAuthenticationManager
    
    console.print(f"[bold blue]🐛 DEBUG: Gerando certificados com todos os temas...[/bold blue]")
    console.print(f"- Template: [cyan]{template}[/cyan]")
    
    try:
        # Criar diretório de saída
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = os.path.join("output", f"debug_themes_{timestamp}")
        
        os.makedirs(output, exist_ok=True)
        console.print(f"- Diretório de saída: [cyan]{output}[/cyan]")
        
        # Carregar template
        with open(template, 'r', encoding='utf-8') as f:
            template_content = f.read()
        console.print(f"[green]✓[/green] Template carregado")
          # Inicializar geradores
        pdf_generator = PDFGenerator(output_dir=output)
        zip_exporter = ZipExporter()
        parameter_manager = ParameterManager()
        template_manager_obj = TemplateManager()
        theme_manager = ThemeManager()
        auth_manager = CertAuthenticationManager()
        
        # Dados para geração de código de autenticação
        nome_exemplo = "Maria Clara Desenvolvimento"
        evento_exemplo = "Curso Avançado de Desenvolvimento de Software"
        data_exemplo = "22 a 24 de maio de 2025"        
        # Gerar código de autenticação único        
        codigo_autenticacao = auth_manager.gerar_codigo_autenticacao(
            nome_participante=nome_exemplo,
            evento=evento_exemplo,
            data_evento=data_exemplo
        )
        qrcode_url = auth_manager.gerar_qrcode_data(codigo_autenticacao)
        qrcode_base64 = auth_manager.gerar_qrcode_base64(codigo_autenticacao)          # Dados de exemplo fixos
        sample_data = {
            "nome": nome_exemplo,
            "evento": evento_exemplo,
            "local": "Centro de Tecnologia e Inovação - Auditório Principal",
            "data": data_exemplo,
            "carga_horaria": "24",
            "coordenador": "Prof. Dr. Ana Carolina Fernandes",
            "diretor": "Prof. Dr. Carlos Eduardo Martins",
            "cidade": "São Paulo",            
            "data_emissao": "29 de maio de 2025",            "codigo_autenticacao": codigo_autenticacao,
            "codigo_verificacao": codigo_autenticacao,
            "url_verificacao": "https://nepemufsc.com/verificar-certificados",
            "url_qrcode": qrcode_url,
            "qrcode_base64": qrcode_base64,
            "intro_text": "Certificamos que",
            "participation_text": "participou com êxito do",
            "location_text": "realizado em",
            "date_text": "no período de",
            "workload_text": "com carga horária total de",
            "hours_text": "horas",
            "coordinator_title": "Coordenador do Programa",
            "director_title": "Diretor Acadêmico",
            "title_text": "CERTIFICADO DE PARTICIPAÇÃO"
        }
        
        # Listar temas disponíveis
        available_themes = theme_manager.list_themes()
        
        if not available_themes:
            console.print("[red]❌ Nenhum tema disponível.[/red]")
            sys.exit(1)
        
        console.print(f"[green]✓[/green] Temas encontrados: {len(available_themes)}")
        console.print(f"[cyan]Temas: {', '.join(available_themes)}[/cyan]")
        
        # Gerar certificados
        generated_files = []
        
        with console.status("[bold green]Gerando certificados...") as status:
            for i, theme_name in enumerate(available_themes, 1):
                try:
                    status.update(f"[bold green]Processando tema {i}/{len(available_themes)}: {theme_name}")
                    
                    # Carregar configurações do tema
                    theme_settings = theme_manager.load_theme(theme_name)
                    
                    # Mesclar dados com configurações do tema
                    merged_data = parameter_manager.merge_placeholders(sample_data.copy(), theme_name)
                    
                    # Criar nome temporário para o template
                    base_name = os.path.basename(template)
                    temp_name = f"temp_debug_{theme_name.replace(' ', '_').lower()}_{i}.html"
                    temp_path = os.path.join("templates", temp_name)
                    
                    try:
                        # Salvar template temporariamente
                        with open(temp_path, "w", encoding="utf-8") as f:
                            f.write(template_content)
                        
                        # Renderizar template
                        html_content = template_manager_obj.render_template(temp_name, merged_data)
                        
                        # Aplicar tema se disponível
                        if theme_settings:
                            html_content = theme_manager.apply_theme_to_template(html_content, theme_settings)
                        
                        # Gerar nome do arquivo PDF
                        safe_theme_name = theme_name.replace(" ", "_").replace("ã", "a").replace("é", "e").replace("ô", "o")
                        pdf_filename = f"certificado_tema_{safe_theme_name}.pdf"
                        pdf_path = os.path.join(output, pdf_filename)
                        
                        # Gerar PDF
                        pdf_generator.generate_pdf(html_content, pdf_path, orientation='landscape')
                        generated_files.append(pdf_path)
                        
                        console.print(f"[green]✓[/green] {theme_name} → {pdf_filename}")
                        
                    finally:
                        # Limpar arquivo temporário
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                            
                except Exception as e:
                    console.print(f"[red]❌ Erro no tema '{theme_name}': {str(e)}[/red]")
        
        # Relatório final
        console.print(f"\n[bold green]🎉 Geração concluída![/bold green]")
        console.print(f"[green]✓ {len(generated_files)} certificados gerados[/green]")
        
        # Criar arquivo ZIP se solicitado
        if zip and generated_files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"debug_temas_{timestamp}.zip"
            zip_path = os.path.join(output, zip_name)
            
            with console.status("[bold green]Criando arquivo ZIP..."):
                zip_exporter.create_zip(generated_files, zip_path)
            
            console.print(f"[bold green]✓ Arquivo ZIP criado: [/bold green]{zip_name}")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao executar debug de temas: [/bold red]{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Verificar se o usuário quer ajuda específica
    help_args = ["--help", "-h", "h", "help"]
    if len(sys.argv) > 1 and any(arg in sys.argv for arg in help_args):
        cli(["--help"])
    else:
        # Tenta exibir a tela de carregamento
        try:
            from app.loading_screen import loading_dummy
            loading_dummy(4.0)
        except ImportError:
            console.print("[yellow]Aviso: Módulo de carregamento não encontrado.[/yellow]")
        
        cli()
