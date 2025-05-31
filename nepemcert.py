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
        
        with console.status("[bold green]Processando certificados...") as status:            # Inicializar o gerenciador de autenticação
            from app.authentication_manager import AuthenticationManager
            auth_manager = AuthenticationManager()
            
            for index, row in df.iterrows():
                # Obter dados do CSV
                csv_data = row.to_dict()
                
                # Mesclar com valores padrão (parâmetros.json)
                data = parameter_manager.merge_placeholders(csv_data, theme)
                
                # Gerar código de autenticação e QR code
                nome = data.get('nome', f"Participante {index+1}")
                evento = data.get('evento', "Evento")
                data_evento = data.get('data', "")
                
                codigo_autenticacao = auth_manager.gerar_codigo_autenticacao(
                    nome_participante=nome,
                    evento=evento,
                    data_evento=data_evento
                )
                  # Adicionar informações de autenticação aos dados
                data['codigo_autenticacao'] = codigo_autenticacao
                data['url_verificacao'] = "https://nepemcertificados.com/verificar-certificados/"
                data['qrcode_base64'] = auth_manager.gerar_qrcode_base64(codigo_autenticacao)

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
                    
                    # Salvar informações do certificado para verificação posterior
                    auth_manager.salvar_codigo(
                        data['codigo_autenticacao'],
                        data['nome'],
                        data.get('evento', 'Evento'),
                        data.get('data', ''),
                        data.get('local', 'Local não especificado'),
                        data.get('carga_horaria', '0')
                    )
                    
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
    from app.authentication_manager import AuthenticationManager
    
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
        data_exemplo = "22 a 24 de maio de 2025"        # Gerar código de autenticação único
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
            "data_emissao": "29 de maio de 2025",
            "codigo_autenticacao": codigo_autenticacao,
            "url_verificacao": "https://nepemufsc.com/verificar-certificados/",
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
        # Se não for solicitação de ajuda, executar normalmente
        cli()
