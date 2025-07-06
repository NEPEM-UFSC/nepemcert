#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se o sistema de sincronização offline
está funcionando corretamente sem travamentos de banco.
"""

import sys
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.offline_sync_manager import OfflineSyncManager

def test_concurrent_storage():
    """Testa armazenamento concorrente de certificados."""
    print("🧪 Testando armazenamento concorrente de certificados...")
    
    sync_manager = OfflineSyncManager()
    
    # Dados de teste
    test_certificates = []
    for i in range(10):
        cert_data = {
            'codigo_autenticacao': f'test_cert_{i}_{int(time.time())}',
            'nome_participante': f'Participante Teste {i}',
            'evento': f'Evento de Teste {i}',
            'data_evento': '17/06/2025',
            'local_evento': 'Local de Teste',
            'carga_horaria': '20',
            'coordenador': 'Prof. Teste',
            'diretor': 'Dir. Teste',
            'data_geracao': datetime.now().isoformat(),
            'url_verificacao': 'https://test.com/verificar',
            'qrcode_base64': 'data:image/png;base64,test',
            'template_usado': 'test_template.html',
            'tema_usado': 'test_theme'
        }
        test_certificates.append(cert_data)
    
    # Testar armazenamento concorrente
    success_count = 0
    error_count = 0
    
    def store_certificate(cert_data):
        try:
            result = sync_manager.store_certificate(cert_data)
            return result
        except Exception as e:
            print(f"❌ Erro ao armazenar certificado: {e}")
            return False
    
    # Usar ThreadPoolExecutor para simular concorrência
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(store_certificate, cert) for cert in test_certificates]
        
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    success_count += 1
                    print("✅ Certificado armazenado com sucesso")
                else:
                    error_count += 1
                    print("❌ Falha ao armazenar certificado")
            except Exception as e:
                error_count += 1
                print(f"❌ Exceção durante armazenamento: {e}")
    
    print(f"\n📊 Resultados do teste:")
    print(f"   ✅ Sucessos: {success_count}")
    print(f"   ❌ Erros: {error_count}")
    print(f"   📋 Total: {len(test_certificates)}")
    
    # Verificar se foram armazenados corretamente
    pending_certs = sync_manager.get_pending_certificates()
    test_certs_count = len([c for c in pending_certs if c.nome_participante.startswith('Participante Teste')])
    
    print(f"   💾 Certificados de teste no banco: {test_certs_count}")
    
    # Obter estatísticas
    stats = sync_manager.get_sync_statistics()
    print(f"\n📈 Estatísticas do banco:")
    print(f"   📋 Total de registros: {stats.get('total_records', 0)}")
    print(f"   ⏳ Pendentes: {stats.get('pending_count', 0)}")
    print(f"   ✅ Sincronizados: {stats.get('synced_count', 0)}")
    
    sync_manager.close()
    
    return success_count == len(test_certificates)

def test_database_robustness():
    """Testa robustez do banco contra operações simultâneas."""
    print("\n🛡️ Testando robustez do banco de dados...")
    
    sync_manager = OfflineSyncManager()
    
    # Testar operações mistas simultâneas
    def mixed_operations():
        # Armazenar um certificado
        cert_data = {
            'codigo_autenticacao': f'mixed_test_{int(time.time() * 1000000)}',
            'nome_participante': 'Mixed Test',
            'evento': 'Mixed Event',
            'data_evento': '17/06/2025',
            'local_evento': 'Test',
            'carga_horaria': '10',
            'coordenador': 'Test',
            'diretor': 'Test',
            'data_geracao': datetime.now().isoformat(),
            'url_verificacao': 'https://test.com',
            'qrcode_base64': 'test',
            'template_usado': 'test.html',
            'tema_usado': 'test'
        }
        
        # Armazenar
        store_result = sync_manager.store_certificate(cert_data)
        
        # Consultar pendentes
        pending = sync_manager.get_pending_certificates(limit=5)
        
        # Obter estatísticas
        stats = sync_manager.get_sync_statistics()
        
        return store_result and len(pending) >= 0 and 'total_records' in stats
    
    # Executar várias operações mistas simultaneamente
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(mixed_operations) for _ in range(8)]
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                if result:
                    print("✅ Operação mista bem-sucedida")
                else:
                    print("❌ Falha em operação mista")
            except Exception as e:
                print(f"❌ Exceção em operação mista: {e}")
                results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 Taxa de sucesso das operações mistas: {success_rate:.1f}%")
    
    sync_manager.close()
    
    return success_rate >= 80  # 80% de sucesso é aceitável

def main():
    """Função principal de teste."""
    print("🚀 Iniciando testes do sistema de sincronização offline")
    print("=" * 60)
    
    try:
        # Teste 1: Armazenamento concorrente
        test1_result = test_concurrent_storage()
        
        # Teste 2: Robustez do banco
        test2_result = test_database_robustness()
        
        print("\n" + "=" * 60)
        print("📋 Resumo dos testes:")
        print(f"   🧪 Armazenamento concorrente: {'✅ PASSOU' if test1_result else '❌ FALHOU'}")
        print(f"   🛡️ Robustez do banco: {'✅ PASSOU' if test2_result else '❌ FALHOU'}")
        
        if test1_result and test2_result:
            print("\n🎉 Todos os testes passaram! O sistema está funcionando corretamente.")
            return True
        else:
            print("\n⚠️ Alguns testes falharam. Verifique os logs acima.")
            return False
            
    except Exception as e:
        print(f"\n💥 Erro durante execução dos testes: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
