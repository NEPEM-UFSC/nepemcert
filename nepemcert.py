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

# Importar o módulo CLI melhorado
from cli import main as cli_main

# Console Rich para saída formatada
console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="1.1.0", prog_name="NEPEM Certificados")
def cli(ctx):
    """NEPEM Certificados - Gerador de certificados em lote via linha de comando."""
    # Se nenhum comando foi especificado, executa o modo interativo
    if ctx.invoked_subcommand is None:
        cli_main()


@cli.command()
def interactive():
    """Inicia a interface interativa do gerador de certificados."""
    cli_main()


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
    # Importações necessárias
    import pandas as pd
    from app.certificate_service import CertificateService # Import CertificateService
    from app.zip_exporter import ZipExporter
    from app.template_manager import TemplateManager as GlobalTemplateManager # Alias for local instance
    
    console.print(f"[bold blue]Gerando certificados...[/bold blue]")
    console.print(f"- Arquivo CSV: [cyan]{csv_file}[/cyan]")
    console.print(f"- Template: [cyan]{template}[/cyan]")
    console.print(f"- Diretório de saída: [cyan]{output}[/cyan]")
    
    try:
        # Criar diretório de saída se não existir
        os.makedirs(output, exist_ok=True)
        
        # Instantiate CertificateService
        certificate_service = CertificateService(output_dir=output)
        # ZipExporter is still needed for zipping after generation
        zip_exporter = ZipExporter()
        # TemplateManager instance for temporary template handling by this command
        cli_template_manager = GlobalTemplateManager()

        # Prepare template for the service:
        # The service expects template_name to be a file in its managed templates_dir.
        # So, we read the template provided by path, save it to the managed dir,
        # then pass its basename to the service.
        template_file_name = os.path.basename(template)
        original_template_in_managed_dir = False
        managed_template_path = os.path.join(cli_template_manager.templates_dir, template_file_name)

        try:
            # Check if the source template is already in the managed directory
            if os.path.abspath(template) == os.path.abspath(managed_template_path):
                original_template_in_managed_dir = True
                console.print(f"[dim]Template '{template_file_name}' já está no diretório gerenciado.[/dim]")
            else:
                with open(template, 'r', encoding='utf-8') as f:
                    original_template_content = f.read()
                # Save it to the managed directory so the service can find it by name
                cli_template_manager.save_template(template_file_name, original_template_content)
                console.print(f"[green]✓[/green] Template '{template_file_name}' preparado para o serviço (copiado para {cli_template_manager.templates_dir}).")
        except Exception as e:
            console.print(f"[bold red]Erro ao preparar template '{template}': [/bold red]{str(e)}")
            sys.exit(1)

        # Carregar dados do CSV (for count display, actual processing by service)
        try:
            df = pd.read_csv(csv_file) # Still load for count, service handles actual data loading
            console.print(f"[green]✓[/green] Arquivo CSV '{csv_file}' carregado: {len(df)} registros indicados para processamento.")
        except Exception as e:
            console.print(f"[bold red]Erro ao carregar CSV '{csv_file}': [/bold red]{str(e)}")
            # Attempt to remove temporary template before exiting if it was copied
            if not original_template_in_managed_dir and os.path.exists(managed_template_path):
                try:
                    os.remove(managed_template_path)
                    console.print(f"[dim]Template temporário '{template_file_name}' limpo após erro.[/dim]")
                except Exception as e_clean:
                    console.print(f"[yellow]Aviso: Não foi possível limpar o template temporário '{template_file_name}' ao sair: {str(e_clean)}[/yellow]")
            sys.exit(1)

        # Parameters for the service call
        event_data = {} # Event details are not directly prompted in this CLI mode; service relies on CSV/parameters.json
        theme_name = None # Themes are not supported in this CLI mode currently
        has_header = True # Default assumption for this CLI mode; CSVs for batch usually have headers.

        console.print(f"Chamando CertificateService para geração em lote...")
        # Call the service to generate certificates
        generation_result = certificate_service.generate_certificates_batch(
            csv_file_path=csv_file,
            event_details=event_data,
            template_name=template_file_name, # Basename of the template path
            theme_name=theme_name,
            has_header=has_header
        )

        # Cleanup temporary template if it was copied
        if not original_template_in_managed_dir and os.path.exists(managed_template_path):
            try:
                os.remove(managed_template_path)
                console.print(f"[dim]Template temporário '{template_file_name}' limpo.[/dim]")
            except FileNotFoundError: # Should not happen if os.path.exists was true, but good practice
                console.print(f"[dim]Template temporário '{template_file_name}' já havia sido removido ou não existia.[/dim]")
            except Exception as e:
                console.print(f"[yellow]Aviso: Não foi possível limpar o template temporário '{template_file_name}': {str(e)}[/yellow]")

        # Handle Results from CertificateService
        if generation_result["success_count"] > 0:
            console.print(f"[bold green]✓ {generation_result['success_count']} certificados gerados com sucesso![/bold green]")
            # Optional: list all generated files
            # for file_path in generation_result["generated_files"]:
            #     console.print(f"  [green]•[/green] {file_path}")

        if generation_result["failed_count"] > 0:
            console.print(f"[bold red]✗ {generation_result['failed_count']} certificados falharam ao gerar.[/bold red]")

        if generation_result["errors"]:
            console.print("\n[bold yellow]Erros e Avisos durante a geração:[/bold yellow]")
            for error_msg in generation_result["errors"]:
                console.print(f"  [yellow]•[/yellow] {error_msg}")
        
        # Criar arquivo ZIP se solicitado and if files were generated
        if zip and generation_result["generated_files"]:
            if not zip_name:
                from datetime import datetime
                # A more descriptive default name could use event name if available from parameters
                # For now, using a timestamped generic name.
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
    from app.connectivity_manager import ConnectivityManager
    
    # Inicializar gerenciador de conectividade
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
@click.option("--stats", is_flag=True, help="Mostrar estatísticas de sincronização")
@click.option("--package", is_flag=True, help="Criar pacote de sincronização")
@click.option("--pending", is_flag=True, help="Listar certificados pendentes")
@click.option("--cleanup", type=int, metavar="DAYS", help="Limpar registros sincronizados com mais de N dias")
@click.option("--backup", is_flag=True, help="Criar backup do banco de dados offline")
def sync(stats, package, pending, cleanup, backup):
    """Gerencia a sincronização offline de códigos de autenticação."""
    from app.offline_sync_manager import OfflineSyncManager
    from rich.table import Table
    from rich import box
    
    # Inicializar gerenciador de sincronização offline
    sync_manager = OfflineSyncManager()
    
    try:
        if stats:
            console.print("[bold blue]📊 Estatísticas de Sincronização Offline[/bold blue]\n")
            
            statistics = sync_manager.get_sync_statistics()
            
            if not statistics:
                console.print("[red]❌ Erro ao obter estatísticas[/red]")
                return
            
            # Tabela de status
            status_table = Table(title="Status dos Certificados", box=box.ROUNDED)
            status_table.add_column("Status", style="bold")
            status_table.add_column("Quantidade", style="cyan", justify="right")
            
            status_counts = statistics.get('status_counts', {})
            status_table.add_row("📋 Pendentes", str(status_counts.get('pending', 0)))
            status_table.add_row("✅ Sincronizados", str(status_counts.get('synced', 0)))
            status_table.add_row("❌ Falharam", str(status_counts.get('failed', 0)))
            status_table.add_row("🔄 Aguardando retry", str(status_counts.get('retry', 0)))
            status_table.add_row("📊 Total", str(statistics.get('total_records', 0)), style="bold green")
            
            console.print(status_table)
            console.print()
            
            # Informações adicionais
            console.print(f"📈 Últimas 24h: [cyan]{statistics.get('last_24h_count', 0)}[/cyan] novos certificados")
            console.print(f"🔢 Média de tentativas: [yellow]{statistics.get('avg_sync_attempts', 0):.1f}[/yellow]")
            console.print(f"🎯 Máx. tentativas: [red]{statistics.get('max_sync_attempts', 0)}[/red]")
            console.print(f"💾 Banco de dados: [dim]{statistics.get('db_path', 'N/A')}[/dim]")
            
        elif package:
            console.print("[bold blue]📦 Criando pacote de sincronização...[/bold blue]")
            
            with console.status("[bold green]Preparando pacote..."):
                package_path = sync_manager.create_sync_package()
            
            if package_path:
                console.print(f"[bold green]✅ Pacote criado com sucesso![/bold green]")
                console.print(f"📁 Localização: [cyan]{package_path}[/cyan]")
            else:
                console.print("[yellow]⚠️ Nenhum certificado pendente para empacotamento[/yellow]")
                
        elif pending:
            console.print("[bold blue]📋 Certificados Pendentes de Sincronização[/bold blue]\n")
            
            pending_certs = sync_manager.get_pending_certificates(limit=50)
            
            if not pending_certs:
                console.print("[green]🎉 Todos os certificados estão sincronizados![/green]")
                return
            
            # Tabela de certificados pendentes
            pending_table = Table(title=f"Primeiros {len(pending_certs)} certificados pendentes", box=box.SIMPLE)
            pending_table.add_column("Nome", style="bold")
            pending_table.add_column("Evento", style="cyan")
            pending_table.add_column("Status", style="yellow")
            pending_table.add_column("Tentativas", justify="right")
            pending_table.add_column("Criado em", style="dim")
            
            for cert in pending_certs:
                status_emoji = {
                    'pending': '⏳',
                    'failed': '❌',
                    'retry': '🔄'
                }.get(cert.sync_status, '❓')
                
                pending_table.add_row(
                    cert.nome_participante[:30] + "..." if len(cert.nome_participante) > 30 else cert.nome_participante,
                    cert.evento[:40] + "..." if len(cert.evento) > 40 else cert.evento,
                    f"{status_emoji} {cert.sync_status}",
                    str(cert.sync_attempts),
                    cert.created_at[:16] if cert.created_at else "N/A"
                )
            
            console.print(pending_table)
            
            if len(pending_certs) == 50:
                console.print("\n[dim]... mostrando apenas os primeiros 50 registros[/dim]")
                
        elif cleanup is not None:
            console.print(f"[bold blue]🧹 Limpando registros sincronizados com mais de {cleanup} dias...[/bold blue]")
            
            with console.status("[bold yellow]Executando limpeza..."):
                removed_count = sync_manager.cleanup_synced_records(days_old=cleanup)
            
            if removed_count > 0:
                console.print(f"[bold green]✅ {removed_count} registros removidos com sucesso![/bold green]")
            else:
                console.print("[yellow]ℹ️ Nenhum registro foi removido[/yellow]")
                
        elif backup:
            console.print("[bold blue]💾 Criando backup do banco de dados...[/bold blue]")
            
            with console.status("[bold green]Criando backup..."):
                backup_path = sync_manager.backup_database()
            
            if backup_path:
                console.print(f"[bold green]✅ Backup criado com sucesso![/bold green]")
                console.print(f"📁 Localização: [cyan]{backup_path}[/cyan]")
            else:
                console.print("[red]❌ Erro ao criar backup[/red]")
                
        else:
            console.print("[bold blue]🔄 Gerenciamento de Sincronização Offline[/bold blue]")            
            console.print("\n[yellow]Escolha uma das opções disponíveis:[/yellow]")
            console.print("  [cyan]--stats[/cyan]     Mostrar estatísticas detalhadas")
            console.print("  [cyan]--package[/cyan]   Criar pacote de sincronização")
            console.print("  [cyan]--pending[/cyan]   Listar certificados pendentes")
            console.print("  [cyan]--cleanup N[/cyan] Limpar registros antigos (N dias)")
            console.print("  [cyan]--backup[/cyan]    Criar backup do banco")
            console.print("\n[dim]Exemplo: nepemcert sync --stats[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Erro ao executar operação de sincronização: {str(e)}[/bold red]")
    finally:
        sync_manager.close()


@cli.command("auto-sync")
@click.option("--start", is_flag=True, help="Iniciar serviço de sincronização automática")
@click.option("--stop", is_flag=True, help="Parar serviço de sincronização automática")
@click.option("--status", is_flag=True, help="Status do serviço de sincronização")
@click.option("--force", is_flag=True, help="Forçar sincronização imediata")
@click.option("--daemon", is_flag=True, help="Executar como daemon (background)")
def auto_sync(start, stop, status, force, daemon):
    """Gerencia o serviço de sincronização automática."""
    from app.auto_sync_service import AutoSyncService
    from rich.table import Table
    from rich import box
    import signal
    import sys
    
    service = AutoSyncService()
    
    try:
        if start:
            console.print("[bold blue]🚀 Iniciando serviço de sincronização automática...[/bold blue]")
            
            # Callbacks para mostrar progresso
            def on_sync_success(cert):
                console.print(f"[green]✅ Sincronizado: {cert.nome_participante}[/green]")
            
            def on_sync_error(cert, error_msg):
                console.print(f"[red]❌ Erro em {cert.nome_participante}: {error_msg}[/red]")
            
            def on_connectivity_change(old_status, new_status):
                if new_status:
                    console.print("[bold green]🌐 Conectividade restaurada - sincronização ativa[/bold green]")
                else:
                    console.print("[bold yellow]📡 Conectividade perdida - modo offline[/bold yellow]")
            
            # Registrar callbacks
            service.add_callback('sync_success', on_sync_success)
            service.add_callback('sync_error', on_sync_error)
            service.add_callback('connectivity_change', on_connectivity_change)
            
            # Iniciar serviço
            service.start()
            
            if daemon:
                console.print("[bold green]✅ Serviço iniciado em modo daemon[/bold green]")
                console.print("[dim]Pressione Ctrl+C para parar o serviço[/dim]")
                
                # Configurar handler para SIGINT (Ctrl+C)
                def signal_handler(sig, frame):
                    console.print("\n[yellow]🛑 Parando serviço...[/yellow]")
                    service.stop()
                    console.print("[green]✅ Serviço parado[/green]")
                    sys.exit(0)
                
                signal.signal(signal.SIGINT, signal_handler)
                
                # Manter o programa rodando
                try:
                    while True:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
            else:
                console.print("[bold green]✅ Serviço iniciado[/bold green]")
                console.print("[yellow]⚠️ O serviço rodará apenas durante esta sessão[/yellow]")
                
        elif stop:
            console.print("[bold yellow]🛑 Parando serviço de sincronização...[/bold yellow]")
            service.stop()
            console.print("[green]✅ Serviço parado[/green]")
            
        elif status:
            console.print("[bold blue]📊 Status do Serviço de Sincronização Automática[/bold blue]\n")
            
            service_status = service.get_service_status()
            
            # Tabela de status
            status_table = Table(title="Status do Serviço", box=box.ROUNDED)
            status_table.add_column("Propriedade", style="bold")
            status_table.add_column("Valor", style="cyan")
            
            # Status principal
            running_emoji = "🟢" if service_status['running'] else "🔴"
            connected_emoji = "🌐" if service_status['connected'] else "📡"
            
            status_table.add_row("Status do Serviço", f"{running_emoji} {'Rodando' if service_status['running'] else 'Parado'}")
            status_table.add_row("Conectividade", f"{connected_emoji} {'Conectado' if service_status['connected'] else 'Desconectado'}")
            status_table.add_row("Certificados Pendentes", str(service_status['pending_certificates']))
            status_table.add_row("URL do Servidor", service_status['server_url'])
            
            # Tempos
            if service_status['last_sync_time']:
                status_table.add_row("Última Sincronização", service_status['last_sync_time'][:19])
            if service_status['uptime_seconds']:
                uptime_str = f"{service_status['uptime_seconds']:.0f}s"
                if service_status['uptime_seconds'] > 3600:
                    hours = service_status['uptime_seconds'] // 3600
                    minutes = (service_status['uptime_seconds'] % 3600) // 60
                    uptime_str = f"{hours:.0f}h {minutes:.0f}m"
                elif service_status['uptime_seconds'] > 60:
                    minutes = service_status['uptime_seconds'] // 60
                    seconds = service_status['uptime_seconds'] % 60
                    uptime_str = f"{minutes:.0f}m {seconds:.0f}s"
                status_table.add_row("Tempo de Execução", uptime_str)
            
            console.print(status_table)
            
            # Estatísticas
            stats = service_status['stats']
            if any(stats.values()):
                console.print()
                stats_table = Table(title="Estatísticas", box=box.SIMPLE)
                stats_table.add_column("Métrica", style="bold")
                stats_table.add_column("Valor", style="green", justify="right")
                
                stats_table.add_row("Total Sincronizado", str(stats['total_synced']))
                stats_table.add_row("Total Falharam", str(stats['total_failed']))
                stats_table.add_row("Verificações de Conectividade", str(stats['connectivity_checks']))
                
                console.print(stats_table)
            
            # Configurações
            config = service_status['config']
            console.print()
            config_table = Table(title="Configurações", box=box.SIMPLE)
            config_table.add_column("Parâmetro", style="bold")
            config_table.add_column("Valor", style="cyan")
            
            config_table.add_row("Intervalo de Verificação", f"{config['check_interval']}s")
            config_table.add_row("Tamanho do Lote", str(config['batch_size']))
            config_table.add_row("Máx. Simultâneos", str(config['max_concurrent']))
            config_table.add_row("Intervalo Mín. Sync", f"{config['min_sync_interval']}s")
            
            console.print(config_table)
            
        elif force:
            console.print("[bold blue]⚡ Forçando sincronização imediata...[/bold blue]")
            
            with console.status("[bold green]Sincronizando..."):
                result = service.force_sync()
            
            if 'error' in result:
                console.print(f"[red]❌ Erro: {result['error']}[/red]")
            else:
                console.print(f"[bold green]✅ Sincronização concluída![/bold green]")
                console.print(f"  📊 Sucessos: [green]{result['success']}[/green]")
                console.print(f"  📊 Falhas: [red]{result['failed']}[/red]")
                
        else:
            console.print("[bold blue]🔄 Serviço de Sincronização Automática[/bold blue]")
            console.print("\n[yellow]Opções disponíveis:[/yellow]")
            console.print("  [cyan]--start[/cyan]      Iniciar serviço")
            console.print("  [cyan]--start --daemon[/cyan] Iniciar como daemon")
            console.print("  [cyan]--stop[/cyan]       Parar serviço")
            console.print("  [cyan]--status[/cyan]     Ver status detalhado")
            console.print("  [cyan]--force[/cyan]      Forçar sincronização")
            console.print("\n[dim]Exemplo: nepemcert auto-sync --start --daemon[/dim]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Erro no serviço de sincronização: {str(e)}[/bold red]")
    finally:
        if 'service' in locals():
            service.stop()


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
    from app.cert_auth_manager import AuthenticationManager
    
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
        auth_manager = AuthenticationManager()
        
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
        # Exibir ajuda normal do Click
        cli(["--help"])
    else:
        # Tenta exibir a tela de carregamento dummy antes de iniciar
        try:
            from app.loading_screen import loading_dummy
            loading_dummy(4.0)  # Exibe por 4 segundos (só será exibido uma vez)
        except ImportError:
            # Se não conseguir importar, continua normalmente
            console.print("[yellow]Aviso: Módulo de carregamento não encontrado.[/yellow]")
        
        # Se não for solicitação de ajuda, executar normalmente
        cli()
