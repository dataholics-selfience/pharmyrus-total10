#!/bin/bash

# ============================================================================
# Script de Teste Rápido - Pharmyrus Batch v3.1
# Testa todos os endpoints batch via curl
# ============================================================================

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuração
BASE_URL="${PHARMYRUS_URL:-https://pharmyrus-total10-production.up.railway.app}"

# Funções auxiliares
print_header() {
    echo -e "\n${BLUE}================================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================================================${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}--------------------------------------------------------------------------------${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}--------------------------------------------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# ============================================================================
# TESTES
# ============================================================================

test_health() {
    print_section "1. Health Check"
    
    response=$(curl -s "$BASE_URL/")
    
    if [ $? -eq 0 ]; then
        version=$(echo "$response" | jq -r '.version // "unknown"')
        status=$(echo "$response" | jq -r '.status // "unknown"')
        
        print_success "API online"
        print_info "Version: $version"
        print_info "Status: $status"
        return 0
    else
        print_error "Falha ao conectar na API"
        return 1
    fi
}

test_create_batch() {
    print_section "2. Criar Batch (3 moléculas)"
    
    payload='{
        "molecules": ["darolutamide", "olaparib", "venetoclax"],
        "country_filter": "BR_US",
        "limit": 10
    }'
    
    response=$(curl -s -X POST "$BASE_URL/api/v1/batch/search" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    if [ $? -eq 0 ]; then
        batch_id=$(echo "$response" | jq -r '.batch_id // empty')
        
        if [ -n "$batch_id" ]; then
            print_success "Batch criado: $batch_id"
            print_info "Monitorando progresso..."
            
            # Salvar batch_id para próximos testes
            echo "$batch_id" > /tmp/batch_id.txt
            
            return 0
        else
            print_error "Resposta inválida"
            echo "$response" | jq '.'
            return 1
        fi
    else
        print_error "Falha ao criar batch"
        return 1
    fi
}

test_monitor_batch() {
    print_section "3. Monitorar Batch"
    
    if [ ! -f /tmp/batch_id.txt ]; then
        print_error "Nenhum batch_id encontrado. Execute test_create_batch primeiro."
        return 1
    fi
    
    batch_id=$(cat /tmp/batch_id.txt)
    print_info "Monitorando batch: $batch_id"
    
    max_iterations=60  # 5 minutos (5 segundos por iteração)
    iteration=0
    
    while [ $iteration -lt $max_iterations ]; do
        response=$(curl -s "$BASE_URL/api/v1/batch/status/$batch_id")
        
        status=$(echo "$response" | jq -r '.status // "unknown"')
        progress=$(echo "$response" | jq -r '.progress_percentage // 0')
        completed=$(echo "$response" | jq -r '.completed_count // 0')
        total=$(echo "$response" | jq -r '.total_molecules // 0')
        eta=$(echo "$response" | jq -r '.estimated_time_remaining_seconds // 0')
        
        printf "\r  Progresso: %.1f%% | Completos: %d/%d | ETA: %.0fs | Status: %s   " \
            "$progress" "$completed" "$total" "$eta" "$status"
        
        # Verificar se completou
        if [ "$status" = "completed" ] || [ "$status" = "failed" ]; then
            echo ""
            if [ "$status" = "completed" ]; then
                print_success "Batch completado!"
                return 0
            else
                print_error "Batch falhou"
                return 1
            fi
        fi
        
        sleep 5
        ((iteration++))
    done
    
    echo ""
    print_error "Timeout aguardando batch completar"
    return 1
}

test_get_results() {
    print_section "4. Obter Resultados"
    
    if [ ! -f /tmp/batch_id.txt ]; then
        print_error "Nenhum batch_id encontrado."
        return 1
    fi
    
    batch_id=$(cat /tmp/batch_id.txt)
    
    response=$(curl -s "$BASE_URL/api/v1/batch/results/$batch_id")
    
    if [ $? -eq 0 ]; then
        results_count=$(echo "$response" | jq '.results | length')
        errors_count=$(echo "$response" | jq '.errors | length')
        
        print_success "Resultados obtidos"
        print_info "Sucessos: $results_count"
        print_info "Erros: $errors_count"
        
        # Mostrar resumo de cada molécula
        echo "$response" | jq -r '.results | to_entries[] | "  • \(.key): \(.value.wo_patents | length) WO patents"'
        
        return 0
    else
        print_error "Falha ao obter resultados"
        return 1
    fi
}

test_list_batches() {
    print_section "5. Listar Batches"
    
    response=$(curl -s "$BASE_URL/api/v1/batch/list")
    
    if [ $? -eq 0 ]; then
        total=$(echo "$response" | jq -r '.total_batches // 0')
        
        print_success "Total de batches: $total"
        
        # Mostrar primeiros 5
        echo "$response" | jq -r '.batches[:5][] | "  • \(.batch_id[:20])... | Status: \(.status) | Progresso: \(.progress_percentage)%"'
        
        return 0
    else
        print_error "Falha ao listar batches"
        return 1
    fi
}

test_cleanup() {
    print_section "6. Limpeza de Batches Antigos"
    
    response=$(curl -s -X POST "$BASE_URL/api/v1/batch/cleanup?max_age_hours=24")
    
    if [ $? -eq 0 ]; then
        deleted=$(echo "$response" | jq -r '.deleted_count // 0')
        
        print_success "Limpeza executada"
        print_info "Batches removidos: $deleted"
        
        return 0
    else
        print_error "Falha na limpeza"
        return 1
    fi
}

# ============================================================================
# WORKFLOW COMPLETO
# ============================================================================

run_full_workflow() {
    print_header "WORKFLOW COMPLETO - Batch v3.1"
    
    # 1. Health check
    test_health || exit 1
    
    # 2. Criar batch
    test_create_batch || exit 1
    
    # 3. Monitorar até completar
    test_monitor_batch || exit 1
    
    # 4. Obter resultados
    test_get_results || exit 1
    
    # 5. Listar batches
    test_list_batches || exit 1
    
    # 6. Limpeza
    test_cleanup || exit 1
    
    print_header "TODOS OS TESTES COMPLETADOS COM SUCESSO!"
}

# ============================================================================
# MENU
# ============================================================================

show_menu() {
    echo ""
    echo "📋 PHARMYRUS BATCH v3.1 - TESTES"
    echo ""
    echo "  1 - Health Check"
    echo "  2 - Criar Batch"
    echo "  3 - Monitorar Batch Atual"
    echo "  4 - Obter Resultados"
    echo "  5 - Listar Batches"
    echo "  6 - Limpeza"
    echo "  7 - Workflow Completo (todos os testes)"
    echo "  0 - Sair"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    print_header "PHARMYRUS BATCH v3.1 - TESTE RÁPIDO"
    print_info "Base URL: $BASE_URL"
    
    # Se argumento --auto, executa workflow completo
    if [ "$1" = "--auto" ] || [ "$1" = "-a" ]; then
        run_full_workflow
        exit 0
    fi
    
    # Menu interativo
    while true; do
        show_menu
        read -p "👉 Escolha uma opção (0-7): " choice
        
        case $choice in
            1) test_health ;;
            2) test_create_batch ;;
            3) test_monitor_batch ;;
            4) test_get_results ;;
            5) test_list_batches ;;
            6) test_cleanup ;;
            7) run_full_workflow ;;
            0) 
                print_info "Encerrando. Até logo!"
                exit 0
                ;;
            *) 
                print_error "Opção inválida. Escolha 0-7."
                ;;
        esac
    done
}

# Executar
main "$@"
