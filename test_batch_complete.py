#!/usr/bin/env python3
"""
Script completo de teste do sistema de batch v3.1
Testa todos os endpoints e funcionalidades
"""

import requests
import time
import json
from typing import Dict, List

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

# URL base da API (Railway ou local)
BASE_URL = "https://pharmyrus-total10-production.up.railway.app"
# BASE_URL = "http://localhost:8000"  # Use para teste local

# Moléculas para teste (3 rápido, 5 médio, 10 completo)
TEST_MOLECULES_FAST = ["darolutamide", "olaparib", "venetoclax"]
TEST_MOLECULES_MEDIUM = ["darolutamide", "olaparib", "venetoclax", "axitinib", "niraparib"]
TEST_MOLECULES_FULL = [
    "darolutamide", "olaparib", "venetoclax", "axitinib", "niraparib",
    "tivozanib", "ixazomib", "sonidegib", "trastuzumab", "vinseltinib"
]

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_section(title: str):
    """Imprime seção formatada"""
    print("\n" + "-"*80)
    print(f"  {title}")
    print("-"*80)

def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"✅ {message}")

def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"❌ {message}")

def print_info(message: str):
    """Imprime mensagem informativa"""
    print(f"ℹ️  {message}")

def format_time(seconds: float) -> str:
    """Formata tempo em formato legível"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"

# ============================================================================
# TESTES DE API
# ============================================================================

def test_health_check():
    """Testa endpoint de health check"""
    print_section("1. Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API online - Version: {data.get('version', 'unknown')}")
            print_info(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"API retornou status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro ao conectar: {e}")
        return False

def test_single_search(molecule: str = "darolutamide"):
    """Testa busca única de molécula (v3.0 - backward compatibility)"""
    print_section(f"2. Busca Individual - {molecule}")
    
    try:
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/v1/search/{molecule}",
            params={"limit": 5},
            timeout=120
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            wo_count = len(data.get('wo_patents', []))
            br_count = sum(len(wo.get('br_patents', [])) for wo in data.get('wo_patents', []))
            
            print_success(f"Busca individual completada em {format_time(elapsed)}")
            print_info(f"WO patents: {wo_count}, BR patents: {br_count}")
            return True
        else:
            print_error(f"Erro: status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro na busca: {e}")
        return False

def create_batch(molecules: List[str], country_filter: str = None, limit: int = 10) -> str:
    """Cria um batch job"""
    print_section(f"3. Criando Batch - {len(molecules)} moléculas")
    
    try:
        payload = {
            "molecules": molecules,
            "limit": limit
        }
        
        if country_filter:
            payload["country_filter"] = country_filter
        
        response = requests.post(
            f"{BASE_URL}/api/v1/batch/search",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            batch_id = data['batch_id']
            estimated_time = data.get('estimated_time_seconds', 0)
            
            print_success(f"Batch criado: {batch_id}")
            print_info(f"Total moléculas: {data['total_molecules']}")
            print_info(f"Tempo estimado: {format_time(estimated_time)}")
            
            return batch_id
        else:
            print_error(f"Erro ao criar batch: {response.status_code}")
            print_error(f"Resposta: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao criar batch: {e}")
        return None

def monitor_batch(batch_id: str, poll_interval: int = 5, max_wait: int = 600) -> bool:
    """Monitora progresso do batch até completar"""
    print_section(f"4. Monitorando Batch - {batch_id}")
    
    start_time = time.time()
    last_progress = -1
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            # Timeout check
            if elapsed > max_wait:
                print_error(f"Timeout após {format_time(elapsed)}")
                return False
            
            # Check status
            response = requests.get(
                f"{BASE_URL}/api/v1/batch/status/{batch_id}",
                timeout=10
            )
            
            if response.status_code != 200:
                print_error(f"Erro ao consultar status: {response.status_code}")
                return False
            
            data = response.json()
            status = data['status']
            progress = data['progress_percentage']
            completed = data['completed_count']
            failed = data['failed_count']
            total = data['total_molecules']
            eta = data.get('estimated_time_remaining_seconds', 0)
            
            # Print progress if changed
            if progress != last_progress:
                print_info(
                    f"Progresso: {progress:.1f}% | "
                    f"Completos: {completed}/{total} | "
                    f"Falhas: {failed} | "
                    f"ETA: {format_time(eta)} | "
                    f"Status: {status}"
                )
                last_progress = progress
            
            # Check if completed
            if status in ['completed', 'failed']:
                total_time = time.time() - start_time
                print_success(f"Batch {status} em {format_time(total_time)}")
                print_info(f"Sucessos: {completed}, Falhas: {failed}")
                return status == 'completed'
            
            # Wait before next poll
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print_error("Monitoramento interrompido pelo usuário")
        return False
    except Exception as e:
        print_error(f"Erro no monitoramento: {e}")
        return False

def get_batch_results(batch_id: str) -> Dict:
    """Obtém resultados do batch"""
    print_section(f"5. Obtendo Resultados - {batch_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/batch/results/{batch_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            results_count = len(data.get('results', {}))
            errors_count = len(data.get('errors', {}))
            
            print_success(f"Resultados obtidos")
            print_info(f"Sucessos: {results_count}, Erros: {errors_count}")
            
            # Mostrar resumo de cada molécula
            for mol, result in data.get('results', {}).items():
                wo_count = len(result.get('wo_patents', []))
                br_count = sum(len(wo.get('br_patents', [])) for wo in result.get('wo_patents', []))
                print_info(f"  • {mol}: {wo_count} WO, {br_count} BR")
            
            return data
        else:
            print_error(f"Erro ao obter resultados: {response.status_code}")
            return None
            
    except Exception as e:
        print_error(f"Erro ao obter resultados: {e}")
        return None

def test_batch_list():
    """Testa listagem de batches"""
    print_section("6. Listando Batches")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/batch/list", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = data['total_batches']
            
            print_success(f"Listagem obtida: {total} batches")
            
            # Mostrar primeiros 5
            for batch in data.get('batches', [])[:5]:
                batch_id = batch['batch_id']
                status = batch['status']
                progress = batch['progress_percentage']
                completed = batch['completed_count']
                total_mols = batch['total_molecules']
                
                print_info(
                    f"  • {batch_id[:20]}... | "
                    f"Status: {status} | "
                    f"Progresso: {progress:.0f}% ({completed}/{total_mols})"
                )
            
            return True
        else:
            print_error(f"Erro ao listar: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro ao listar batches: {e}")
        return False

def test_batch_cancel():
    """Testa cancelamento de batch"""
    print_section("7. Testando Cancelamento")
    
    try:
        # Criar batch de teste
        batch_id = create_batch(["aspirin"], limit=5)
        
        if not batch_id:
            print_error("Falha ao criar batch para teste de cancelamento")
            return False
        
        # Aguardar um pouco
        time.sleep(2)
        
        # Cancelar
        response = requests.delete(f"{BASE_URL}/api/v1/batch/{batch_id}", timeout=10)
        
        if response.status_code == 200:
            print_success("Batch cancelado com sucesso")
            return True
        else:
            print_error(f"Erro ao cancelar: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro no teste de cancelamento: {e}")
        return False

def test_batch_cleanup():
    """Testa limpeza de batches antigos"""
    print_section("8. Testando Limpeza")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/batch/cleanup",
            params={"max_age_hours": 24},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            deleted = data['deleted_count']
            print_success(f"Limpeza executada: {deleted} batches removidos")
            return True
        else:
            print_error(f"Erro na limpeza: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Erro na limpeza: {e}")
        return False

# ============================================================================
# WORKFLOW COMPLETO
# ============================================================================

def run_complete_workflow(molecules: List[str], test_name: str):
    """Executa workflow completo de batch"""
    print_header(f"WORKFLOW COMPLETO: {test_name}")
    
    # 1. Criar batch
    batch_id = create_batch(molecules, country_filter="BR_US", limit=10)
    
    if not batch_id:
        print_error("Falha ao criar batch. Abortando workflow.")
        return False
    
    # 2. Monitorar progresso
    success = monitor_batch(batch_id, poll_interval=5, max_wait=600)
    
    if not success:
        print_error("Batch não completou com sucesso")
        return False
    
    # 3. Obter resultados
    results = get_batch_results(batch_id)
    
    if not results:
        print_error("Falha ao obter resultados")
        return False
    
    print_success(f"Workflow {test_name} completado com sucesso!")
    return True

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def main():
    """Menu principal de testes"""
    print_header("PHARMYRUS BATCH v3.1 - TESTES COMPLETOS")
    
    # Health check primeiro
    if not test_health_check():
        print_error("API não está disponível. Verifique se está rodando.")
        return
    
    # Menu de opções
    print("\n📋 OPÇÕES DE TESTE:")
    print("  1 - Health Check")
    print("  2 - Busca Individual (backward compatibility)")
    print("  3 - Batch Rápido (3 moléculas, ~1-2 min)")
    print("  4 - Batch Médio (5 moléculas, ~2-3 min)")
    print("  5 - Batch Completo (10 moléculas, ~3-5 min)")
    print("  6 - Listar Batches")
    print("  7 - Testar Cancelamento")
    print("  8 - Testar Limpeza")
    print("  9 - TODOS OS TESTES (sequencial)")
    print("  0 - Sair")
    
    while True:
        choice = input("\n👉 Escolha uma opção (0-9): ").strip()
        
        if choice == "0":
            print_info("Encerrando testes. Até logo!")
            break
            
        elif choice == "1":
            test_health_check()
            
        elif choice == "2":
            test_single_search()
            
        elif choice == "3":
            run_complete_workflow(TEST_MOLECULES_FAST, "RÁPIDO - 3 moléculas")
            
        elif choice == "4":
            run_complete_workflow(TEST_MOLECULES_MEDIUM, "MÉDIO - 5 moléculas")
            
        elif choice == "5":
            run_complete_workflow(TEST_MOLECULES_FULL, "COMPLETO - 10 moléculas")
            
        elif choice == "6":
            test_batch_list()
            
        elif choice == "7":
            test_batch_cancel()
            
        elif choice == "8":
            test_batch_cleanup()
            
        elif choice == "9":
            print_header("EXECUTANDO TODOS OS TESTES")
            test_health_check()
            test_single_search()
            run_complete_workflow(TEST_MOLECULES_FAST, "RÁPIDO")
            test_batch_list()
            test_batch_cancel()
            test_batch_cleanup()
            print_success("TODOS OS TESTES COMPLETADOS!")
            
        else:
            print_error("Opção inválida. Escolha 0-9.")

if __name__ == "__main__":
    main()
