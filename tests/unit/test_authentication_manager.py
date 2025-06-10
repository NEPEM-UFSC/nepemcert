"""
Testes de unidade para o módulo authentication_manager.py
Testa a geração de códigos, armazenamento em SQLite e funcionalidades de QR code.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import base64
from pathlib import Path

# Adicionar o diretório raiz do projeto ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.authentication_manager import AuthenticationManager

class TestAuthenticationManager(unittest.TestCase):

    def setUp(self):
        """Configura um banco de dados SQLite em memória para cada teste."""
        self.db_path = ":memory:"
        # Mock o os.path.abspath e os.path.dirname para que o db_path seja :memory:
        # Isso é um pouco complexo porque o db_path é construído no __init__
        # Uma abordagem mais fácil é passar o db_path para o construtor ou mockar o connect.
        
        # Vamos mockar sqlite3.connect para sempre usar :memory: para esta classe de teste
        self.patcher = patch('sqlite3.connect')
        self.mock_connect = self.patcher.start()
        
        # Configurar o mock_connect para retornar uma conexão real em memória
        # mas precisamos garantir que a mesma conexão seja retornada se chamada múltiplas vezes
        # no __init__ e em _create_table. Para simplificar, assumimos que __init__
        # cria a conexão e a armazena em self.conn.
        
        self.memory_conn = sqlite3.connect(":memory:")
        self.memory_conn.row_factory = sqlite3.Row # Definir row_factory aqui também
        self.mock_connect.return_value = self.memory_conn
        
        self.auth_manager = AuthenticationManager(salt="test_salt")
        # O _create_table já deve ter sido chamado no __init__ do AuthenticationManager

    def tearDown(self):
        """Fecha a conexão e para o patcher após cada teste."""
        self.auth_manager.close_connection() # Usa o método close_connection da classe
        self.patcher.stop()

    def test_create_table_idempotency(self):
        """Testa se _create_table pode ser chamado múltiplas vezes sem erro."""
        # _create_table é chamado no __init__. Chamamos de novo para testar idempotência.
        try:
            self.auth_manager._create_table()
            # Tentar inserir algo para garantir que a tabela existe e está funcional
            cursor = self.auth_manager.conn.cursor()
            cursor.execute("INSERT INTO auth_codes (codigo_autenticacao) VALUES (?)", ("test_code_idempotency",))
            self.auth_manager.conn.commit()
            cursor.execute("SELECT * FROM auth_codes WHERE codigo_autenticacao = ?", ("test_code_idempotency",))
            self.assertIsNotNone(cursor.fetchone())
        except Exception as e:
            self.fail(f"_create_table idempotency test failed: {e}")


    def test_salvar_e_verificar_codigo(self):
        """Testa salvar um código e depois verificá-lo"""
        codigo = self.auth_manager.gerar_codigo_autenticacao("João Silva", "Workshop Python")
        
        # Salvar o código com dados completos
        resultado = self.auth_manager.salvar_codigo(
            codigo, 
            "João Silva", 
            "Workshop Python", 
            "15/05/2025", 
            "Auditório Central", 
            "40 horas"
        )
        assert resultado is True
        
        # Verificar o código
        dados = self.auth_manager.verificar_codigo(codigo)
        assert dados is not None
        # Verificar as chaves que realmente existem no dicionário retornado
        assert "nome" in dados or "nome_participante" in dados
        # Usar a chave correta dependendo da implementação
        nome_key = "nome" if "nome" in dados else "nome_participante"
        assert dados[nome_key] == "João Silva"
        assert dados["evento"] == "Workshop Python"
        assert dados["data"] == "15/05/2025"

    def test_verificar_codigo_nao_existente(self):
        """Testa verificar um código que não existe"""
        dados = self.auth_manager.verificar_codigo("CODIGO_INEXISTENTE")
        # Verificar se retorna None ou dicionário vazio dependendo da implementação
        assert dados is None or dados == {}

    def test_gerar_codigo_autenticacao_formato(self):
        """Testa o formato do código de autenticação gerado."""
        codigo = self.auth_manager.gerar_codigo_autenticacao("Participante X", "Evento Y", "02/01/2024")
        self.assertIsInstance(codigo, str)
        self.assertEqual(len(codigo), 32) # SHA-256 truncado para 32 chars
        try:
            int(codigo, 16) # Deve ser um hexadecimal
        except ValueError:
            self.fail("Código de autenticação não é um hexadecimal válido.")

    def test_gerar_qrcode_base64(self):
        """Testa se gerar_qrcode_base64 retorna uma string base64 válida."""
        codigo = "test_qr_code_data"
        qr_base64 = self.auth_manager.gerar_qrcode_base64(codigo)
        self.assertTrue(qr_base64.startswith("data:image/png;base64,"))
        try:
            base64.b64decode(qr_base64.split(",")[1])
        except Exception:
            self.fail("gerar_qrcode_base64 não retornou uma string base64 válida.")

    def test_substituir_qr_placeholder_presente(self):
        """Testa substituir_qr_placeholder quando o placeholder existe."""
        html_content = '<html><head></head><body><div id="qr-code-placeholder"></div></body></html>'
        qrcode_base64 = "fake_base64_string"
        
        modified_html = self.auth_manager.substituir_qr_placeholder(html_content, qrcode_base64)
        
        expected_replacement = f'<div id="qr-code-placeholder"><img src="{qrcode_base64}" alt="QR Code de verificação" style="width:100%; height:100%; display:block;"></div>'
        self.assertIn(expected_replacement, modified_html)
        self.assertNotIn('<div id="qr-code-placeholder"></div>', modified_html) # O placeholder original vazio não deve mais existir

    def test_substituir_qr_placeholder_ausente(self):
        """Testa substituir_qr_placeholder quando o placeholder não existe."""
        html_content = "<html><head></head><body><p>Sem placeholder.</p></body></html>"
        qrcode_base64 = "fake_base64_string"
        
        modified_html = self.auth_manager.substituir_qr_placeholder(html_content, qrcode_base64)
        self.assertEqual(modified_html, html_content) # HTML não deve ser modificado

    def test_salvar_codigo_sqlite_error(self):
        """Testa o tratamento de erro ao salvar no SQLite."""
        # Forçar um erro no commit
        with patch.object(self.auth_manager.conn, 'commit', side_effect=sqlite3.Error("Simulated DB error")):
            saved = self.auth_manager.salvar_codigo("code", "name", "event", "date", "local", "ch")
            self.assertFalse(saved)

    def test_verificar_codigo_sqlite_error(self):
        """Testa o tratamento de erro ao verificar no SQLite."""
        # Forçar um erro no execute
        with patch.object(self.auth_manager.conn, 'cursor') as mock_cursor_ctx:
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = sqlite3.Error("Simulated DB error")
            mock_cursor_ctx.return_value = mock_cursor
            
            retrieved = self.auth_manager.verificar_codigo("some_code")
            self.assertIsNone(retrieved)

if __name__ == '__main__':
    unittest.main()
