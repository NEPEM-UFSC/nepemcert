"""
Testes de unidade para o módulo certificate_service.py
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.certificate_service import CertificateService
# Mocked versions of dependencies if they are not easily instantiable or for isolation
# For this test, we'll mock the methods of instances.

class TestCertificateService(unittest.TestCase):

    def setUp(self):
        """Configura o ambiente para cada teste."""
        self.output_dir = "tests/temp_cert_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Patch all external managers
        self.patch_csv_manager = patch('app.certificate_service.CSVManager')
        self.mock_csv_manager_cls = self.patch_csv_manager.start()
        self.mock_csv_manager = self.mock_csv_manager_cls.return_value

        self.patch_template_manager = patch('app.certificate_service.TemplateManager')
        self.mock_template_manager_cls = self.patch_template_manager.start()
        self.mock_template_manager = self.mock_template_manager_cls.return_value

        self.patch_pdf_generator = patch('app.certificate_service.PDFGenerator')
        self.mock_pdf_generator_cls = self.patch_pdf_generator.start()
        self.mock_pdf_generator = self.mock_pdf_generator_cls.return_value

        self.patch_auth_manager = patch('app.certificate_service.AuthenticationManager')
        self.mock_auth_manager_cls = self.patch_auth_manager.start()
        self.mock_auth_manager = self.mock_auth_manager_cls.return_value

        self.patch_param_manager = patch('app.certificate_service.ParameterManager')
        self.mock_param_manager_cls = self.patch_param_manager.start()
        self.mock_param_manager = self.mock_param_manager_cls.return_value
        
        self.patch_theme_manager = patch('app.certificate_service.ThemeManager')
        self.mock_theme_manager_cls = self.patch_theme_manager.start()
        self.mock_theme_manager = self.mock_theme_manager_cls.return_value

        self.service = CertificateService(output_dir=self.output_dir)

    def tearDown(self):
        """Limpa após cada teste."""
        self.patch_csv_manager.stop()
        self.patch_template_manager.stop()
        self.patch_pdf_generator.stop()
        self.patch_auth_manager.stop()
        self.patch_param_manager.stop()
        self.patch_theme_manager.stop()
        
        # Limpar diretório de saída temporário
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                os.remove(os.path.join(self.output_dir, f))
            os.rmdir(self.output_dir)

    def test_generate_certificates_batch_success(self):
        """Testa a geração de certificados em lote com sucesso."""
        sample_df = pd.DataFrame({"nome": ["Alice", "Bob"]})
        self.mock_csv_manager.load_data.return_value = sample_df
        
        base_template_html = "<html><head></head><body>Olá {{ nome }}, seu código é {{ codigo_autenticacao }}. <div id='qr-code-placeholder'></div></body></html>"
        themed_template_html = "<html><head><style>/*themed*/</style></head><body>Olá {{ nome }}, seu código é {{ codigo_autenticacao }}. <div id='qr-code-placeholder'></div></body></html>"
        self.mock_template_manager.load_template.return_value = base_template_html
        self.mock_theme_manager.load_theme.return_value = {"font_family": "Arial"}
        self.mock_theme_manager.apply_theme_to_template.return_value = themed_template_html

        self.mock_auth_manager.gerar_codigo_autenticacao.side_effect = ["code_alice", "code_bob"]
        self.mock_auth_manager.gerar_qrcode_data.side_effect = ["url_alice", "url_bob"]
        self.mock_auth_manager.gerar_qrcode_base64.side_effect = ["qr_alice_b64", "qr_bob_b64"]
        # Mock substituir_qr_placeholder para retornar o HTML com o QR code mockado
        self.mock_auth_manager.substituir_qr_placeholder.side_effect = lambda html, qr: html.replace("<div id='qr-code-placeholder'></div>", f"<img src='{qr}'>")

        self.mock_param_manager.get_institutional_placeholders.return_value = {"url_verificacao": "http://verify.com"}
        self.mock_param_manager.merge_placeholders.side_effect = lambda d, t: d # Simplesmente retorna os dados

        # PDFGenerator.batch_generate retorna a lista de arquivos gerados com sucesso
        expected_pdf_paths = [os.path.join(self.output_dir, "certificado_Alice_1.pdf"), os.path.join(self.output_dir, "certificado_Bob_2.pdf")]
        self.mock_pdf_generator.batch_generate.return_value = expected_pdf_paths

        event_details = {"evento": "Evento Teste", "data": "01/01/2024", "local": "Online", "carga_horaria": "10"}
        results = self.service.generate_certificates_batch("dummy.csv", event_details, "template.html", "tema_teste")

        self.assertEqual(results["success_count"], 2)
        self.assertEqual(results["failed_count"], 0)
        self.assertEqual(len(results["generated_files"]), 2)
        self.assertEqual(results["generated_files"], expected_pdf_paths)
        self.assertEqual(results["errors"], [])
        self.assertEqual(results["warnings"], [])
        
        # Verificar se os mocks foram chamados corretamente
        self.mock_csv_manager.load_data.assert_called_once_with("dummy.csv")
        self.mock_template_manager.load_template.assert_called_once_with("template.html")
        self.mock_theme_manager.apply_theme_to_template.assert_called_once_with(base_template_html, {"font_family": "Arial"})
        
        # Verificar chamadas para AuthenticationManager
        self.assertEqual(self.mock_auth_manager.gerar_codigo_autenticacao.call_count, 2)
        self.assertEqual(self.mock_auth_manager.salvar_codigo.call_count, 2)
        self.assertEqual(self.mock_auth_manager.gerar_qrcode_base64.call_count, 2)
        self.assertEqual(self.mock_auth_manager.substituir_qr_placeholder.call_count, 2)

        # Verificar os argumentos para PDFGenerator.batch_generate
        # O primeiro argumento é html_contents
        args_call_pdf_gen = self.mock_pdf_generator.batch_generate.call_args
        self.assertEqual(len(args_call_pdf_gen[0][0]), 2) # Dois conteúdos HTML
        self.assertIn("Olá Alice", args_call_pdf_gen[0][0][0]) # Conteúdo HTML renderizado para Alice
        self.assertIn("<img src='qr_alice_b64'>", args_call_pdf_gen[0][0][0]) # QR code substituído
        self.assertIn("Olá Bob", args_call_pdf_gen[0][0][1]) # Conteúdo HTML renderizado para Bob
        self.assertIn("<img src='qr_bob_b64'>", args_call_pdf_gen[0][0][1])

    def test_generate_certificates_csv_empty_nome_warning(self):
        """Testa aviso para nomes vazios no CSV."""
        # Um nome válido, um NaN
        sample_df = pd.DataFrame({"nome": ["Alice", None, "Bob", float('nan')]})
        self.mock_csv_manager.load_data.return_value = sample_df
        self.mock_template_manager.load_template.return_value = "Olá {{ nome }}"
        self.mock_theme_manager.apply_theme_to_template.side_effect = lambda html, theme: html # No theming
        self.mock_auth_manager.gerar_codigo_autenticacao.return_value = "code"
        self.mock_auth_manager.gerar_qrcode_base64.return_value = "qr_b64"
        self.mock_auth_manager.substituir_qr_placeholder.side_effect = lambda html, qr: html
        self.mock_param_manager.get_institutional_placeholders.return_value = {}
        self.mock_param_manager.merge_placeholders.side_effect = lambda d, t: d
        self.mock_pdf_generator.batch_generate.return_value = [
            os.path.join(self.output_dir, "certificado_Alice_1.pdf"),
            os.path.join(self.output_dir, "certificado_Bob_3.pdf") # Bob é o terceiro (index 2, row 3)
        ]


        event_details = {"evento": "Evento Teste"}
        results = self.service.generate_certificates_batch("dummy.csv", event_details, "t.html", None)
        
        self.assertEqual(results["success_count"], 2) # Alice e Bob
        self.assertEqual(results["failed_count"], 0) # NaN não são falhas de processamento, são avisos/skip
        self.assertIn("CSV contains 2 empty 'nome' values that will be skipped.", results["warnings"])

    def test_generate_certificates_participant_processing_error(self):
        """Testa erro durante o processamento de um participante."""
        sample_df = pd.DataFrame({"nome": ["Alice", "Problematic Bob"]})
        self.mock_csv_manager.load_data.return_value = sample_df
        self.mock_template_manager.load_template.return_value = "Olá {{ nome }}"
        self.mock_theme_manager.apply_theme_to_template.side_effect = lambda html, theme: html

        def auth_side_effect(nome_participante, evento, data_evento):
            if "Problematic Bob" in nome_participante:
                raise Exception("Erro ao gerar código para Bob")
            return f"code_{nome_participante}"
        self.mock_auth_manager.gerar_codigo_autenticacao.side_effect = auth_side_effect
        # ... outros mocks ...
        self.mock_auth_manager.gerar_qrcode_base64.return_value = "qr_b64"
        self.mock_auth_manager.substituir_qr_placeholder.side_effect = lambda html, qr: html
        self.mock_param_manager.get_institutional_placeholders.return_value = {}
        self.mock_param_manager.merge_placeholders.side_effect = lambda d, t: d
        self.mock_pdf_generator.batch_generate.return_value = [os.path.join(self.output_dir, "certificado_Alice_1.pdf")]


        event_details = {"evento": "Evento Teste"}
        results = self.service.generate_certificates_batch("dummy.csv", event_details, "t.html", None)

        self.assertEqual(results["success_count"], 1)
        self.assertEqual(results["failed_count"], 1)
        self.assertEqual(len(results["errors"]), 1)
        self.assertIn("Error processing participant Problematic Bob (row 2): Erro ao gerar código para Bob", results["errors"][0])

    def test_load_csv_error(self):
        """Testa erro ao carregar CSV."""
        self.mock_csv_manager.load_data.side_effect = Exception("Falha ao ler CSV")
        results = self.service.generate_certificates_batch("bad.csv", {}, "t.html", None)
        self.assertEqual(results["success_count"], 0)
        self.assertEqual(results["failed_count"], 0) # Nenhum processado
        self.assertIn("Error loading CSV from 'bad.csv': Falha ao ler CSV", results["errors"])
        
    def test_load_template_error(self):
        """Testa erro ao carregar template."""
        self.mock_csv_manager.load_data.return_value = pd.DataFrame({"nome": ["Test"]})
        self.mock_template_manager.load_template.side_effect = Exception("Template não encontrado")
        results = self.service.generate_certificates_batch("d.csv", {}, "bad.html", None)
        self.assertIn("Error loading template 'bad.html': Template não encontrado", results["errors"])

    def test_apply_theme_error(self):
        """Testa erro ao aplicar tema."""
        self.mock_csv_manager.load_data.return_value = pd.DataFrame({"nome": ["Test"]})
        self.mock_template_manager.load_template.return_value = "<html></html>"
        self.mock_theme_manager.load_theme.return_value = {"some_setting": "value"}
        self.mock_theme_manager.apply_theme_to_template.side_effect = Exception("Falha ao aplicar tema")
        results = self.service.generate_certificates_batch("d.csv", {}, "t.html", "bad_theme")
        self.assertIn("Error applying theme 'bad_theme': Falha ao aplicar tema", results["errors"])


if __name__ == '__main__':
    unittest.main()
