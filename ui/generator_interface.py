"""
Interface para geração de certificados.
"""

import os
import pandas as pd
from datetime import datetime
from .ui_utils import console, UIUtils
from .ui_components import UIComponents

class GeneratorInterface:
    """Interface para operações de geração de certificados."""
    
    def __init__(self, app_services):
        self.app_services = app_services
        self.ui_utils = UIUtils()
        self.ui_components = UIComponents()
    
    def handle_action(self, action):
        """Processa ações de geração."""
        if action == "🔖 Gerar Certificados":
            self.show_generation_menu()
    
    def show_generation_menu(self):
        """Exibe menu de opções de geração."""
        console.clear()
        console.print("[bold blue]== Geração de Certificados ==[/bold blue]\n")
        
        options = [
            "📄 Gerar certificado único",
            "📦 Gerar certificados em lote",
            "🧪 Teste de geração",
            "↩️ Voltar ao menu principal"
        ]
        
        choice = self.ui_utils.quiet_select(
            "Selecione o tipo de geração:",
            choices=options,
            style=self.ui_utils.get_menu_style()
        )
        
        if choice == "📄 Gerar certificado único":
            self.generate_single_certificate()
        elif choice == "📦 Gerar certificados em lote":
            self.generate_certificates_batch()
        elif choice == "🧪 Teste de geração":
            self.test_certificate_generation()
    
    def generate_single_certificate(self):
        """Interface para gerar certificado único."""
        console.clear()
        console.print("[bold blue]== Gerar Certificado Único ==[/bold blue]\n")
        
        # Coletar dados do certificado
        certificate_data = self._collect_single_certificate_data()
        if not certificate_data:
            return
        
        # Executar geração
        self._execute_single_generation(certificate_data)
        self.ui_utils.wait_for_enter()
    
    def generate_certificates_batch(self):
        """Interface para geração em lote."""
        console.clear()
        console.print("[bold blue]== Geração de Certificados em Lote ==[/bold blue]\n")
        
        # Coletar dados para geração em lote
        batch_data = self._collect_batch_data()
        if not batch_data:
            return
        
        # Executar geração em lote
        result = self._execute_batch_generation(batch_data)
        
        # Exibir resultados
        self.ui_components.show_generation_results(result)
        
        # Oferecer criação de ZIP
        if result["success_count"] > 0:
            self._offer_zip_creation(result, batch_data)
        
        self.ui_utils.wait_for_enter()
    
    def test_certificate_generation(self):
        """Interface para teste de geração."""
        console.clear()
        console.print("[bold blue]== Teste de Geração de Certificado ==[/bold blue]\n")
        
        # Selecionar template
        template_manager = self.app_services["template_manager"]
        template_name = self._select_template(template_manager)
        if not template_name:
            return
        
        # Coletar dados de teste
        test_data = self._collect_test_data(template_manager, template_name)
        if not test_data:
            return
        
        # Executar teste
        self._execute_test_generation(template_name, test_data)
        self.ui_utils.wait_for_enter()
    
    def _collect_single_certificate_data(self):
        """Coleta dados para certificado único."""
        # Selecionar template
        template_manager = self.app_services["template_manager"]
        template_name = self._select_template(template_manager)
        if not template_name:
            return None
        
        # Coletar dados básicos
        participant_data = self._collect_participant_data()
        if not participant_data:
            return None
        
        # Selecionar tema
        theme = self._select_theme()
        
        return {
            "template_name": template_name,
            "participant_data": participant_data,
            "theme": theme
        }
    
    def _collect_batch_data(self):
        """Coleta dados para geração em lote."""
        # Selecionar arquivo CSV
        csv_path = self.ui_utils.quiet_path(
            "Selecione o arquivo CSV com nomes dos participantes:",
            validate=lambda path: os.path.exists(path) and path.endswith('.csv')
        )
        
        if not csv_path:
            console.print("[yellow]Operação cancelada.[/yellow]")
            return None
        
        # Processar CSV
        csv_info = self._process_csv_file(csv_path)
        if not csv_info:
            return None
        
        # Coletar informações do evento
        event_data = self._collect_event_information()
        if not event_data:
            return None
        
        # Selecionar template e tema
        template_name = self._select_template(self.app_services["template_manager"])
        if not template_name:
            return None
        
        theme = self._select_theme()
        
        # Configurar saída
        output_dir = self._configure_output_directory()
        
        return {
            "csv_path": csv_path,
            "csv_info": csv_info,
            "event_data": event_data,
            "template_name": template_name,
            "theme": theme,
            "output_dir": output_dir
        }
    
    def _collect_participant_data(self):
        """Coleta dados do participante."""
        nome = self.ui_utils.quiet_text("Nome do participante:")
        if not nome:
            return None
        
        evento = self.ui_utils.quiet_text("Nome do evento:")
        data = self.ui_utils.quiet_text("Data do evento:", default=datetime.now().strftime("%d/%m/%Y"))
        local = self.ui_utils.quiet_text("Local do evento:")
        carga_horaria = self.ui_utils.quiet_text("Carga horária (horas):")
        
        return {
            "nome": nome,
            "evento": evento,
            "data": data,
            "local": local,
            "carga_horaria": carga_horaria
        }
    
    def _collect_event_information(self):
        """Coleta informações do evento."""
        console.print("\n[bold]Informações do Evento[/bold]")
        
        evento = self.ui_utils.quiet_text("Nome do evento:")
        if not evento:
            return None
        
        data = self.ui_utils.quiet_text("Data do evento:", default=datetime.now().strftime("%d/%m/%Y"))
        local = self.ui_utils.quiet_text("Local do evento:")
        carga_horaria = self.ui_utils.quiet_text("Carga horária (horas):")
        
        event_data = {
            "evento": evento,
            "data": data,
            "local": local,
            "carga_horaria": carga_horaria
        }
        
        # Permitir revisão das informações
        return self._review_event_data(event_data)
    
    def _select_template(self, template_manager):
        """Seleciona template disponível."""
        templates = template_manager.list_templates()
        if not templates:
            console.print("[yellow]Nenhum template disponível.[/yellow]")
            return None
        
        return self.ui_utils.quiet_select(
            "Selecione o template:",
            choices=templates,
            style=self.ui_utils.get_menu_style()
        )
    
    def _select_theme(self):
        """Seleciona tema disponível."""
        theme_manager = self.app_services["theme_manager"]
        themes = ["Nenhum"] + theme_manager.list_themes()
        
        selected = self.ui_utils.quiet_select(
            "Selecione um tema:",
            choices=themes,
            style=self.ui_utils.get_menu_style()
        )
        
        return None if selected == "Nenhum" else selected
    
    def _process_csv_file(self, csv_path):
        """Processa arquivo CSV."""
        import pandas as pd
        
        has_header = self.ui_utils.quiet_confirm("O arquivo CSV possui linha de cabeçalho?")
        
        try:
            # Carregar dados
            if has_header:
                df = pd.read_csv(csv_path)
                if "nome" not in df.columns and len(df.columns) == 1:
                    df.columns = ["nome"]
            else:
                df = pd.read_csv(csv_path, header=None, names=["nome"])
            
            df = df.dropna(subset=["nome"])
            num_records = len(df)
            
            console.print(f"[green]✓[/green] {num_records} participantes encontrados.")
            
            return {
                "dataframe": df,
                "num_records": num_records,
                "has_header": has_header
            }
            
        except Exception as e:
            console.print(f"[bold red]Erro ao processar CSV:[/bold red] {str(e)}")
            return None
    
    def _configure_output_directory(self):
        """Configura diretório de saída."""
        certificate_service = self.app_services["certificate_service"]
        
        output_dir = self.ui_utils.quiet_path(
            "Pasta de destino para os certificados:",
            default=certificate_service.output_dir,
            only_directories=True
        )
        
        return output_dir if output_dir else certificate_service.output_dir
    
    def _review_event_data(self, event_data):
        """Permite revisar dados do evento."""
        while True:
            console.clear()
            console.print("[bold blue]== Revisão das Informações do Evento ==[/bold blue]\n")
            
            table = self.ui_utils.create_summary_table(event_data)
            console.print(table)
            
            choice = self.ui_utils.quiet_select(
                "Deseja modificar alguma informação?",
                choices=[
                    "Não, continuar",
                    "Modificar nome do evento",
                    "Modificar data",
                    "Modificar local",
                    "Modificar carga horária",
                    "Cancelar operação"
                ],
                style=self.ui_utils.get_menu_style()
            )
            
            if choice == "Não, continuar":
                break
            elif choice == "Cancelar operação":
                return None
            else:
                # Modificar campo específico
                self._modify_event_field(event_data, choice)
        
        return event_data
    
    def _modify_event_field(self, event_data, choice):
        """Modifica campo específico do evento."""
        field_map = {
            "Modificar nome do evento": ("evento", "Nome do evento:"),
            "Modificar data": ("data", "Data do evento:"),
            "Modificar local": ("local", "Local do evento:"),
            "Modificar carga horária": ("carga_horaria", "Carga horária (horas):")
        }
        
        if choice in field_map:
            field, prompt = field_map[choice]
            event_data[field] = self.ui_utils.quiet_text(prompt, default=event_data[field])
    
    def _collect_test_data(self, template_manager, template_name):
        """Coleta dados para teste."""
        # Carregar template e identificar placeholders
        template_content = template_manager.load_template(template_name)
        if not template_content:
            console.print("[bold red]Erro ao carregar template.[/bold red]")
            return None
        
        placeholders = template_manager.extract_placeholders(template_content)
        
        # Coletar dados básicos
        test_data = self._collect_participant_data()
        if not test_data:
            return None
        
        # Gerar código de autenticação
        auth_manager = self.app_services["auth_manager"]
        codigo = auth_manager.gerar_codigo_autenticacao(
            test_data["nome"], test_data["evento"], test_data["data"]
        )
        
        test_data.update({
            "codigo_autenticacao": codigo,
            "codigo_verificacao": codigo,
            "url_verificacao": "https://nepemufsc.com/verificar-certificados",
            "data_emissao": datetime.now().strftime("%d/%m/%Y")
        })
        
        # Solicitar outros placeholders
        outros_placeholders = [p for p in placeholders if p not in test_data]
        for placeholder in outros_placeholders:
            value = self.ui_utils.quiet_text(f"Valor para '{placeholder}':")
            test_data[placeholder] = value
        
        return test_data
    
    def _execute_single_generation(self, certificate_data):
        """Executa geração de certificado único."""
        try:
            certificate_service = self.app_services["certificate_service"]
            
            with console.status("[bold green]Gerando certificado..."):
                result = certificate_service.generate_single_certificate(
                    participant_data=certificate_data["participant_data"],
                    template_name=certificate_data["template_name"],
                    theme_name=certificate_data["theme"]
                )
            
            if result["success"]:
                console.print(f"[bold green]✓ Certificado gerado:[/bold green] {result['file_path']}")
                
                if self.ui_utils.quiet_confirm("Deseja abrir o certificado?"):
                    self.ui_utils.open_file_cross_platform(result["file_path"])
            else:
                console.print(f"[bold red]Erro na geração:[/bold red] {result.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            console.print(f"[bold red]Erro na geração:[/bold red] {str(e)}")
    
    def _execute_batch_generation(self, batch_data):
        """Executa geração em lote."""
        try:
            certificate_service = self.app_services["certificate_service"]
            
            with console.status("[bold green]Gerando certificados em lote..."):
                result = certificate_service.generate_certificates_batch(
                    csv_file_path=batch_data["csv_path"],
                    event_details=batch_data["event_data"],
                    template_name=batch_data["template_name"],
                    theme_name=batch_data["theme"],
                    has_header=batch_data["csv_info"]["has_header"]
                )
            
            return result
            
        except Exception as e:
            console.print(f"[bold red]Erro na geração em lote:[/bold red] {str(e)}")
            return {"success_count": 0, "failed_count": 0, "errors": [str(e)]}
    
    def _execute_test_generation(self, template_name, test_data):
        """Executa geração de teste."""
        try:
            certificate_service = self.app_services["certificate_service"]
            
            with console.status("[bold green]Gerando certificado de teste..."):
                result = certificate_service.generate_single_certificate(
                    participant_data=test_data,
                    template_name=template_name,
                    theme_name=None,
                    filename="certificado_teste.pdf"
                )
            
            if result["success"]:
                console.print(f"[bold green]✓ Certificado de teste gerado:[/bold green] {result['file_path']}")
                
                if self.ui_utils.quiet_confirm("Deseja abrir o certificado?"):
                    self.ui_utils.open_file_cross_platform(result["file_path"])
            else:
                console.print(f"[bold red]Erro na geração:[/bold red] {result.get('error', 'Erro desconhecido')}")
                
        except Exception as e:
            console.print(f"[bold red]Erro na geração de teste:[/bold red] {str(e)}")
    
    def _offer_zip_creation(self, generation_result, batch_data):
        """Oferece criação de arquivo ZIP."""
        if not generation_result.get("generated_files"):
            return
        
        if self.ui_utils.quiet_confirm("Deseja empacotar os certificados em um arquivo ZIP?"):
            zip_name = f"{batch_data['event_data']['evento'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.zip"
            zip_name = self.ui_utils.quiet_text("Nome do arquivo ZIP:", default=zip_name)
            
            if not zip_name.endswith('.zip'):
                zip_name += '.zip'
            
            try:
                zip_exporter = self.app_services["zip_exporter"]
                zip_path = os.path.join(batch_data["output_dir"], zip_name)
                
                with console.status("[bold green]Criando arquivo ZIP..."):
                    zip_exporter.create_zip(generation_result["generated_files"], zip_path)
                
                console.print(f"[bold green]✓ Arquivo ZIP criado:[/bold green] {zip_path}")
                
            except Exception as e:
                console.print(f"[bold red]Erro ao criar ZIP:[/bold red] {str(e)}")

class CertificateGenerator:
    """Classe para geração de certificados - interface para testes."""
    
    def __init__(self, services):
        self.services = services
        self.ui_utils = UIUtils()
        self.ui_components = UIComponents()
    
    def start_generation_flow(self):
        """Inicia fluxo de geração."""
        import questionary
        
        choice = questionary.select(
            "Selecione o tipo de geração:",
            choices=[
                "📄 Gerar em lote (CSV)",
                "📃 Gerar individual",
                "❌ Cancelar"
            ]
        ).ask()
        
        if choice == "📄 Gerar em lote (CSV)":
            self.handle_batch_generation()
        elif choice == "📃 Gerar individual":
            self.handle_single_generation()
    
    def handle_batch_generation(self):
        """Processa geração em lote."""
        # Obter arquivo CSV
        csv_file, df = self.get_csv_file()
        if not csv_file or df is None:
            return
        
        # Validar dados CSV
        if not self.validate_csv_data(df):
            return
        
        # Processar cabeçalho
        has_header = self.handle_csv_header_question()
        
        # Selecionar template e tema
        template = self.select_template()
        if not template:
            return
        
        theme = self.select_theme()
        
        # Coletar detalhes do evento
        event_details = self.collect_event_details()
        if not event_details:
            return
        
        # Confirmar detalhes
        details = {
            "csv_file": csv_file,
            "template": template,
            "theme": theme,
            "event_details": event_details,
            "participants_count": len(df)
        }
        
        if not self.confirm_generation_details(details):
            return
        
        # Executar geração
        result = self.execute_generation(details)
        
        # Oferecer criação de ZIP
        if result.get("generated_files"):
            if self.ask_create_zip(result["generated_files"]):
                zip_filename = self.get_zip_filename()
                self.create_zip_file(result["generated_files"], zip_filename)
    
    def handle_single_generation(self):
        """Processa geração individual."""
        # Selecionar template
        template = self.select_template()
        if not template:
            return
        
        # Selecionar tema
        theme = self.select_theme()
        
        # Coletar dados do participante
        participant_data = self.collect_event_details()
        if not participant_data:
            return
        
        # Executar geração individual
        result = self.services["certificate_service"].generate_single_certificate(
            participant_data=participant_data,
            template_name=template,
            theme_name=theme
        )
        
        return result
    
    def get_csv_file(self):
        """Obtém arquivo CSV."""
        import questionary
        
        try:
            csv_path = questionary.path("Selecione o arquivo CSV:").ask()
            if not csv_path:
                return None, None
            
            df = pd.read_csv(csv_path)
            return csv_path, df
        except Exception:
            return None, None
    
    def select_template(self):
        """Seleciona template."""
        import questionary
        
        templates = self.services["template_manager"].list_templates()
        if not templates:
            return None
        
        return questionary.select(
            "Selecione o template:",
            choices=templates
        ).ask()
    
    def select_theme(self):
        """Seleciona tema."""
        import questionary
        
        themes = ["❌ Nenhum tema"] + self.services["theme_manager"].list_themes()
        
        choice = questionary.select(
            "Selecione um tema:",
            choices=themes
        ).ask()
        
        return None if choice == "❌ Nenhum tema" else choice
    
    def collect_event_details(self):
        """Coleta detalhes do evento."""
        import questionary
        
        evento = questionary.text("Nome do evento:").ask()
        if not evento:
            return None
        
        data = questionary.text("Data do evento:").ask()
        local = questionary.text("Local do evento:").ask()
        carga_horaria = questionary.text("Carga horária:").ask()
        
        return {
            "evento": evento,
            "data": data,
            "local": local,
            "carga_horaria": carga_horaria
        }
    
    def confirm_generation_details(self, details):
        """Confirma detalhes da geração."""
        import questionary
        
        return questionary.confirm("Confirma os detalhes da geração?").ask()
    
    def execute_generation(self, details):
        """Executa a geração."""
        return self.services["certificate_service"].generate_certificates_batch(
            csv_file_path=details["csv_file"],
            event_details=details["event_details"],
            template_name=details["template"],
            theme_name=details["theme"]
        )
    
    def ask_create_zip(self, files):
        """Pergunta sobre criação de ZIP."""
        import questionary
        
        if not files:
            return False
        
        return questionary.confirm("Deseja criar arquivo ZIP?").ask()
    
    def get_zip_filename(self):
        """Obtém nome do arquivo ZIP."""
        import questionary
        
        filename = questionary.text("Nome do arquivo ZIP:").ask()
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"certificados_{timestamp}"
        
        if not filename.endswith('.zip'):
            filename += '.zip'
        
        return filename
    
    def create_zip_file(self, files, zip_name):
        """Cria arquivo ZIP."""
        try:
            self.services["zip_exporter"].create_zip(files, zip_name)
            return True
        except Exception:
            return False
    
    def validate_csv_data(self, df):
        """Valida dados do CSV."""
        if df.empty:
            return False
        
        # Verificar se tem coluna 'nome' ou pelo menos uma coluna
        if "nome" not in df.columns and len(df.columns) == 0:
            return False
        
        return True
    
    def handle_csv_header_question(self):
        """Pergunta sobre cabeçalho do CSV."""
        import questionary
        
        return questionary.confirm("O arquivo CSV possui cabeçalho?").ask()
