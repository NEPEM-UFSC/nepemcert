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

    def generate_certificates_batch(self, csv_file_path, event_details, template_name, theme_name, has_header=True):
        """
        Generates certificates in batch.

        Args:
            csv_file_path (str): Path to the CSV file.
            event_details (dict): Dictionary containing event details like
                                  'evento', 'data', 'local', 'carga_horaria'.
            template_name (str): Name of the template file (e.g., 'template.html').
            theme_name (str or None): Name of the theme to apply, or None.
            has_header (bool): Whether the CSV file has a header row.

        Returns:
            dict: A dictionary containing 'success_count', 'failed_count', 
                  'generated_files', and 'errors'.
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "generated_files": [],
            "errors": [],
            "warnings": [] # Initialized warnings list
        }

        # Load CSV data
        try:
            if has_header:
                df = self.csv_manager.load_data(csv_file_path)
                if "nome" not in df.columns:
                    if len(df.columns) == 1:
                        df.columns = ["nome"] 
                    else:
                        results["errors"].append("CSV with header must contain a 'nome' column.")
                        results["failed_count"] = -1 
                        return results
            else:
                df = pd.read_csv(csv_file_path, header=None, names=["nome"], sep=',', encoding='utf-8')


            if df["nome"].isna().any():
                null_count = df["nome"].isna().sum()
                # Changed from results["errors"] to results["warnings"]
                results["warnings"].append(f"CSV contains {null_count} empty 'nome' values that will be skipped.")
            df = df.dropna(subset=["nome"])
            if df.empty:
                results["errors"].append("No valid participant data found in CSV after handling empty names.")
                return results
        except Exception as e:
            results["errors"].append(f"Error loading CSV from '{csv_file_path}': {str(e)}")
            return results

        # Load template content
        try:
            template_content = self.template_manager.load_template(template_name)
            if not template_content:
                results["errors"].append(f"Template '{template_name}' not found or empty.")
                return results
        except Exception as e:
            results["errors"].append(f"Error loading template '{template_name}': {str(e)}")
            return results

        if theme_name and theme_name.lower() != "nenhum":
            try:
                theme_settings = self.theme_manager.load_theme(theme_name)
                if theme_settings:
                    template_content = self.theme_manager.apply_theme_to_template(template_content, theme_settings)
            except Exception as e:
                results["errors"].append(f"Error applying theme '{theme_name}': {str(e)}")

        html_contents_to_generate = []
        pdf_file_paths = []
        base_data = {**event_details}

        # Create Jinja2 Template object once from the (potentially themed) template_content string
        try:
            jinja_template = jinja2.Template(template_content)
        except Exception as e_jinja_setup:
            results["errors"].append(f"Failed to create Jinja2 template: {str(e_jinja_setup)}")
            return results

        for index, row in df.iterrows():
            try:
                participant_name = str(row["nome"]).strip()
                if not participant_name:
                    results["errors"].append(f"Skipping row {index+1} due to empty participant name.")
                    results["failed_count"] += 1
                    continue

                participant_data = {"nome": participant_name}
                auth_code = self.auth_manager.gerar_codigo_autenticacao(
                    nome_participante=participant_name,
                    evento=event_details.get('evento', 'Evento Padrão'),
                    data_evento=event_details.get('data', '')
                )
                self.auth_manager.salvar_codigo(
                    codigo_autenticacao=auth_code,
                    nome_participante=participant_name,
                    evento=event_details.get('evento', 'Evento Padrão'),
                    data_evento=event_details.get('data', ''),
                    local_evento=event_details.get('local', ''),
                    carga_horaria=str(event_details.get('carga_horaria', '')) # Ensure carga_horaria is string
                )
                
                # Attempt to get URL from parameters, fallback to default
                institutional_params = self.parameter_manager.get_institutional_placeholders()
                url_base = institutional_params.get("url_verificacao", "https://nepemufsc.com/verificar-certificados")


                participant_data.update({
                    "codigo_autenticacao": auth_code,
                    "codigo_verificacao": auth_code,
                    "url_verificacao": url_base,
                    "url_qrcode": self.auth_manager.gerar_qrcode_data(auth_code), # data for QR code image
                    "data_emissao": datetime.now().strftime("%d/%m/%Y")
                })

                final_data = self.parameter_manager.merge_placeholders(
                    {**base_data, **participant_data},
                    theme_name if theme_name and theme_name.lower() != "nenhum" else None
                )
                
                # Generate QR code using the standardized gerar_qrcode_base64 method
                qrcode_base64 = self.auth_manager.gerar_qrcode_base64(auth_code, url_base=url_base)
                final_data["qrcode_base64"] = qrcode_base64 # Add to data for rendering if template uses it directly (e.g. for alt text or other data)

                # Note: The placeholder will be replaced in the rendered HTML.
                # template_content (themed) is used by jinja_template.

                # Render the template with participant data using the Jinja2 template object
                # final_data already includes qrcode_base64 if needed by template for non-image uses
                html_cert_content_rendered = jinja_template.render(final_data)
                
                # Replace the placeholder in the rendered HTML with the actual QR code image
                # The qrcode_base64 generated above is used here.
                html_cert_content = self.auth_manager.substituir_qr_placeholder(html_cert_content_rendered, qrcode_base64)

                # Removed temporary file logic for rendering

                safe_name = "".join(c if c.isalnum() else "_" for c in participant_name)
                pdf_file_name = f"certificado_{safe_name}_{index+1}.pdf"
                full_pdf_path = os.path.join(self.output_dir, pdf_file_name)

                html_contents_to_generate.append(html_cert_content)
                pdf_file_paths.append(full_pdf_path)
                
            except Exception as e_cert:
                results["errors"].append(f"Error processing participant {row.get('nome', 'N/A')} (row {index+1}): {str(e_cert)}")
                results["failed_count"] += 1

        if not html_contents_to_generate:
            if not results["errors"]:
                 results["errors"].append("No certificates could be prepared for generation.")
            return results

        try:
            self.pdf_generator.output_dir = self.output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            generated_pdf_files = self.pdf_generator.batch_generate(html_contents_to_generate, pdf_file_paths, orientation='landscape')
            results["generated_files"].extend(generated_pdf_files)
            results["success_count"] = len(generated_pdf_files)
        except Exception as e_batch:
            results["errors"].append(f"Error during batch PDF generation: {str(e_batch)}")
            results["failed_count"] += len(html_contents_to_generate) - results["success_count"]

        return results
