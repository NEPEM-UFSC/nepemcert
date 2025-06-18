#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final de validação do sistema NEPEMCERT
- Verifica se o processamento de CSV respeita corretamente o parâmetro has_header
- Testa a sincronização offline
- Testa a criação de ZIP
"""

import os
import tempfile
import pandas as pd
from datetime import datetime

from app.certificate_service import CertificateService
from app.offline_sync_manager import OfflineSyncManager
from app.zip_exporter import ZipExporter


def test_csv_processing():
    """Testa o processamento correto do CSV com e sem cabeçalho."""
    print("=" * 50)
    print("TESTE 1: Processamento de CSV")
    print("=" * 50)
    
    # Criar CSVs de teste
    with tempfile.TemporaryDirectory() as temp_dir:
        # CSV sem cabeçalho
        csv_sem_cabecalho = os.path.join(temp_dir, "sem_cabecalho.csv")
        with open(csv_sem_cabecalho, 'w', encoding='utf-8') as f:
            f.write("João Silva\n")
            f.write("Maria Santos\n")
            f.write("Pedro Oliveira\n")
        
        # CSV com cabeçalho
        csv_com_cabecalho = os.path.join(temp_dir, "com_cabecalho.csv")
        with open(csv_com_cabecalho, 'w', encoding='utf-8') as f:
            f.write("Nome\n")
            f.write("João Silva\n")
            f.write("Maria Santos\n")
            f.write("Pedro Oliveira\n")
        
        # Template simples
        template_content = """
        <html>
        <body>
            <h1>Certificado</h1>
            <p>{{ nome }} participou de {{ evento }}</p>
        </body>
        </html>
        """
        
        template_path = os.path.join(temp_dir, "template.html")
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # Criar output directory
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Configurar serviço
        certificate_service = CertificateService(output_dir=output_dir)
        
        # Dados do evento
        event_details = {
            "evento": "Teste de Certificação",
            "data": "25/01/2025",
            "local": "UFSC",
            "carga_horaria": "20"
        }
        
        # Teste 1: CSV sem cabeçalho (has_header=False)
        print("\nTeste 1.1: CSV SEM cabeçalho (has_header=False)")
        result_sem_header = certificate_service.generate_certificates_batch(
            csv_file_path=csv_sem_cabecalho,
            event_details=event_details,
            template_name="template.html",
            has_header=False
        )
        
        print(f"  Certificados gerados: {result_sem_header['success_count']}")
        print(f"  Falhas: {result_sem_header['failed_count']}")
        if result_sem_header['errors']:
            print(f"  Erros: {result_sem_header['errors']}")
        
        expected_participants_sem_header = 3  # João, Maria, Pedro
        if result_sem_header['success_count'] == expected_participants_sem_header:
            print("  ✓ SUCESSO: Todos os participantes processados (sem pular primeira linha)")
        else:
            print(f"  ✗ FALHA: Esperado {expected_participants_sem_header}, obtido {result_sem_header['success_count']}")
        
        # Teste 2: CSV com cabeçalho (has_header=True)
        print("\nTeste 1.2: CSV COM cabeçalho (has_header=True)")
        result_com_header = certificate_service.generate_certificates_batch(
            csv_file_path=csv_com_cabecalho,
            event_details=event_details,
            template_name="template.html",
            has_header=True
        )
        
        print(f"  Certificados gerados: {result_com_header['success_count']}")
        print(f"  Falhas: {result_com_header['failed_count']}")
        if result_com_header['errors']:
            print(f"  Erros: {result_com_header['errors']}")
        
        expected_participants_com_header = 3  # João, Maria, Pedro (sem contar "Nome")
        if result_com_header['success_count'] == expected_participants_com_header:
            print("  ✓ SUCESSO: Cabeçalho removido corretamente")
        else:
            print(f"  ✗ FALHA: Esperado {expected_participants_com_header}, obtido {result_com_header['success_count']}")
        
        # Teste 3: CSV com cabeçalho mas processado incorretamente (has_header=False)
        print("\nTeste 1.3: CSV COM cabeçalho mas has_header=False (deve incluir 'Nome' como participante)")
        result_incorreto = certificate_service.generate_certificates_batch(
            csv_file_path=csv_com_cabecalho,
            event_details=event_details,
            template_name="template.html",
            has_header=False
        )
        
        print(f"  Certificados gerados: {result_incorreto['success_count']}")
        print(f"  Falhas: {result_incorreto['failed_count']}")
        if result_incorreto['errors']:
            print(f"  Erros: {result_incorreto['errors']}")
        
        expected_participants_incorreto = 4  # "Nome", João, Maria, Pedro
        if result_incorreto['success_count'] == expected_participants_incorreto:
            print("  ✓ SUCESSO: Sistema respeitou has_header=False (incluiu 'Nome' como participante)")
        else:
            print(f"  ✗ FALHA: Esperado {expected_participants_incorreto}, obtido {result_incorreto['success_count']}")


def test_offline_sync():
    """Testa o sistema de sincronização offline."""
    print("\n" + "=" * 50)
    print("TESTE 2: Sistema de Sincronização Offline")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Configurar OfflineSyncManager com diretório temporário
        offline_manager = OfflineSyncManager()
        
        # Dados de teste
        cert_data = {
            'codigo_autenticacao': 'TEST123456',
            'nome_participante': 'João Teste',
            'evento': 'Evento de Teste',
            'data_evento': '25/01/2025',
            'local_evento': 'UFSC',
            'carga_horaria': '20',
            'coordenador': 'Prof. Coordenador',
            'diretor': 'Prof. Diretor',
            'data_geracao': datetime.now().isoformat(),
            'url_verificacao': 'https://nepemufsc.com/verificar-certificados',
            'qrcode_base64': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==',
            'template_usado': 'template.html',
            'tema_usado': 'default'
        }
        
        # Teste 1: Armazenamento
        print("\nTeste 2.1: Armazenamento de certificado")
        stored = offline_manager.store_certificate(cert_data)
        if stored:
            print("  ✓ Certificado armazenado com sucesso")
        else:
            print("  ✗ Falha no armazenamento")
        
        # Teste 2: Listagem
        print("\nTeste 2.2: Listagem de certificados")
        pending_certs = offline_manager.get_pending_certificates()
        print(f"  Certificados pendentes: {len(pending_certs)}")
        if len(pending_certs) >= 1:
            print("  ✓ Certificado encontrado na lista")
        else:
            print("  ✗ Certificado não encontrado")
        
        # Teste 3: Estatísticas
        print("\nTeste 2.3: Estatísticas")
        stats = offline_manager.get_sync_statistics()
        print(f"  Total de certificados: {stats.get('total_certificates', 0)}")
        print(f"  Pendentes: {stats.get('pending_sync', 0)}")
        print(f"  Sincronizados: {stats.get('synced', 0)}")
        print(f"  Com falha: {stats.get('sync_failed', 0)}")


def test_zip_exporter():
    """Testa o ZipExporter."""
    print("\n" + "=" * 50)
    print("TESTE 3: ZipExporter")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Criar arquivos de teste
        files_to_zip = []
        for i in range(3):
            file_path = os.path.join(temp_dir, f"certificado_{i+1}.pdf")
            with open(file_path, 'w') as f:
                f.write(f"Conteúdo do certificado {i+1}")
            files_to_zip.append(file_path)
        
        # Teste 1: create_zip_in_memory
        print("\nTeste 3.1: Criação de ZIP em memória")
        zip_exporter = ZipExporter()
        try:
            zip_bytes = zip_exporter.create_zip_in_memory(files_to_zip)
            if zip_bytes and len(zip_bytes) > 0:
                print(f"  ✓ ZIP criado em memória ({len(zip_bytes)} bytes)")
            else:
                print("  ✗ Falha na criação do ZIP em memória")
        except Exception as e:
            print(f"  ✗ Erro na criação do ZIP em memória: {e}")
        
        # Teste 2: create_zip
        print("\nTeste 3.2: Criação de ZIP em arquivo")
        zip_path = os.path.join(temp_dir, "certificados.zip")
        try:
            result = zip_exporter.create_zip(files_to_zip, zip_path)
            if result and os.path.exists(zip_path):
                zip_size = os.path.getsize(zip_path)
                print(f"  ✓ ZIP criado no disco ({zip_size} bytes): {zip_path}")
            else:
                print("  ✗ Falha na criação do ZIP no disco")
        except Exception as e:
            print(f"  ✗ Erro na criação do ZIP no disco: {e}")


def main():
    """Executa todos os testes de validação."""
    print("VALIDAÇÃO FINAL DO SISTEMA NEPEMCERT")
    print("Data:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    
    try:
        test_csv_processing()
        test_offline_sync()
        test_zip_exporter()
        
        print("\n" + "=" * 50)
        print("VALIDAÇÃO CONCLUÍDA")
        print("=" * 50)
        print("✓ Todos os testes executados. Verifique os resultados acima.")
        
    except Exception as e:
        print(f"\n✗ ERRO DURANTE A VALIDAÇÃO: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
