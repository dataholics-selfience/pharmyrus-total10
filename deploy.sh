#!/bin/bash

# Pharmyrus WIPO Crawler - Railway Deploy Script

set -e

echo "🚀 Pharmyrus WIPO Crawler - Railway Deploy"
echo "=========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Verifica Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI não encontrado${NC}"
    echo "Instale com: npm install -g @railway/cli"
    exit 1
fi

echo -e "${GREEN}✅ Railway CLI encontrado${NC}"

# Verifica Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git não encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Git encontrado${NC}"

# Inicializa Git se necessário
if [ ! -d ".git" ]; then
    echo "📦 Inicializando Git..."
    git init
    git add .
    git commit -m "Initial commit - Pharmyrus WIPO Crawler"
fi

# Login Railway
echo "🔐 Verificando login Railway..."
railway whoami || railway login

# Cria/seleciona projeto
echo "📦 Configurando projeto..."
if [ ! -f "railway.toml" ]; then
    railway init
else
    echo "Usando projeto existente"
fi

# Variáveis de ambiente
echo "⚙️ Configurando variáveis..."
railway variables set PORT=8000
railway variables set CACHE_TTL=3600
railway variables set WIPO_POOL_SIZE=3
railway variables set LOG_LEVEL=INFO

# Deploy
echo "🚀 Fazendo deploy..."
railway up

# Aguarda deployment
echo "⏳ Aguardando deployment..."
sleep 10

# Pega URL
echo ""
echo "🌐 Obtendo URL..."
URL=$(railway domain 2>/dev/null || echo "")

if [ -n "$URL" ]; then
    echo -e "${GREEN}✅ Deploy completo!${NC}"
    echo ""
    echo "📍 URL: https://$URL"
    echo ""
    echo "🧪 Teste com:"
    echo "  curl https://$URL/health"
    echo ""
    echo "📚 Docs: https://$URL/docs"
else
    echo -e "${YELLOW}⚠️ Use 'railway domain' para obter URL${NC}"
fi

echo ""
echo "🎉 Deploy finalizado!"
echo ""
echo "📊 Para ver logs:"
echo "  railway logs"
echo ""
echo "⚙️ Para configurar variáveis:"
echo "  railway variables set KEY=VALUE"
