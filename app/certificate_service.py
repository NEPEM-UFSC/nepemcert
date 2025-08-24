import os
import random
from datetime import datetime
import pandas as pd # Ensure pandas is imported
import jinja2 # Added for direct string template rendering

from .csv_manager import CSVManager
from .template_manager import TemplateManager
from .pdf_generator import PDFGenerator
from .cert_auth_manager import CertAuthenticationManager
from .parameter_manager import ParameterManager
from .theme_manager import ThemeManager
from .offline_sync_manager import OfflineSyncManager


class CertificateService:
    def __init__(self, output_dir="output"):
        self.csv_manager = CSVManager()
        self.template_manager = TemplateManager()
        self.pdf_generator = PDFGenerator(output_dir=output_dir)
        self.auth_manager =CertAuthenticationManager()
        self.parameter_manager = ParameterManager()
        self.theme_manager = ThemeManager()
        self.offline_sync_manager = OfflineSyncManager()
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
                
            # 2. O CSV já foi processado pelo CLI, então não precisamos reprocessar o cabeçalho
            # Vamos apenas garantir que temos dados válidos
            if df.empty:
                result["failed_count"] = -1
                result["errors"].append("No participant data found in CSV")
                return result
            
            # 3. Verificar se a primeira coluna contém os nomes
            if len(df.columns) == 0:
                result["failed_count"] = -1
                result["errors"].append("CSV has no columns")
                return result
            
            # 4. Garantir que estamos usando a primeira coluna como nome
            # O CLI já processou o CSV e garantiu que a primeira coluna é 'nome'
            if 'nome' not in df.columns:
                # Se não tem coluna 'nome', usar a primeira coluna
                df = df.rename(columns={df.columns[0]: 'nome'})
            
            # 5. Remover registros com nomes vazios
            df = df.dropna(subset=['nome'])
            df = df[df['nome'].str.strip() != '']
            
            if df.empty:
                result["failed_count"] = -1
                result["errors"].append("No valid participant names found in CSV")
                return result
            
            # 6. Carregar template
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
                    
                    # Salvar código de autenticação localmente (método original)
                    self.auth_manager.salvar_codigo(
                        auth_code,
                        participant_data["nome"],
                        event_details.get("evento", "Evento"),
                        event_details.get("data", ""),
                        event_details.get("local", ""),
                        event_details.get("carga_horaria", "")
                    )
                    
                    participant_data["codigo_verificacao"] = auth_code
                    participant_data["url_verificacao"] = "https://certificados.nepemufsc.com"
                    
                    # Mesclar com parâmetros do sistema ANTES de usar final_data
                    final_data = self.parameter_manager.merge_placeholders(participant_data, theme_name)
                    
                    # IMPORTANTE: Gerar assinatura ANTES da renderização do template
                    assinatura_path = os.path.join(os.getcwd(), "app", "auth", "rubrica-olivoto.png")
                    if os.path.exists(assinatura_path):
                        rubrica_coordenador = self.auth_manager.gerar_assinatura_base64(assinatura_path)
                        final_data["signature_image"] = rubrica_coordenador
                    else:
                        final_data["signature_image"] = None
                        result["errors"].append(f"Warning: Signature image not found at {assinatura_path}")
                    
                    # NOVO: Armazenar no sistema offline para sincronização posterior
                    certificate_data_for_sync = {
                        'codigo_autenticacao': auth_code,
                        'nome_participante': participant_data["nome"],
                        'evento': event_details.get("evento", "Evento"),
                        'data_evento': event_details.get("data", ""),
                        'local_evento': event_details.get("local", ""),
                        'carga_horaria': event_details.get("carga_horaria", ""),
                        'coordenador': final_data.get("coordenador", ""),
                        'diretor': final_data.get("diretor", ""),
                        'data_geracao': datetime.now().isoformat(),
                        'url_verificacao': "https://certificados.nepemufsc.com",
                        'qrcode_base64': self.auth_manager.gerar_qrcode_base64(auth_code),
                        'template_usado': template_name,
                        'tema_usado': theme_name or "default"
                    }
                    
                    # Armazenar para sincronização offline
                    sync_stored = self.offline_sync_manager.store_certificate(certificate_data_for_sync)
                    if not sync_stored:
                        result["errors"].append(f"Warning: Failed to store {participant_data['nome']} for offline sync")
                    
                    # Renderizar template COM a assinatura já incluída nos dados
                    html_content = self.template_manager.render_template_from_string(template_content, final_data)
                    
                    # Gerar QR code e substituir placeholder
                    qr_base64 = self.auth_manager.gerar_qrcode_base64(auth_code)
                    html_content = self.auth_manager.substituir_qr_placeholder(html_content, qr_base64)
                    
                    # Adicionar o HTML renderizado à lista
                    html_contents.append(html_content)
                    
                    # Preparar nome do arquivo
                    safe_name = self._sanitize_filename(participant_data["nome"])
                    pdf_filename = f"certificado_{safe_name}_{int(index) + 1}.pdf"
                    pdf_path = os.path.join(self.output_dir, pdf_filename)
                    file_paths.append(pdf_path)
                    
                except Exception as e:
                    result["errors"].append(f"Error processing participant {int(index) + 1}: {str(e)}")
                    result["failed_count"] += 1
                    continue
            
            # 7. Gerar PDFs em lote (sequencial por padrão)
            if html_contents:
                try:
                    generated_paths = self.pdf_generator.batch_generate(
                        html_contents, 
                        file_paths, 
                        orientation="landscape",
                        use_multiprocessing=use_multiprocessing
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
    
    def generate_single_certificate(self, participant_name, event_details, template_name, theme_name=None):
        """
        Gera um único certificado para um participante.
        
        Args:
            participant_name (str): Nome do participante
            event_details (dict): Detalhes do evento (nome, data, local, carga_horaria)
            template_name (str): Nome do template a ser usado
            theme_name (str, optional): Nome do tema a ser aplicado
        
        Returns:
            dict: Resultado da geração com status e caminho do arquivo ou erro
        """
        result = {
            "success": False,
            "generated_file": None,
            "error": None
        }
        
        try:
            # 1. Validar entrada
            if not participant_name or not participant_name.strip():
                result["error"] = "Nome do participante não pode estar vazio"
                return result
            
            participant_name = participant_name.strip()
            
            # 2. Carregar template
            template_content = self.template_manager.load_template(template_name)
            if not template_content:
                result["error"] = f"Template '{template_name}' não encontrado"
                return result
            
            # 3. Aplicar tema se especificado
            if theme_name:
                theme_settings = self.theme_manager.load_theme(theme_name)
                if theme_settings:
                    try:
                        template_content = self.theme_manager.apply_theme_to_template(template_content, theme_settings)
                    except Exception as e:
                        result["error"] = f"Erro ao aplicar tema '{theme_name}': {str(e)}"
                        return result
            
            # 4. Preparar dados do participante
            participant_data = {"nome": participant_name}
            
            # 5. Adicionar detalhes do evento
            participant_data.update(event_details)
            
            # 6. Adicionar dados de emissão
            from datetime import datetime
            participant_data["data_emissao"] = datetime.now().strftime("%d/%m/%Y")
            participant_data["cidade"] = "Florianópolis"  # Pode ser configurável
            
            # 7. Gerar código de autenticação
            auth_code = self.auth_manager.gerar_codigo_autenticacao(
                participant_data["nome"], 
                event_details.get("evento", "Evento")
            )
            
            # 8. Salvar código de autenticação localmente (método original)
            self.auth_manager.salvar_codigo(
                auth_code,
                participant_data["nome"],
                event_details.get("evento", "Evento"),
                event_details.get("data", ""),
                event_details.get("local", ""),
                event_details.get("carga_horaria", "")
            )
            
            participant_data["codigo_verificacao"] = auth_code
            participant_data["url_verificacao"] = "https://certificados.nepemufsc.com"
            
            # 9. Mesclar com parâmetros do sistema
            final_data = self.parameter_manager.merge_placeholders(participant_data, theme_name)
            
            # 10. Gerar assinatura ANTES da renderização do template
            assinatura_path = os.path.join(os.getcwd(), "app", "auth", "rubrica-olivoto.png")
            if os.path.exists(assinatura_path):
                rubrica_coordenador = self.auth_manager.gerar_assinatura_base64(assinatura_path)
                final_data["signature_image"] = rubrica_coordenador
            else:
                final_data["signature_image"] = None
                result["error"] = f"Warning: Signature image not found at {assinatura_path}"

            # 10. Armazenar no sistema offline para sincronização posterior
            certificate_data_for_sync = {
                'codigo_autenticacao': auth_code,
                'nome_participante': participant_data["nome"],
                'evento': event_details.get("evento", "Evento"),
                'data_evento': event_details.get("data", ""),
                'local_evento': event_details.get("local", ""),
                'carga_horaria': event_details.get("carga_horaria", ""),
                'coordenador': final_data.get("coordenador", ""),
                'diretor': final_data.get("diretor", ""),
                'data_geracao': datetime.now().isoformat(),
                'url_verificacao': "https://certificados.nepemufsc.com",
                'qrcode_base64': self.auth_manager.gerar_qrcode_base64(auth_code),
                'template_usado': template_name,
                'tema_usado': theme_name or "default"
            }
            
            # 11. Armazenar para sincronização offline
            sync_stored = self.offline_sync_manager.store_certificate(certificate_data_for_sync)
            if not sync_stored:
                result["error"] = f"Falha ao armazenar certificado para sincronização offline"
                return result
            
            # 12. Renderizar template
            html_content = self.template_manager.render_template_from_string(template_content, final_data)
            
            # 13. Gerar QR code e substituir placeholder
            qr_base64 = self.auth_manager.gerar_qrcode_base64(auth_code)
            html_content = self.auth_manager.substituir_qr_placeholder(html_content, qr_base64)
            
            # 14. Preparar nome do arquivo
            safe_name = self._sanitize_filename(participant_data["nome"])
            pdf_filename = f"certificado_{safe_name}.pdf"
            pdf_path = os.path.join(self.output_dir, pdf_filename)
            
            # 15. Gerar PDF
            generated_path = self.pdf_generator.generate_pdf(
                html_content, 
                pdf_path, 
                orientation="landscape"
            )
            
            if generated_path:
                result["success"] = True
                result["generated_file"] = generated_path
            else:
                result["error"] = "Falha na geração do PDF"
            
        except Exception as e:
            result["error"] = f"Erro na geração do certificado: {str(e)}"
        
        return result
