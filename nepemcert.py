#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEPEM Certificados - Programa principal
Aplicativo para geração de certificados em lote via CLI.
"""

import os
import sys
import click
from rich.console import Console

# Importar o módulo CLI melhorado
from cli import main as cli_main

# Console Rich para saída formatada
console = Console()


@click.group()
@click.version_option(version="1.1.0", prog_name="NEPEM Certificados")
def cli():
    """NEPEM Certificados - Gerador de certificados em lote via linha de comando."""
    pass


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
    """    # Importações necessárias
    import pandas as pd
    from app.pdf_generator import PDFGenerator
    from app.zip_exporter import ZipExporter
    from app.parameter_manager import ParameterManager
    from app.template_manager import TemplateManager
    from app.theme_manager import ThemeManager
    
    console.print(f"[bold blue]Gerando certificados...[/bold blue]")
    console.print(f"- Arquivo CSV: [cyan]{csv_file}[/cyan]")
    console.print(f"- Template: [cyan]{template}[/cyan]")
    console.print(f"- Diretório de saída: [cyan]{output}[/cyan]")
    
    try:
        # Criar diretório de saída se não existir
        os.makedirs(output, exist_ok=True)
        
        # Carregar dados do CSV
        df = pd.read_csv(csv_file)
        console.print(f"[green]✓[/green] Dados carregados: {len(df)} registros")
        
        # Carregar template
        with open(template, 'r', encoding='utf-8') as f:
            template_content = f.read()
        console.print(f"[green]✓[/green] Template carregado")
        
        # Inicializar geradores
        pdf_generator = PDFGenerator(output_dir=output)
        zip_exporter = ZipExporter()
          # Inicializar gerenciadores adicionais
        parameter_manager = ParameterManager()
        template_manager_obj = TemplateManager()
        theme_manager = ThemeManager()
        
        # Extrair nome do tema se fornecido (implementação futura)
        theme = None
        
        # Gerar certificados
        html_contents = []
        file_names = []
        
        # Extrair placeholders do template para informação
        placeholders = template_manager_obj.extract_placeholders(template_content)
        console.print(f"Placeholders encontrados no template: {len(placeholders)}")
        
        with console.status("[bold green]Processando certificados...") as status:
            for index, row in df.iterrows():
                # Obter dados do CSV
                csv_data = row.to_dict()
                
                # Mesclar com valores padrão (parâmetros.json)
                data = parameter_manager.merge_placeholders(csv_data, theme)
                
                # Informar sobre placeholders ainda não preenchidos
                missing_placeholders = [p for p in placeholders if p not in data]
                if missing_placeholders and index == 0:  # Mostrar apenas para o primeiro certificado
                    console.print(f"[yellow]Aviso: Os seguintes placeholders não têm valores definidos e aparecerão vazios:[/yellow]")
                    console.print(f"[yellow]{', '.join(missing_placeholders)}[/yellow]")
                
                # Gerar nome do arquivo
                if "nome" in data:
                    file_name = f"certificado_{data['nome'].strip().replace(' ', '_')}.pdf"
                else:
                    file_name = f"certificado_{index+1}.pdf"
                
                # Caminho completo para o arquivo
                file_path = os.path.join(output, file_name)
                
                # Usar o template_manager para renderizar o template com Jinja2
                base_name = os.path.basename(template)
                temp_path = os.path.join("templates", f"temp_{base_name}")
                
                # Salvar temporariamente o template para usar o renderizador
                with open(temp_path, "w", encoding="utf-8") as f:
                    f.write(template_content)
                
                try:
                    html_content = template_manager_obj.render_template(os.path.basename(temp_path), data)
                    
                    # Adicionar à lista
                    html_contents.append(html_content)
                    file_names.append(file_path)
                    
                    # Atualizar status
                    console.print(f"Processando certificado {index+1}/{len(df)}: {data.get('nome', f'Registro {index+1}')}", end="\r")
                    
                finally:
                    # Limpar arquivo temporário
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
        
        # Gerar PDFs em batch
        generated_paths = pdf_generator.batch_generate(html_contents, file_names)
        console.print(f"[bold green]✓ {len(generated_paths)} certificados gerados com sucesso![/bold green]")
        
        # Criar arquivo ZIP se solicitado
        if zip:
            if not zip_name:
                from datetime import datetime
                zip_name = f"certificados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            elif not zip_name.endswith('.zip'):
                zip_name += '.zip'
                
            zip_path = os.path.join(output, zip_name)
            
            # Criar arquivo ZIP
            with console.status("[bold green]Criando arquivo ZIP..."):
                zip_exporter.create_zip(generated_paths, zip_path)
            
            console.print(f"[bold green]✓ Arquivo ZIP criado: [/bold green]{zip_path}")
    
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


if __name__ == "__main__":
    cli()
