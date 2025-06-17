"""
Interface para gerenciamento de templates.
"""

import os
import random
from .ui_utils import console, UIUtils
from .ui_components import UIComponents

class TemplateInterface:
    """Interface para operações relacionadas a templates."""
    
    def __init__(self, app_services):
        self.app_services = app_services
        self.ui_utils = UIUtils()
        self.ui_components = UIComponents()
    
    def handle_action(self, action):
        """Processa ações relacionadas a templates."""
        action_map = {
            "📄 Listar templates": self.list_templates,
            "📥 Importar template": self.import_template,
            "✏️ Editar template": self.edit_template,
            "🗑️ Excluir template": self.delete_template,
            "👁️ Visualizar template": self.preview_template,
            "🧪 Testar geração de certificado": self.test_generation,
            "📊 Visualizar dados CSV": self.preview_csv_data
        }
        
        if action in action_map:
            action_map[action]()
    
    def list_templates(self):
        """Lista templates disponíveis."""
        console.clear()
        console.print("[bold blue]== Templates Disponíveis ==[/bold blue]\n")
        
        template_manager = self.app_services["template_manager"]
        templates = template_manager.list_templates()
        
        self.ui_components.show_template_list(templates)
        self.ui_utils.wait_for_enter()
    
    def import_template(self):
        """Interface para importar template."""
        console.clear()
        console.print("[bold blue]== Importar Novo Template ==[/bold blue]\n")
        
        # Solicitar dados
        template_data = self._collect_import_data()
        if not template_data:
            return
        
        # Executar importação
        template_manager = self.app_services["template_manager"]
        success = self._execute_template_import(template_manager, template_data)
        
        if success:
            console.print(f"[bold green]✓ Template '{template_data['name']}' importado com sucesso![/bold green]")
        
        self.ui_utils.wait_for_enter()
    
    def edit_template(self):
        """Interface para editar template."""
        console.clear()
        console.print("[bold blue]== Editar Template ==[/bold blue]\n")
        
        template_manager = self.app_services["template_manager"]
        
        # Selecionar template
        template_name = self._select_template(template_manager)
        if not template_name:
            return
        
        # Abrir para edição
        self._open_template_for_editing(template_manager, template_name)
        self.ui_utils.wait_for_enter()
    
    def delete_template(self):
        """Interface para excluir template."""
        console.clear()
        console.print("[bold blue]== Excluir Template ==[/bold blue]\n")
        
        template_manager = self.app_services["template_manager"]
        
        # Selecionar e confirmar exclusão
        template_name = self._select_template(template_manager)
        if not template_name:
            return
        
        if self._confirm_deletion(template_name):
            success = template_manager.delete_template(template_name)
            if success:
                console.print(f"[bold green]✓ Template '{template_name}' excluído com sucesso![/bold green]")
            else:
                console.print(f"[bold red]Erro ao excluir template.[/bold red]")
        
        self.ui_utils.wait_for_enter()
    
    def preview_template(self):
        """Interface para visualizar template."""
        console.clear()
        console.print("[bold blue]== Visualizar Template ==[/bold blue]\n")
        
        template_manager = self.app_services["template_manager"]
        
        # Selecionar template
        template_name = self._select_template(template_manager)
        if not template_name:
            return
        
        # Carregar e exibir
        template_content = template_manager.load_template(template_name)
        if template_content:
            placeholders = template_manager.extract_placeholders(template_content)
            self.ui_components.show_template_preview(template_name, template_content, placeholders)
            
            # Oferecer prévia em PDF
            if self.ui_utils.quiet_confirm("Deseja gerar uma prévia em PDF com dados de exemplo?"):
                self._generate_template_preview(template_manager, template_name, template_content, placeholders)
        
        self.ui_utils.wait_for_enter()
    
    def test_generation(self):
        """Interface para teste de geração."""
        console.clear()
        console.print("[bold blue]== Teste de Geração de Certificado ==[/bold blue]\n")
        
        # Delegar para interface de geração
        generator_interface = self.app_services.get("generator_interface")
        if generator_interface:
            generator_interface.test_certificate_generation()
        else:
            console.print("[yellow]Funcionalidade de teste não disponível.[/yellow]")
        
        self.ui_utils.wait_for_enter()
    
    def preview_csv_data(self):
        """Interface para visualizar dados CSV."""
        console.clear()
        console.print("[bold blue]== Visualização de Dados CSV ==[/bold blue]\n")
        
        # Solicitar arquivo CSV
        csv_path = self.ui_utils.quiet_path(
            "Selecione o arquivo CSV para visualizar:",
            validate=lambda path: os.path.exists(path) and path.endswith('.csv')
        )
        
        if not csv_path:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return
        
        # Processar e exibir
        self._process_and_show_csv(csv_path)
        self.ui_utils.wait_for_enter()
    
    def _collect_import_data(self):
        """Coleta dados para importação de template."""
        template_path = self.ui_utils.quiet_path(
            "Selecione o arquivo HTML do template:",
            validate=lambda path: os.path.exists(path) and path.lower().endswith('.html')
        )
        
        if not template_path:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return None
        
        template_name = self.ui_utils.quiet_text(
            "Nome para salvar o template:",
            default=os.path.basename(template_path)
        )
        
        if not template_name:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return None
        
        if not template_name.lower().endswith('.html'):
            template_name += '.html'
        
        return {
            "path": template_path,
            "name": template_name
        }
    
    def _execute_template_import(self, template_manager, template_data):
        """Executa a importação do template."""
        try:
            # Verificar se já existe
            if template_data["name"] in template_manager.list_templates():
                if not self.ui_utils.quiet_confirm(f"Template '{template_data['name']}' já existe. Sobrescrever?"):
                    console.print("[yellow]Operação cancelada.[/yellow]")
                    return False
            
            # Ler e salvar
            with open(template_data["path"], 'r', encoding='utf-8') as f:
                content = f.read()
            
            template_manager.save_template(template_data["name"], content)
            return True
            
        except Exception as e:
            console.print(f"[bold red]Erro ao importar template:[/bold red] {str(e)}")
            return False
    
    def _select_template(self, template_manager):
        """Permite seleção de template."""
        templates = template_manager.list_templates()
        
        if not templates:
            console.print("[yellow]Nenhum template disponível.[/yellow]")
            return None
        
        return self.ui_utils.quiet_select(
            "Selecione o template:",
            choices=templates,
            style=self.ui_utils.get_menu_style()
        )
    
    def _confirm_deletion(self, template_name):
        """Confirma exclusão de template."""
        return self.ui_utils.quiet_confirm(
            f"Tem certeza que deseja excluir o template '{template_name}'? Esta ação não pode ser desfeita."
        )
    
    def _open_template_for_editing(self, template_manager, template_name):
        """Abre template para edição."""
        template_content = template_manager.load_template(template_name)
        if not template_content:
            console.print(f"[bold red]Erro ao carregar template.[/bold red]")
            return
        
        console.print(f"[bold]Template:[/bold] {template_name}")
        console.print("[yellow]A edição via CLI é limitada. Recomendamos usar um editor externo.[/yellow]\n")
        
        if self.ui_utils.quiet_confirm("Deseja abrir o template em um editor externo?"):
            template_path = os.path.join(template_manager.templates_dir, template_name)
            try:
                self.ui_utils.open_file_cross_platform(template_path)
                console.print("[green]Template aberto no editor padrão.[/green]")
            except Exception as e:
                console.print(f"[bold red]Erro ao abrir arquivo:[/bold red] {str(e)}")
    
    def _generate_template_preview(self, template_manager, template_name, template_content, placeholders):
        """Gera prévia do template em PDF."""
        try:
            # Criar dados de exemplo
            example_data = {placeholder: f"Exemplo de {placeholder}" for placeholder in placeholders}
            
            # Gerar PDF
            certificate_service = self.app_services["certificate_service"]
            preview_path = os.path.join(certificate_service.output_dir, "preview_template.pdf")
            
            with console.status("[bold green]Gerando prévia em PDF..."):
                # Template temporário
                temp_name = f"temp_preview_{random.randint(1000, 9999)}.html"
                temp_path = os.path.join("templates", temp_name)
                
                try:
                    with open(temp_path, "w", encoding="utf-8") as f:
                        f.write(template_content)
                    
                    html_content = template_manager.render_template(temp_name, example_data)
                    
                    from app.pdf_generator import PDFGenerator
                    pdf_generator = PDFGenerator()
                    pdf_generator.generate_pdf(html_content, preview_path, orientation='landscape')
                    
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            console.print(f"[bold green]✓ Prévia gerada:[/bold green] {preview_path}")
            
            if self.ui_utils.quiet_confirm("Deseja abrir a prévia?"):
                self.ui_utils.open_file_cross_platform(preview_path)
                
        except Exception as e:
            console.print(f"[bold red]Erro ao gerar prévia:[/bold red] {str(e)}")
    
    def _process_and_show_csv(self, csv_path):
        """Processa e exibe dados do CSV."""
        try:
            import pandas as pd
            
            has_header = self.ui_utils.quiet_confirm("O arquivo CSV possui linha de cabeçalho?")
            df = pd.read_csv(csv_path, header=0 if has_header else None)
            
            if not has_header:
                df.columns = ["nome"]
            
            self.ui_components.show_csv_preview(csv_path, df, has_header)
            
        except Exception as e:
            console.print(f"[bold red]Erro ao processar arquivo:[/bold red] {str(e)}")
