#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exemplo de uso do sistema de sincronização offline do NEPEMCERT.
Este script demonstra como usar as funcionalidades de armazenamento offline
e sincronização posterior dos códigos de autenticação.
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.offline_sync_manager import OfflineSyncManager, CertificateRecord
from app.auto_sync_service import AutoSyncService
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def exemplo_armazenamento_offline():
    """Demonstra como armazenar certificados offline."""
    console.print("[bold blue]📦 Exemplo: Armazenamento Offline de Certificados[/bold blue]\n")
    
    # Inicializar gerenciador
    sync_manager = OfflineSyncManager()
    
    # Dados de exemplo
    certificados_exemplo = [
        {
            'codigo_autenticacao': 'abc123def456ghi789',
            'nome_participante': 'Maria Silva Santos',
            'evento': 'Workshop de Desenvolvimento Web Avançado',
            'data_evento': '15 a 17 de junho de 2025',
            'local_evento': 'Centro de Tecnologia UFSC',
            'carga_horaria': '24',
            'coordenador': 'Prof. Dr. João Carlos Silva',
            'diretor': 'Prof. Dra. Ana Maria Costa',
            'data_geracao': datetime.now().isoformat(),
            'url_verificacao': 'https://nepemufsc.com/verificar-certificados',
            'qrcode_base64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'template_usado': 'certificado_v1_basico.html',
            'tema_usado': 'contemporaneo_elegante'
        },
        {
            'codigo_autenticacao': 'xyz789abc123def456',
            'nome_participante': 'Carlos Eduardo Oliveira',
            'evento': 'Curso de Python para Ciência de Dados',
            'data_evento': '20 a 22 de junho de 2025',
            'local_evento': 'Laboratório de Informática - UFSC',
            'carga_horaria': '30',
            'coordenador': 'Prof. Dr. Roberto Silva',
            'diretor': 'Prof. Dra. Fernanda Santos',
            'data_geracao': datetime.now().isoformat(),
            'url_verificacao': 'https://nepemufsc.com/verificar-certificados',
            'qrcode_base64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            'template_usado': 'certificado_v1_basico.html',
            'tema_usado': 'academico_classico'
        }
    ]
    
    # Armazenar certificados
    console.print("🔄 Armazenando certificados offline...")
    for i, cert_data in enumerate(certificados_exemplo, 1):
        success = sync_manager.store_certificate(cert_data)
        status = "✅ Sucesso" if success else "❌ Erro"
        console.print(f"  {i}. {cert_data['nome_participante']}: {status}")
    
    console.print("\n📊 Certificados armazenados para sincronização posterior!")
    
    # Mostrar estatísticas
    stats = sync_manager.get_sync_statistics()
    console.print(f"  • Total de registros: {stats.get('total_records', 0)}")
    console.print(f"  • Pendentes: {stats.get('pending_count', 0)}")
    console.print(f"  • Banco de dados: {stats.get('db_path', 'N/A')}")
    
    sync_manager.close()


def exemplo_consulta_pendentes():
    """Demonstra como consultar certificados pendentes."""
    console.print("\n[bold blue]📋 Exemplo: Consulta de Certificados Pendentes[/bold blue]\n")
    
    sync_manager = OfflineSyncManager()
    
    # Obter certificados pendentes
    pendentes = sync_manager.get_pending_certificates(limit=10)
    
    if not pendentes:
        console.print("[yellow]ℹ️ Nenhum certificado pendente encontrado[/yellow]")
        sync_manager.close()
        return
    
    # Criar tabela
    table = Table(title=f"Certificados Pendentes ({len(pendentes)} encontrados)", box=box.ROUNDED)
    table.add_column("Nome", style="bold", width=25)
    table.add_column("Evento", style="cyan", width=30)
    table.add_column("Status", style="yellow")
    table.add_column("Tentativas", justify="right")
    table.add_column("Criado", style="dim")
    
    # Adicionar linhas
    for cert in pendentes:
        table.add_row(
            cert.nome_participante[:22] + "..." if len(cert.nome_participante) > 22 else cert.nome_participante,
            cert.evento[:27] + "..." if len(cert.evento) > 27 else cert.evento,
            cert.sync_status,
            str(cert.sync_attempts),
            cert.created_at[:16] if cert.created_at else "N/A"
        )
    
    console.print(table)
    sync_manager.close()


def exemplo_criacao_pacote():
    """Demonstra como criar pacotes de sincronização."""
    console.print("\n[bold blue]📦 Exemplo: Criação de Pacote de Sincronização[/bold blue]\n")
    
    sync_manager = OfflineSyncManager()
    
    console.print("🔄 Criando pacote de sincronização...")
    package_path = sync_manager.create_sync_package(max_records=5)
    
    if package_path:
        console.print(f"[bold green]✅ Pacote criado com sucesso![/bold green]")
        console.print(f"📁 Localização: [cyan]{package_path}[/cyan]")
        
        # Mostrar informações do arquivo
        if os.path.exists(package_path):
            file_size = os.path.getsize(package_path)
            console.print(f"📏 Tamanho: {file_size} bytes")
    else:
        console.print("[yellow]⚠️ Nenhum certificado disponível para empacotamento[/yellow]")
    
    sync_manager.close()


def exemplo_servico_automatico():
    """Demonstra o serviço de sincronização automática."""
    console.print("\n[bold blue]🚀 Exemplo: Serviço de Sincronização Automática[/bold blue]\n")
    
    # Configurar serviço
    service = AutoSyncService(
        server_url="https://nepemufsc.com/api",
        check_interval=10,  # Verificar a cada 10 segundos
        batch_size=3        # Sincronizar 3 certificados por vez
    )
    
    # Callbacks para demonstração
    def on_sync_success(cert):
        console.print(f"[green]✅ Sincronizado: {cert.nome_participante}[/green]")
    
    def on_sync_error(cert, error_msg):
        console.print(f"[red]❌ Erro em {cert.nome_participante}: {error_msg}[/red]")
    
    def on_connectivity_change(old_status, new_status):
        if new_status:
            console.print("[bold green]🌐 Conectividade restaurada![/bold green]")
        else:
            console.print("[bold yellow]📡 Conectividade perdida - modo offline[/bold yellow]")
    
    # Registrar callbacks
    service.add_callback('sync_success', on_sync_success)
    service.add_callback('sync_error', on_sync_error)
    service.add_callback('connectivity_change', on_connectivity_change)
    
    console.print("🔄 Iniciando serviço de sincronização automática...")
    console.print("[dim]O serviço irá verificar conectividade e sincronizar automaticamente[/dim]")
    console.print("[dim]Pressione Ctrl+C para parar[/dim]\n")
    
    try:
        # Iniciar serviço
        service.start()
        
        # Mostrar status inicial
        status = service.get_service_status()
        console.print(f"📊 Status: {'🟢 Rodando' if status['running'] else '🔴 Parado'}")
        console.print(f"🌐 Conectividade: {'✅ Conectado' if status['connected'] else '❌ Desconectado'}")
        console.print(f"📋 Certificados pendentes: {status['pending_certificates']}")
        
        # Simular execução por um tempo limitado
        import time
        console.print("\n[dim]Simulando execução por 30 segundos...[/dim]")
        
        for i in range(30):
            time.sleep(1)
            if i % 10 == 0 and i > 0:
                console.print(f"[dim]• {i}s - Serviço rodando...[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Interrompido pelo usuário[/yellow]")
    
    finally:
        console.print("🛑 Parando serviço...")
        service.stop()
        console.print("[green]✅ Serviço parado[/green]")


def exemplo_backup_e_limpeza():
    """Demonstra backup e limpeza do banco de dados."""
    console.print("\n[bold blue]🧹 Exemplo: Backup e Limpeza[/bold blue]\n")
    
    sync_manager = OfflineSyncManager()
    
    # Criar backup
    console.print("💾 Criando backup do banco de dados...")
    backup_path = sync_manager.backup_database()
    
    if backup_path:
        console.print(f"[bold green]✅ Backup criado![/bold green]")
        console.print(f"📁 Localização: [cyan]{backup_path}[/cyan]")
    else:
        console.print("[red]❌ Erro ao criar backup[/red]")
    
    # Simular limpeza (comentado para não remover dados reais)
    console.print("\n🧹 Simulando limpeza de registros antigos...")
    console.print("[dim]# removed_count = sync_manager.cleanup_synced_records(days_old=30)[/dim]")
    console.print("[dim]# console.print(f'Removidos {removed_count} registros antigos')[/dim]")
    console.print("[yellow]ℹ️ Limpeza não executada neste exemplo[/yellow]")
    
    sync_manager.close()


def main():
    """Função principal que executa todos os exemplos."""
    console.print("[bold green]🎯 NEPEMCERT - Exemplos de Sincronização Offline[/bold green]")
    console.print("[dim]Este script demonstra as funcionalidades do sistema de sincronização offline[/dim]\n")
    
    try:
        # Executar exemplos
        exemplo_armazenamento_offline()
        exemplo_consulta_pendentes()
        exemplo_criacao_pacote()
        exemplo_servico_automatico()
        exemplo_backup_e_limpeza()
        
        console.print("\n[bold green]🎉 Todos os exemplos foram executados com sucesso![/bold green]")
        console.print("\n[cyan]Para usar em produção:[/cyan]")
        console.print("  • Use [bold]nepemcert sync --stats[/bold] para ver estatísticas")
        console.print("  • Use [bold]nepemcert auto-sync --start --daemon[/bold] para sincronização automática")
        console.print("  • Use [bold]nepemcert sync --package[/bold] para criar pacotes manualmente")
        
    except Exception as e:
        console.print(f"[bold red]❌ Erro durante execução: {str(e)}[/bold red]")
        import traceback
        console.print("[dim]" + traceback.format_exc() + "[/dim]")


if __name__ == "__main__":
    main()
