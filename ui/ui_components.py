"""
Componentes reutilizáveis de interface do usuário.
"""

from rich.table import Table
from rich import box
from rich.syntax import Syntax
from datetime import datetime
import os
from .ui_utils import console, UIUtils

class UIComponents:
    """Componentes reutilizáveis para interfaces."""
    
    @staticmethod
    def show_template_list(templates):
        """Exibe lista de templates em formato de tabela."""
        if not templates:
            console.print("[yellow]Nenhum template encontrado.[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold")
        table.add_column("Nome do Template", style="cyan")
        table.add_column("Tamanho", justify="right")
        table.add_column("Última Modificação")
        
        for template in templates:
            template_path = os.path.join("templates", template)
            if os.path.exists(template_path):
                size = os.path.getsize(template_path) / 1024  # KB
                mod_time = datetime.fromtimestamp(os.path.getmtime(template_path))
                
                table.add_row(
                    template,
                    f"{size:.1f} KB",
                    mod_time.strftime("%d/%m/%Y %H:%M")
                )
        
        console.print(table)
    
    @staticmethod
    def show_template_preview(template_name, template_content, placeholders):
        """Exibe prévia de um template."""
        console.print(f"[bold]Template:[/bold] {template_name}\n")
        
        # Mostrar visualização do HTML
        console.print("[bold]Visualização do HTML:[/bold]")
        display_content = template_content[:1000] + "..." if len(template_content) > 1000 else template_content
        console.print(Syntax(display_content, "html"))
        
        if placeholders:
            console.print("\n[bold]Placeholders detectados:[/bold]")
            for i, placeholder in enumerate(placeholders, 1):
                console.print(f"{i}. [cyan]{{{{{placeholder}}}}}[/cyan]")
        else:
            console.print("\n[yellow]Nenhum placeholder detectado no template.[/yellow]")
    
    @staticmethod
    def show_csv_preview(csv_path, dataframe, has_header):
        """Exibe prévia dos dados do CSV."""
        table = Table(title=f"Dados do arquivo: {os.path.basename(csv_path)}", box=box.ROUNDED)
        
        # Adicionar colunas
        for col in dataframe.columns:
            table.add_column(col, style="cyan")
        
        # Adicionar linhas (limitando a 10 registros para visualização)
        for _, row in dataframe.head(10).iterrows():
            table.add_row(*[str(val) for val in row.values])
        
        console.print(table)
        
        # Informações adicionais
        console.print(f"\n[bold]Total de registros:[/bold] {len(dataframe)}")
        console.print(f"[bold]Colunas disponíveis:[/bold] {', '.join(dataframe.columns.tolist())}")
        
        # Verificar valores ausentes
        missing = dataframe.isnull().sum()
        if missing.any():
            console.print("\n[yellow]Aviso: O arquivo contém valores ausentes nas seguintes colunas:[/yellow]")
            for col, count in missing[missing > 0].items():
                console.print(f"- {col}: {count} valores ausentes")
    
    @staticmethod
    def show_generation_results(generation_result):
        """Exibe resultados da geração de certificados."""
        console.print("\n[bold blue]== Resultados da Geração ==[/bold blue]")
        
        if generation_result["success_count"] > 0:
            console.print(f"[bold green]✓ {generation_result['success_count']} certificados gerados com sucesso![/bold green]")
        
        if generation_result["failed_count"] > 0:
            console.print(f"[bold red]✗ {generation_result['failed_count']} certificados falharam ao gerar.[/bold red]")
        
        if generation_result.get("errors"):
            console.print("\n[bold yellow]Erros e Avisos:[/bold yellow]")
            for error_msg in generation_result["errors"]:
                console.print(f"  [yellow]•[/yellow] {error_msg}")
    
    @staticmethod
    def show_menu_options():
        """Retorna as opções dos menus da aplicação."""
        return {
            "main": [
                "🔖 Gerar Certificados",
                "🎨 Gerenciar Templates", 
                "⚙️ Configurações",
                "🔄 Sincronização e Conectividade",
                "❓ Ajuda",
                "🚪 Sair"
            ],
            "templates": [
                "📄 Listar templates",
                "📥 Importar template",
                "✏️ Editar template",
                "🗑️ Excluir template",
                "👁️ Visualizar template",
                "🧪 Testar geração de certificado",
                "📊 Visualizar dados CSV",
                "↩️ Voltar ao menu principal"
            ],
            "settings": [
                "📁 Diretórios de trabalho",
                "🎨 Aparência e tema",
                "📊 Parâmetros de geração",
                "🔧 Configurações do sistema",
                "💾 Salvar/carregar presets",
                "↩️ Voltar ao menu principal"
            ],
            "connectivity": [
                "🔄 Verificar conexão",
                "📊 Status detalhado de sincronização",
                "🔄 Sincronizar certificados pendentes",
                "⚙️ Configurar servidor",
                "📤 Enviar Certificados Gerados",
                "📥 Baixar Templates do Servidor",
                "📋 Histórico de sincronização",
                "↩️ Voltar ao menu principal"
            ],
            "generation_parameters": [
                "📝 Valores para campos institucionais",
                "🔤 Valores padrão para campos",
                "🖼️ Valores específicos para temas",
                "↩️ Voltar"
            ],
            "institutional_placeholders": [
                "➕ Adicionar/editar campo",
                "🗑️ Remover campo",
                "↩️ Voltar"
            ]
        }
