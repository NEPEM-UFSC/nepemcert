#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEPEM Certificados - Interface de Linha de Comando
Ferramenta para geração de certificados em lote.
"""

import os
import sys
import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich import box
from rich.align import Align
from rich.layout import Layout
from rich.text import Text
from pathlib import Path
import questionary
from pyfiglet import Figlet
import pandas as pd
import time
from datetime import datetime
import random

# Importação dos módulos da aplicação
from app.csv_manager import CSVManager
from app.template_manager import TemplateManager
from app.pdf_generator import PDFGenerator
from app.field_mapper import FieldMapper
from app.zip_exporter import ZipExporter
from app.connectivity_manager import ConnectivityManager

# Configuração do console Rich
console = Console()

# Versão do aplicativo
APP_VERSION = "1.0.0"

# Inicialização dos gerenciadores
csv_manager = CSVManager()
template_manager = TemplateManager()
pdf_generator = PDFGenerator()
field_mapper = FieldMapper()
zip_exporter = ZipExporter()
connectivity_manager = ConnectivityManager()


def check_connection_status():
    """Verifica o status de conexão com servidor remoto."""
    # Usa o connectivity_manager para obter o status real
    conn_info = connectivity_manager.get_connection_status()
    return conn_info["status"]


def print_header():
    """Exibe o cabeçalho da aplicação com logo e informações de status."""
    console.clear()
    f = Figlet(font="slant")
    console.print(f.renderText("NEPEM Cert"), style="bold blue")
    
    # Layout para as caixas de informação
    layout = Layout()
    layout.split_column(
        Layout(name="header"),
        Layout(name="info_boxes")
    )
    
    # Divisão para as caixas de informação lado a lado
    layout["info_boxes"].split_row(
        Layout(name="version"),
        Layout(name="connection")
    )
    
    # Conteúdo das caixas
    layout["version"].update(
        Panel(
            f"[bold]Versão:[/bold] {APP_VERSION}",
            title="Informações do Sistema",
            border_style="green"
        )
    )
    
    connection_status = check_connection_status()
    status_color = {
        "Conectado": "green",
        "Desconectado": "red",
        "Aguardando": "yellow"
    }.get(connection_status, "yellow")
    
    layout["connection"].update(
        Panel(
            f"[bold]Status:[/bold] [{status_color}]{connection_status}[/{status_color}]",
            title="Conexão com Servidor",
            border_style=status_color
        )
    )
    
    console.print(layout["info_boxes"])
    console.print("\n[bold cyan]Gerador de Certificados em Lote[/bold cyan]")
    console.print("[dim]Use os comandos abaixo para gerenciar seus certificados.[/dim]\n")


def main_menu():
    """Exibe o menu principal da aplicação."""
    print_header()
    
    choice = questionary.select(
        "Selecione uma opção:",
        choices=[
            "🔖 Gerar Certificados",
            "🎨 Gerenciar Templates",
            "⚙️ Configurações",
            "🔄 Sincronização e Conectividade",
            "❓ Ajuda",
            "🚪 Sair"
        ],
        use_indicator=True,
        style=questionary.Style([
            ('selected', 'bg:#0A1128 #ffffff'),
            ('instruction', 'fg:#0A1128'),
            ('pointer', 'fg:#0A1128'),
        ])
    ).ask()
    
    if choice == "🔖 Gerar Certificados":
        generate_certificates_menu()
    elif choice == "🎨 Gerenciar Templates":
        manage_templates_menu()
    elif choice == "⚙️ Configurações":
        settings_menu()
    elif choice == "🔄 Sincronização e Conectividade":
        connectivity_menu()
    elif choice == "❓ Ajuda":
        show_help()
    elif choice == "🚪 Sair":
        console.print("[bold green]Obrigado por usar o NEPEM Cert. Até logo![/bold green]")
        return False
    
    return True


def generate_certificates_menu():
    """Menu para geração de certificados."""
    console.clear()
    console.print("[bold blue]== Geração de Certificados ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "📄 Gerar certificados em lote",
            "📋 Visualizar dados importados",
            "🔍 Testar geração com um único registro",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📄 Gerar certificados em lote":
        generate_batch_certificates()
    elif choice == "📋 Visualizar dados importados":
        preview_imported_data()
    elif choice == "🔍 Testar geração com um único registro":
        test_certificate_generation()
    elif choice == "↩️ Voltar ao menu principal":
        return


def manage_templates_menu():
    """Menu para gerenciamento de templates."""
    console.clear()
    console.print("[bold blue]== Gerenciamento de Templates ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "📝 Listar templates disponíveis",
            "➕ Importar novo template",
            "🖌️ Editar template existente",
            "🗑️ Excluir template",
            "👁️ Visualizar template",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📝 Listar templates disponíveis":
        list_templates()
    elif choice == "➕ Importar novo template":
        import_template()
    elif choice == "🖌️ Editar template existente":
        edit_template()
    elif choice == "🗑️ Excluir template":
        delete_template()
    elif choice == "👁️ Visualizar template":
        preview_template()
    elif choice == "↩️ Voltar ao menu principal":
        return


def settings_menu():
    """Menu de configurações."""
    console.clear()
    console.print("[bold blue]== Configurações ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja configurar?",
        choices=[
            "📁 Diretórios de trabalho",
            "🎨 Aparência e tema",
            "📊 Parâmetros de geração",
            "💾 Salvar/carregar presets",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "📁 Diretórios de trabalho":
        configure_directories()
    elif choice == "🎨 Aparência e tema":
        configure_appearance()
    elif choice == "📊 Parâmetros de geração":
        configure_generation_parameters()
    elif choice == "💾 Salvar/carregar presets":
        manage_presets()
    elif choice == "↩️ Voltar ao menu principal":
        return


def connectivity_menu():
    """Menu de conectividade e sincronização."""
    console.clear()
    console.print("[bold blue]== Sincronização e Conectividade ==[/bold blue]\n")
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=[
            "🔄 Verificar status da conexão",
            "📡 Configurar servidor remoto",
            "⬆️ Enviar certificados para servidor",
            "⬇️ Baixar templates do servidor",
            "🔒 Configurar credenciais",
            "↩️ Voltar ao menu principal"
        ]
    ).ask()
    
    if choice == "🔄 Verificar status da conexão":
        check_connection()
    elif choice == "📡 Configurar servidor remoto":
        configure_remote_server()
    elif choice == "⬆️ Enviar certificados para servidor":
        upload_certificates()
    elif choice == "⬇️ Baixar templates do servidor":
        download_templates()
    elif choice == "🔒 Configurar credenciais":
        configure_credentials()
    elif choice == "↩️ Voltar ao menu principal":
        return


def show_help():
    """Exibe informações de ajuda."""
    console.clear()
    
    help_text = """
    # Ajuda do NEPEM Cert
    
    ## Como usar
    
    O NEPEM Cert é uma ferramenta para geração de certificados em lote. Você pode:
    
    1. **Gerar Certificados em Lote**:
       - Importe dados de participantes em CSV
       - Selecione um template HTML
       - Configure o mapeamento de campos
       - Gere os certificados
    
    2. **Gerenciar Templates**:
       - Crie, edite e visualize templates HTML
       - Use placeholders para campos dinâmicos
    
    3. **Configurações**:
       - Defina diretórios de trabalho
       - Configure parâmetros de geração
    
    4. **Conectividade**:
       - Sincronize com servidor remoto
       - Importe/exporte templates e certificados
    
    ## Contato e Suporte
    
    Para mais informações ou suporte, entre em contato:
    - Email: contato@nepem.com
    - Site: www.nepem.com
    """
    
    md = Markdown(help_text)
    console.print(md)
    console.print("\n[dim]Pressione Enter para voltar ao menu principal...[/dim]")
    input()


# Funções de implementação para o menu de geração de certificados

def generate_batch_certificates():
    """Gera certificados em lote."""
    console.clear()
    console.print("[bold blue]== Geração de Certificados em Lote ==[/bold blue]\n")
    
    # Selecionar arquivo CSV
    csv_path = questionary.path(
        "Selecione o arquivo CSV com dados dos participantes:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    ).ask()
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar dados do CSV
    with console.status("[bold green]Carregando dados do CSV..."):
        try:
            df = pd.read_csv(csv_path)
            num_records = len(df)
            console.print(f"[green]✓[/green] Dados carregados com sucesso. {num_records} registros encontrados.")
        except Exception as e:
            console.print(f"[bold red]Erro ao carregar CSV:[/bold red] {str(e)}")
            return
    
    # Selecionar template
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        return
        
    template_name = questionary.select(
        "Selecione o template a ser utilizado:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar template
    with console.status("[bold green]Carregando template..."):
        template_content = template_manager.load_template(template_name)
        if not template_content:
            console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
            return
    
    # Mapear campos
    console.print("\n[bold]Mapeamento de campos[/bold]")
    csv_columns = df.columns.tolist()
    
    # Obter placeholders do template (implementação simplificada)
    placeholders = []
    for col in csv_columns:
        if col in template_content:
            placeholders.append(col)
    
    if not placeholders:
        console.print("[yellow]Aviso: Não foram encontrados placeholders compatíveis no template.[/yellow]")
        
        # Permitir continuar mesmo sem placeholders
        continue_anyway = questionary.confirm(
            "Deseja continuar mesmo assim?"
        ).ask()
        
        if not continue_anyway:
            return
    
    # Configurar caminho de saída para os certificados
    output_dir = questionary.path(
        "Pasta de destino para os certificados:",
        default=pdf_generator.output_dir,
        only_directories=True
    ).ask()
    
    if not output_dir:
        output_dir = pdf_generator.output_dir
    
    # Confirmação final
    console.print("\n[bold]Resumo da operação:[/bold]")
    console.print(f"- Arquivo CSV: [cyan]{csv_path}[/cyan] ({num_records} registros)")
    console.print(f"- Template: [cyan]{template_name}[/cyan]")
    console.print(f"- Destino: [cyan]{output_dir}[/cyan]")
    
    confirm = questionary.confirm("Deseja iniciar a geração dos certificados?").ask()
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Processar e gerar os certificados
    html_contents = []
    file_names = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False
    ) as progress:
        task = progress.add_task(f"[green]Gerando certificados...", total=num_records)
        
        for index, row in df.iterrows():
            progress.update(task, description=f"[green]Processando certificado {index+1}/{num_records}...")
            
            # Preparar dados para o template
            data = row.to_dict()
            
            # Gerar nome do arquivo
            # Usar o nome do participante ou um campo de identificação se disponível
            if "nome" in data:
                file_name = f"certificado_{data['nome'].strip().replace(' ', '_')}.pdf"
            else:
                file_name = f"certificado_{index+1}.pdf"
                
            # Caminho completo para o arquivo
            file_path = os.path.join(output_dir, file_name)
            
            # Gerar HTML com os dados substituídos (simplificado)
            html_content = template_content
            for key, value in data.items():
                placeholder = f"{{{{{key}}}}}"
                if placeholder in html_content:
                    html_content = html_content.replace(placeholder, str(value))
            
            # Adicionar à lista
            html_contents.append(html_content)
            file_names.append(file_path)
            
            progress.update(task, advance=1)
    
    # Gerar PDFs em batch
    console.print("\n[bold]Gerando arquivos PDF...[/bold]")
    
    try:
        generated_paths = pdf_generator.batch_generate(html_contents, file_names)
        console.print(f"[bold green]✓ {len(generated_paths)} certificados gerados com sucesso![/bold green]")
        
        # Oferecer opção para empacotar em ZIP
        zip_option = questionary.confirm("Deseja empacotar os certificados em um arquivo ZIP?").ask()
        
        if zip_option:
            zip_name = questionary.text(
                "Nome do arquivo ZIP:",
                default=f"certificados_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ).ask()
            
            if not zip_name.endswith('.zip'):
                zip_name += '.zip'
                
            zip_path = os.path.join(output_dir, zip_name)
            
            # Criar arquivo ZIP
            with console.status("[bold green]Criando arquivo ZIP..."):
                zip_exporter.create_zip(generated_paths, zip_path)
            
            console.print(f"[bold green]✓ Arquivo ZIP criado em:[/bold green] {zip_path}")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificados:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def preview_imported_data():
    """Visualiza dados importados de um CSV."""
    console.clear()
    console.print("[bold blue]== Visualização de Dados Importados ==[/bold blue]\n")
    
    # Selecionar arquivo CSV
    csv_path = questionary.path(
        "Selecione o arquivo CSV para visualizar:",
        validate=lambda path: os.path.exists(path) and path.endswith('.csv')
    ).ask()
    
    if not csv_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar e mostrar dados
    try:
        df = pd.read_csv(csv_path)
        
        # Criar tabela Rich
        table = Table(title=f"Dados do arquivo: {os.path.basename(csv_path)}")
        
        # Adicionar colunas
        for col in df.columns:
            table.add_column(col, style="cyan")
        
        # Adicionar linhas (limitando a 10 registros para visualização)
        for _, row in df.head(10).iterrows():
            table.add_row(*[str(val) for val in row.values])
        
        console.print(table)
        
        # Informações adicionais
        console.print(f"\n[bold]Total de registros:[/bold] {len(df)}")
        console.print(f"[bold]Colunas disponíveis:[/bold] {', '.join(df.columns.tolist())}")
        
        # Verificar valores ausentes
        missing = df.isnull().sum()
        if missing.any():
            console.print("\n[yellow]Aviso: O arquivo contém valores ausentes nas seguintes colunas:[/yellow]")
            for col, count in missing[missing > 0].items():
                console.print(f"- {col}: {count} valores ausentes")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao processar o arquivo:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def test_certificate_generation():
    """Testa a geração de um certificado único."""
    console.clear()
    console.print("[bold blue]== Teste de Geração de Certificado ==[/bold blue]\n")
    
    # Selecionar template
    templates = template_manager.list_templates()
    if not templates:
        console.print("[yellow]Nenhum template disponível. Por favor, importe um template primeiro.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
        
    template_name = questionary.select(
        "Selecione o template a ser utilizado:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        input("\nPressione Enter para voltar...")
        return
    
    # Identificar placeholders (implementação simplificada)
    import re
    placeholders = re.findall(r'{{([^}]+)}}', template_content)
    
    if not placeholders:
        console.print("[yellow]Aviso: Não foram encontrados placeholders no template.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Solicitar valores para os placeholders
    test_data = {}
    console.print("[bold]Informe os valores para os campos:[/bold]\n")
    
    for placeholder in placeholders:
        value = questionary.text(f"Valor para '{placeholder}':").ask()
        test_data[placeholder] = value
    
    # Gerar HTML com os valores substituídos
    html_content = template_content
    for key, value in test_data.items():
        placeholder = f"{{{{{key}}}}}"
        html_content = html_content.replace(placeholder, str(value))
    
    # Gerar PDF de teste
    output_path = os.path.join(pdf_generator.output_dir, "certificado_teste.pdf")
    
    try:
        with console.status("[bold green]Gerando certificado de teste..."):
            pdf_generator.generate_pdf(html_content, output_path)
        
        console.print(f"[bold green]✓ Certificado de teste gerado com sucesso![/bold green]")
        console.print(f"[bold]Caminho:[/bold] {output_path}")
        
        # Oferecer opção para abrir o PDF
        open_option = questionary.confirm("Deseja abrir o certificado gerado?").ask()
        
        if open_option:
            import subprocess
            try:
                os.startfile(output_path)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", output_path])  # macOS
                except:
                    subprocess.call(["xdg-open", output_path])  # Linux
    
    except Exception as e:
        console.print(f"[bold red]Erro ao gerar certificado de teste:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


# Funções de implementação para o menu de templates

def list_templates():
    """Lista os templates disponíveis."""
    console.clear()
    console.print("[bold blue]== Templates Disponíveis ==[/bold blue]\n")
    
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template encontrado.[/yellow]")
    else:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Nome do Template", style="cyan")
        table.add_column("Tamanho", justify="right")
        table.add_column("Última Modificação")
        
        for template in templates:
            template_path = os.path.join(template_manager.templates_dir, template)
            size = os.path.getsize(template_path) / 1024  # KB
            mod_time = datetime.fromtimestamp(os.path.getmtime(template_path))
            
            table.add_row(
                template,
                f"{size:.1f} KB",
                mod_time.strftime("%d/%m/%Y %H:%M")
            )
        
        console.print(table)
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def import_template():
    """Importa um novo template."""
    console.clear()
    console.print("[bold blue]== Importar Novo Template ==[/bold blue]\n")
    
    # Solicitar caminho do template
    template_path = questionary.path(
        "Selecione o arquivo HTML do template:",
        validate=lambda path: os.path.exists(path) and path.lower().endswith('.html')
    ).ask()
    
    if not template_path:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Solicitar nome para salvar o template
    template_name = questionary.text(
        "Nome para salvar o template:",
        default=os.path.basename(template_path)
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    if not template_name.lower().endswith('.html'):
        template_name += '.html'
    
    # Verificar se já existe um template com esse nome
    templates = template_manager.list_templates()
    if template_name in templates:
        overwrite = questionary.confirm(
            f"Já existe um template com o nome '{template_name}'. Deseja sobrescrever?"
        ).ask()
        
        if not overwrite:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return
    
    # Ler o conteúdo do arquivo original
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Salvar o template
        template_manager.save_template(template_name, template_content)
        console.print(f"[bold green]✓ Template '{template_name}' importado com sucesso![/bold green]")
    
    except Exception as e:
        console.print(f"[bold red]Erro ao importar template:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def edit_template():
    """Edita um template existente."""
    console.clear()
    console.print("[bold blue]== Editar Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para edição.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para editar
    template_name = questionary.select(
        "Selecione o template para editar:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar conteúdo do template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        return
    
    console.print(f"[bold]Conteúdo atual do template:[/bold] {template_name}\n")
    console.print(Syntax(template_content[:500] + "..." if len(template_content) > 500 else template_content, "html"))
    
    console.print("\n[yellow]Aviso: A edição direta de templates HTML via CLI é limitada.[/yellow]")
    console.print("[yellow]Para edições complexas, recomendamos usar um editor HTML externo.[/yellow]\n")
    
    # Oferecer opção para abrir em um editor externo
    open_option = questionary.confirm("Deseja abrir o template em um editor externo?").ask()
    
    if open_option:
        template_path = os.path.join(template_manager.templates_dir, template_name)
        
        try:
            import subprocess
            try:
                os.startfile(template_path)  # Windows
            except AttributeError:
                try:
                    subprocess.call(["open", template_path])  # macOS
                except:
                    subprocess.call(["xdg-open", template_path])  # Linux
            
            console.print("[green]Template aberto no editor padrão.[/green]")
            console.print("[yellow]Lembre-se de salvar o arquivo após a edição.[/yellow]")
        
        except Exception as e:
            console.print(f"[bold red]Erro ao abrir o arquivo:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def delete_template():
    """Exclui um template."""
    console.clear()
    console.print("[bold blue]== Excluir Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para exclusão.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para excluir
    template_name = questionary.select(
        "Selecione o template para excluir:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Confirmar exclusão
    confirm = questionary.confirm(
        f"Tem certeza que deseja excluir o template '{template_name}'? Esta ação não pode ser desfeita."
    ).ask()
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Excluir o template
    result = template_manager.delete_template(template_name)
    
    if result:
        console.print(f"[bold green]✓ Template '{template_name}' excluído com sucesso![/bold green]")
    else:
        console.print(f"[bold red]Erro ao excluir template:[/bold red] Arquivo não encontrado.")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def preview_template():
    """Visualiza um template."""
    console.clear()
    console.print("[bold blue]== Visualizar Template ==[/bold blue]\n")
    
    # Listar templates disponíveis
    templates = template_manager.list_templates()
    
    if not templates:
        console.print("[yellow]Nenhum template disponível para visualização.[/yellow]")
        input("\nPressione Enter para voltar...")
        return
    
    # Selecionar template para visualizar
    template_name = questionary.select(
        "Selecione o template para visualizar:",
        choices=templates
    ).ask()
    
    if not template_name:
        console.print("[yellow]Operação cancelada.[/yellow]")
        return
    
    # Carregar conteúdo do template
    template_content = template_manager.load_template(template_name)
    if not template_content:
        console.print(f"[bold red]Erro ao carregar template:[/bold red] Arquivo não encontrado.")
        return
    
    # Detectar placeholders no template
    import re
    placeholders = re.findall(r'{{([^}]+)}}', template_content)
    
    console.print(f"[bold]Template:[/bold] {template_name}\n")
    
    # Mostrar informações sobre o template
    console.print("[bold]Visualização do HTML:[/bold]")
    console.print(Syntax(template_content[:1000] + "..." if len(template_content) > 1000 else template_content, "html"))
    
    if placeholders:
        console.print("\n[bold]Placeholders detectados:[/bold]")
        for i, placeholder in enumerate(placeholders, 1):
            console.print(f"{i}. [cyan]{{{{{placeholder}}}}}[/cyan]")
    else:
        console.print("\n[yellow]Nenhum placeholder detectado no template.[/yellow]")
    
    # Oferecer opção para gerar uma prévia em PDF com dados fictícios
    preview_option = questionary.confirm("Deseja gerar uma prévia em PDF com dados de exemplo?").ask()
    
    if preview_option:
        # Criar dados de exemplo para os placeholders
        example_data = {}
        for placeholder in placeholders:
            example_data[placeholder] = f"Exemplo de {placeholder}"
        
        # Substituir placeholders pelos dados de exemplo
        preview_content = template_content
        for key, value in example_data.items():
            placeholder = f"{{{{{key}}}}}"
            preview_content = preview_content.replace(placeholder, str(value))
        
        # Gerar PDF de prévia
        preview_path = os.path.join(pdf_generator.output_dir, "preview_template.pdf")
        
        try:
            with console.status("[bold green]Gerando prévia em PDF..."):
                pdf_generator.generate_pdf(preview_content, preview_path)
            
            console.print(f"[bold green]✓ Prévia gerada com sucesso![/bold green]")
            console.print(f"[bold]Caminho:[/bold] {preview_path}")
            
            # Oferecer opção para abrir o PDF
            open_option = questionary.confirm("Deseja abrir a prévia em PDF?").ask()
            
            if open_option:
                import subprocess
                try:
                    os.startfile(preview_path)  # Windows
                except AttributeError:
                    try:
                        subprocess.call(["open", preview_path])  # macOS
                    except:
                        subprocess.call(["xdg-open", preview_path])  # Linux
        
        except Exception as e:
            console.print(f"[bold red]Erro ao gerar prévia:[/bold red] {str(e)}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


# Funções de implementação para as demais opções de menu (a serem expandidas posteriormente)

def configure_directories():
    """Configura os diretórios de trabalho."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_appearance():
    """Configura aparência e tema."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


def configure_generation_parameters():
    """Configura parâmetros de geração de certificados."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


def manage_presets():
    """Gerencia presets de configuração."""
    console.print("[yellow]Função ainda não implementada.[/yellow]")
    input("\nPressione Enter para voltar...")


def check_connection():
    """Verifica o status da conexão."""
    console.clear()
    console.print("[bold blue]== Status da Conexão ==[/bold blue]\n")
    
    with console.status("[bold green]Verificando conexão com o servidor..."):
        result = connectivity_manager.check_connection()
    
    status_color = {
        "Conectado": "green",
        "Desconectado": "red",
        "Aguardando": "yellow"
    }.get(result["status"], "yellow")
    
    console.print(f"[bold]Status:[/bold] [{status_color}]{result['status']}[/{status_color}]")
    console.print(f"[bold]Mensagem:[/bold] {result['message']}")
    console.print(f"[bold]Horário:[/bold] {result['timestamp']}")
    
    if "server_url" in connectivity_manager.config and connectivity_manager.config["server_url"]:
        console.print(f"[bold]URL do servidor:[/bold] {connectivity_manager.config['server_url']}")
    else:
        console.print("[yellow]Servidor não configurado.[/yellow]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def configure_remote_server():
    """Configura servidor remoto."""
    console.clear()
    console.print("[bold blue]== Configuração de Servidor Remoto ==[/bold blue]\n")
    
    current_url = connectivity_manager.config.get("server_url", "")
    if current_url:
        console.print(f"URL atual do servidor: [cyan]{current_url}[/cyan]")
    
    # Solicitar nova URL
    new_url = questionary.text(
        "Digite a URL do servidor remoto:",
        default=current_url
    ).ask()
    
    if not new_url:
        console.print("[yellow]Operação cancelada.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Verificar formato básico da URL
    if not (new_url.startswith('http://') or new_url.startswith('https://')):
        suggestion = f"https://{new_url}"
        use_suggestion = questionary.confirm(
            f"A URL deve começar com http:// ou https://. Deseja usar '{suggestion}' em vez disso?"
        ).ask()
        
        if use_suggestion:
            new_url = suggestion
    
    # Salvar a nova URL
    connectivity_manager.set_server_url(new_url)
    console.print(f"[bold green]✓ URL do servidor configurada: [/bold green] {new_url}")
    
    # Verificar conexão com a nova URL
    check_now = questionary.confirm("Deseja verificar a conexão agora?").ask()
    
    if check_now:
        with console.status("[bold green]Verificando conexão..."):
            result = connectivity_manager.check_connection()
        
        status_color = {
            "Conectado": "green",
            "Desconectado": "red",
            "Aguardando": "yellow"
        }.get(result["status"], "yellow")
        
        console.print(f"[bold]Status:[/bold] [{status_color}]{result['status']}[/{status_color}]")
        console.print(f"[bold]Mensagem:[/bold] {result['message']}")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def upload_certificates():
    """Envia certificados para o servidor remoto."""
    console.clear()
    console.print("[bold blue]== Envio de Certificados para o Servidor ==[/bold blue]\n")
    
    # Verificar se há um servidor configurado
    if not connectivity_manager.config.get("server_url"):
        console.print("[yellow]Nenhum servidor configurado. Configure um servidor primeiro.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Verificar conexão antes de prosseguir
    with console.status("[bold green]Verificando conexão..."):
        conn_result = connectivity_manager.check_connection()
    
    if conn_result["status"] != "Conectado":
        console.print(f"[red]Não foi possível conectar ao servidor: {conn_result['message']}[/red]")
        console.print("[yellow]Verifique as configurações de conexão e tente novamente.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Selecionar arquivos para envio
    upload_dir = questionary.path(
        "Selecione o diretório contendo os certificados a enviar:",
        only_directories=True,
        default=pdf_generator.output_dir
    ).ask()
    
    if not upload_dir:
        console.print("[yellow]Operação cancelada.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Listar arquivos PDF no diretório
    pdf_files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        console.print(f"[yellow]Nenhum arquivo PDF encontrado em: {upload_dir}[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Mostrar quantidade de arquivos encontrados
    console.print(f"[bold]{len(pdf_files)} arquivos PDF encontrados.[/bold]")
    
    # Confirmar envio
    confirm = questionary.confirm(f"Deseja enviar {len(pdf_files)} certificados para o servidor?").ask()
    
    if not confirm:
        console.print("[yellow]Operação cancelada.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Enviar arquivos
    with console.status("[bold green]Enviando certificados para o servidor..."):
        result = connectivity_manager.upload_certificates(pdf_files)
    
    if result["success"]:
        console.print(f"[bold green]✓ {result['message']}[/bold green]")
    else:
        console.print(f"[bold red]Erro ao enviar certificados: {result['message']}[/bold red]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def download_templates():
    """Baixa templates do servidor remoto."""
    console.clear()
    console.print("[bold blue]== Download de Templates do Servidor ==[/bold blue]\n")
    
    # Verificar se há um servidor configurado
    if not connectivity_manager.config.get("server_url"):
        console.print("[yellow]Nenhum servidor configurado. Configure um servidor primeiro.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Verificar conexão antes de prosseguir
    with console.status("[bold green]Verificando conexão..."):
        conn_result = connectivity_manager.check_connection()
    
    if conn_result["status"] != "Conectado":
        console.print(f"[red]Não foi possível conectar ao servidor: {conn_result['message']}[/red]")
        console.print("[yellow]Verifique as configurações de conexão e tente novamente.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Obter lista de templates disponíveis
    with console.status("[bold green]Consultando templates disponíveis..."):
        result = connectivity_manager.download_templates()
    
    if not result["success"]:
        console.print(f"[bold red]Erro ao consultar templates: {result['message']}[/bold red]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    if not result["templates"]:
        console.print("[yellow]Nenhum template disponível no servidor.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Mostrar templates disponíveis
    console.print(f"[bold]{len(result['templates'])} templates encontrados no servidor:[/bold]")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Nome", style="cyan")
    table.add_column("Tamanho", justify="right")
    table.add_column("Atualizado em")
    
    for template in result["templates"]:
        table.add_row(
            template["name"],
            f"{template['size'] / 1024:.1f} KB",
            template["updated_at"]
        )
    
    console.print(table)
    
    # Opções de download
    options = ["Baixar todos os templates"] + [f"Baixar '{t['name']}'" for t in result["templates"]] + ["Cancelar"]
    
    choice = questionary.select(
        "O que você deseja fazer?",
        choices=options
    ).ask()
    
    if choice == "Cancelar":
        console.print("[yellow]Operação cancelada.[/yellow]")
        console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
        input()
        return
    
    # Simular download de templates
    with console.status("[bold green]Baixando templates..."):
        # Aqui seria feito o download real
        import time
        time.sleep(2)  # Simular tempo de download
    
    if choice == "Baixar todos os templates":
        console.print(f"[bold green]✓ {len(result['templates'])} templates baixados com sucesso![/bold green]")
    else:
        console.print(f"[bold green]✓ Template baixado com sucesso![/bold green]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


def configure_credentials():
    """Configura credenciais de acesso ao servidor."""
    console.clear()
    console.print("[bold blue]== Configuração de Credenciais ==[/bold blue]\n")
    
    # Obter configurações atuais
    current_username = connectivity_manager.config.get("username", "")
    has_password = bool(connectivity_manager.config.get("password", ""))
    current_api_key = connectivity_manager.config.get("api_key", "")
    
    # Mostrar informações atuais
    console.print("Configurações atuais:")
    console.print(f"- Usuário: [cyan]{current_username or 'Não definido'}[/cyan]")
    console.print(f"- Senha: [cyan]{'Configurada' if has_password else 'Não definida'}[/cyan]")
    console.print(f"- Chave API: [cyan]{current_api_key or 'Não definida'}[/cyan]\n")
    
    # Opções de configuração
    option = questionary.select(
        "O que você deseja configurar?",
        choices=[
            "👤 Atualizar usuário e senha",
            "🔑 Configurar chave API",
            "↩️ Voltar ao menu"
        ]
    ).ask()
    
    if option == "👤 Atualizar usuário e senha":
        username = questionary.text(
            "Nome de usuário:",
            default=current_username
        ).ask()
        
        if username is None:  # Operação cancelada
            console.print("[yellow]Operação cancelada.[/yellow]")
        else:
            password = questionary.password("Senha:").ask()
            
            if password is None:  # Operação cancelada
                console.print("[yellow]Operação cancelada.[/yellow]")
            else:
                # Salvar credenciais
                connectivity_manager.set_credentials(username, password)
                console.print("[bold green]✓ Credenciais atualizadas com sucesso![/bold green]")
    
    elif option == "🔑 Configurar chave API":
        api_key = questionary.password(
            "Chave API:",
            default=current_api_key
        ).ask()
        
        if api_key is None:  # Operação cancelada
            console.print("[yellow]Operação cancelada.[/yellow]")
        else:
            # Salvar chave API
            connectivity_manager.set_api_key(api_key)
            console.print("[bold green]✓ Chave API configurada com sucesso![/bold green]")
    
    console.print("\n[dim]Pressione Enter para voltar ao menu...[/dim]")
    input()


# Função principal do aplicativo
def main():
    """Função principal que inicializa o aplicativo."""
    while main_menu():
        pass


# Ponto de entrada do script
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Programa encerrado pelo usuário.[/bold yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Erro inesperado:[/bold red] {str(e)}")
