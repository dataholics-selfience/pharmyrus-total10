#!/bin/bash

# Build Script com opções alternativas

set -e

echo "🔨 Pharmyrus WIPO - Build Script"
echo "================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Opções
echo ""
echo "Escolha a estratégia de build:"
echo ""
echo "1) Dockerfile padrão (corrigido)"
echo "2) Dockerfile.playwright (imagem oficial)"
echo "3) Build local + push manual"
echo "4) Deploy direto no Railway (skip build local)"
echo ""
read -p "Opção [1]: " option
option=${option:-1}

case $option in
  1)
    echo -e "${GREEN}📦 Usando Dockerfile padrão${NC}"
    if [ -f "railway.json" ]; then
      sed -i 's/"dockerfilePath": ".*"/"dockerfilePath": "Dockerfile"/' railway.json
    fi
    echo "✅ Configurado para usar Dockerfile"
    ;;
    
  2)
    echo -e "${GREEN}📦 Usando Dockerfile.playwright${NC}"
    if [ -f "railway.json" ]; then
      sed -i 's/"dockerfilePath": ".*"/"dockerfilePath": "Dockerfile.playwright"/' railway.json
    fi
    echo "✅ Configurado para usar Dockerfile.playwright"
    ;;
    
  3)
    echo -e "${GREEN}🔨 Build local${NC}"
    
    # Build
    echo "Building imagem..."
    docker build -t pharmyrus-wipo:latest .
    
    if [ $? -eq 0 ]; then
      echo -e "${GREEN}✅ Build bem-sucedido!${NC}"
      echo ""
      echo "Para testar localmente:"
      echo "  docker run -p 8000:8000 pharmyrus-wipo:latest"
      echo ""
      echo "Para fazer push para Railway:"
      echo "  1. railway login"
      echo "  2. docker tag pharmyrus-wipo:latest registry.railway.app/[seu-app]:latest"
      echo "  3. docker push registry.railway.app/[seu-app]:latest"
    else
      echo -e "${RED}❌ Build falhou!${NC}"
      echo "Tente opção 2 (Dockerfile.playwright)"
      exit 1
    fi
    exit 0
    ;;
    
  4)
    echo -e "${GREEN}🚀 Deploy direto no Railway${NC}"
    ;;
    
  *)
    echo -e "${RED}Opção inválida${NC}"
    exit 1
    ;;
esac

# Verifica Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI não encontrado${NC}"
    echo "Instale: npm install -g @railway/cli"
    exit 1
fi

# Deploy
echo ""
echo -e "${YELLOW}🚀 Iniciando deploy...${NC}"
railway up

if [ $? -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ Deploy completo!${NC}"
  echo ""
  echo "Comandos úteis:"
  echo "  railway logs        # Ver logs"
  echo "  railway domain      # Ver URL"
  echo "  railway variables   # Ver variáveis"
else
  echo ""
  echo -e "${RED}❌ Deploy falhou!${NC}"
  echo ""
  echo "Troubleshooting:"
  echo "  1. Veja logs: railway logs"
  echo "  2. Leia: docs/BUILD_TROUBLESHOOTING.md"
  echo "  3. Tente opção 2: ./build.sh (escolha opção 2)"
fi
