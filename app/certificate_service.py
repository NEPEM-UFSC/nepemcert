import os
import random
from datetime import datetime
import pandas as pd # Ensure pandas is imported
import jinja2 # Added for direct string template rendering

from .csv_manager import CSVManager
from .template_manager import TemplateManager
from .pdf_generator import PDFGenerator
from .authentication_manager import AuthenticationManager
from .parameter_manager import ParameterManager
from .theme_manager import ThemeManager


class CertificateService:
    def __init__(self, output_dir="output"):
        self.csv_manager = CSVManager()
        self.template_manager = TemplateManager()
        self.pdf_generator = PDFGenerator(output_dir=output_dir)
        self.auth_manager = AuthenticationManager()
        self.parameter_manager = ParameterManager()
        self.theme_manager = ThemeManager()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_certificates_batch(self, csv_file_path, event_details, template_name, theme_name=None, has_header=True, use_multiprocessing=False):
        """
        Gera certificados em lote a partir de um arquivo CSV.
        
        Args:
            csv_file_path (str): Caminho para o arquivo CSV com dados dos participantes
            event_details (dict): Detalhes do evento (nome, data, local, carga_horaria)
            template_name (str): Nome do template a ser usado
            theme_name (str, optional): Nome do tema a ser aplicado
            has_header (bool): Se o CSV tem cabeçalho na primeira linha
            use_multiprocessing (bool): Se deve usar processamento paralelo (padrão: False)
        
        Returns:
            dict: Resultado da geração com contadores e listas de arquivos/erros
        """
        result = {
            "success_count": 0,
            "failed_count": 0,
            "generated_files": [],
            "errors": []
        }
        
        try:
            # 1. Carregar dados do CSV
            df = self.csv_manager.load_data(csv_file_path)
            
            if df.empty:
                result["failed_count"] = -1
                result["errors"].append("CSV file is empty or could not be loaded")
                return result
            
            # 2. Processar cabeçalho se necessário
            if has_header and len(df) > 0:
                # Se tem cabeçalho, verificar se a primeira linha parece ser um cabeçalho
                if df.iloc[0, 0].lower() in ['nome', 'name', 'participante']:
                    df = df.iloc[1:].reset_index(drop=True)
            
            # 3. Validar se há dados após processamento do cabeçalho
            if df.empty:
                result["failed_count"] = -1
                result["errors"].append("No participant data found after header processing")
                return result
            
            # 4. Carregar template
            template_content = self.template_manager.load_template(template_name)
            if not template_content:
                result["failed_count"] = -1
                result["errors"].append(f"Template '{template_name}' not found")
                return result
            
            # 5. Aplicar tema se especificado
            if theme_name:
                theme_settings = self.theme_manager.load_theme(theme_name)
                if theme_settings:
                    try:
                        template_content = self.theme_manager.apply_theme_to_template(template_content, theme_settings)
                    except Exception as e:
                        result["errors"].append(f"Error applying theme '{theme_name}': {str(e)}")
                        # Continuar sem tema em caso de erro
            
            # 6. Preparar dados para geração em lote
            html_contents = []
            file_paths = []
            
            for index, row in df.iterrows():
                try:
                    # Preparar dados do participante
                    participant_data = {"nome": row.iloc[0]}  # Primeira coluna é sempre o nome
                    
                    # Adicionar detalhes do evento
                    participant_data.update(event_details)
                    
                    # Adicionar dados de emissão
                    from datetime import datetime
                    participant_data["data_emissao"] = datetime.now().strftime("%d/%m/%Y")
                    participant_data["cidade"] = "Florianópolis"  # Pode ser configurável
                    
                    # Gerar código de autenticação
                    auth_code = self.auth_manager.gerar_codigo_autenticacao(
                        participant_data["nome"], 
                        event_details.get("evento", "Evento")
                    )
                    
                    # Salvar código de autenticação
                    self.auth_manager.salvar_codigo(
                        auth_code,
                        participant_data["nome"],
                        event_details.get("evento", "Evento"),
                        event_details.get("data", ""),
                        event_details.get("local", ""),
                        event_details.get("carga_horaria", "")
                    )
                    
                    participant_data["codigo_verificacao"] = auth_code
                    participant_data["url_verificacao"] = "https://nepemufsc.com/verificar"
                    
                    # Mesclar com parâmetros do sistema
                    final_data = self.parameter_manager.merge_placeholders(participant_data, theme_name)
                    
                    # Renderizar template
                    html_content = self.template_manager.render_template_from_string(template_content, final_data)
                    
                    # Gerar QR code e substituir placeholder - USAR MÉTODO CORRETO
                    qr_base64 = self.auth_manager.gerar_qrcode_base64(auth_code)
                    html_content = self.auth_manager.substituir_qr_placeholder(html_content, qr_base64)
                    
                    html_contents.append(html_content)
                    
                    # Preparar nome do arquivo
                    safe_name = self._sanitize_filename(participant_data["nome"])
                    pdf_filename = f"certificado_{safe_name}_{index + 1}.pdf"
                    pdf_path = os.path.join(self.output_dir, pdf_filename)
                    file_paths.append(pdf_path)
                    
                except Exception as e:
                    result["errors"].append(f"Error processing participant {index + 1}: {str(e)}")
                    result["failed_count"] += 1
                    continue
            
            # 7. Gerar PDFs em lote (sequencial por padrão)
            if html_contents:
                try:
                    generated_paths = self.pdf_generator.batch_generate(
                        html_contents, 
                        file_paths, 
                        orientation="landscape",
                        use_multiprocessing=use_multiprocessing  # Passar o parâmetro
                    )
                    
                    result["generated_files"] = generated_paths
                    result["success_count"] = len(generated_paths)
                    result["failed_count"] = len(html_contents) - len(generated_paths)
                    
                except Exception as e:
                    result["failed_count"] = len(html_contents)
                    result["errors"].append(f"Error during batch PDF generation: {str(e)}")
            
        except Exception as e:
            result["failed_count"] = -1
            result["errors"].append(f"Error loading CSV: {str(e)}")
        
        return result

    def _sanitize_filename(self, name):
        """
        Sanitize the filename by removing or replacing invalid characters.
        """
        # Replace or remove characters that are not allowed in filenames
        return "".join(c if c.isalnum() or c in (' ', '_') else "_" for c in name).strip("_")
