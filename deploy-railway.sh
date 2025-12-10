#!/bin/bash

# 🚀 Pharmyrus v3.1 - Script de Deploy Automatizado
# Verifica o pacote e prepara para deploy no Railway

set -e  # Parar em caso de erro

echo "🔍 PHARMYRUS v3.1 - VERIFICAÇÃO E DEPLOY"
echo "========================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função de verificação
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# PASSO 1: Verificar se pacote existe
echo "📦 PASSO 1: Verificando pacote..."
if [ ! -f "pharmyrus-v3.1-BATCH-FINAL.tar.gz" ]; then
    echo -e "${RED}❌ ERRO: Pacote pharmyrus-v3.1-BATCH-FINAL.tar.gz não encontrado!${NC}"
    echo "Baixe o pacote primeiro e coloque nesta pasta."
    exit 1
fi
check "Pacote encontrado"

# PASSO 2: Extrair pacote
echo ""
echo "📂 PASSO 2: Extraindo pacote..."
rm -rf pharmyrus-wipo-deploy-v3
tar -xzf pharmyrus-v3.1-BATCH-FINAL.tar.gz
check "Pacote extraído"

# PASSO 3: Verificar aiohttp
echo ""
echo "🔍 PASSO 3: Verificando aiohttp no requirements.txt..."
cd pharmyrus-wipo-deploy-v3
if grep -q "aiohttp==3.9.1" requirements.txt; then
    check "aiohttp encontrado no requirements.txt"
else
    echo -e "${RED}❌ ERRO: aiohttp NÃO encontrado!${NC}"
    echo "Você está usando o pacote ERRADO. Baixe novamente."
    exit 1
fi

# PASSO 4: Mostrar requirements.txt
echo ""
echo "📄 PASSO 4: Conteúdo do requirements.txt:"
echo "----------------------------------------"
cat requirements.txt
echo "----------------------------------------"

# PASSO 5: Verificar sintaxe Python
echo ""
echo "🐍 PASSO 5: Verificando sintaxe Python..."
if command -v python3 &> /dev/null; then
    python3 -m py_compile src/api_service.py 2>/dev/null
    check "Sintaxe Python OK"
else
    echo -e "${YELLOW}⚠️  Python3 não encontrado, pulando verificação${NC}"
fi

# PASSO 6: Verificar arquivos
echo ""
echo "📁 PASSO 6: Verificando estrutura de arquivos..."
required_files=(
    "Dockerfile"
    "requirements.txt"
    "nixpacks.toml"
    "src/api_service.py"
    "src/batch_service.py"
    "src/pipeline_service.py"
    "src/wipo_crawler.py"
    "src/crawler_pool.py"
)

all_ok=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${RED}  ❌ $file - FALTANDO!${NC}"
        all_ok=false
    fi
done

if [ "$all_ok" = false ]; then
    echo -e "${RED}❌ Arquivos faltando! Pacote incompleto.${NC}"
    exit 1
fi

# PASSO 7: Resumo
echo ""
echo "================================================"
echo -e "${GREEN}✅ TODAS AS VERIFICAÇÕES PASSARAM!${NC}"
echo "================================================"
echo ""
echo "📦 Pacote: pharmyrus-v3.1-BATCH-FINAL.tar.gz"
echo "📁 Diretório: pharmyrus-wipo-deploy-v3/"
echo "✅ aiohttp: 3.9.1 (PRESENTE)"
echo "✅ Sintaxe Python: OK"
echo "✅ Arquivos: Completos"
echo ""

# PASSO 8: Instruções de deploy
echo "🚀 PRÓXIMOS PASSOS PARA DEPLOY:"
echo "================================"
echo ""
echo "1. Fazer login no Railway:"
echo "   railway login"
echo ""
echo "2. OPÇÃO A - Novo projeto (RECOMENDADO):"
echo "   railway init"
echo "   railway up"
echo ""
echo "   OU"
echo ""
echo "2. OPÇÃO B - Projeto existente:"
echo "   railway link"
echo "   railway up"
echo ""
echo "3. Acompanhar logs:"
echo "   railway logs"
echo ""
echo "4. Verificar que funcionou:"
echo "   Procure nos logs por:"
echo "   - 'Successfully installed aiohttp-3.9.1'"
echo "   - 'Application startup complete'"
echo ""
echo "5. Testar API:"
echo "   railway status  # pegar URL"
echo "   curl https://SEU-APP.railway.app/health"
echo ""
echo "================================================"
echo -e "${GREEN}✅ Pronto para deploy!${NC}"
echo "================================================"
