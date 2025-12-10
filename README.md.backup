# 🔬 Pharmyrus WIPO Crawler

> Solução production-ready para extração robusta de patentes WIPO com pooling e cache inteligente

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Railway](https://img.shields.io/badge/Railway-Ready-green.svg)](https://railway.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal.svg)](https://fastapi.tiangolo.com/)

## ✨ Características

- 🎯 **Extração Completa** - Todos os campos importantes da patente
- 🏊 **Pooling Inteligente** - Múltiplos crawlers em paralelo
- 💾 **Cache Otimizado** - TTL configurável para performance
- 🔄 **Retry Robusto** - Até 5 tentativas com backoff exponencial
- 🛡️ **Stealth Mode** - Anti-detecção de bot
- 🚀 **Railway Ready** - Deploy em 1 click

## 🚀 Deploy Rápido (Railway)

### 1️⃣ Clone o repositório

```bash
git clone <your-repo>
cd pharmyrus-wipo-deploy
```

### 2️⃣ Deploy no Railway

```bash
# Instale Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### 3️⃣ Configure variáveis (opcional)

```bash
railway variables set PORT=8000
railway variables set CACHE_TTL=3600
railway variables set WIPO_POOL_SIZE=3
```

## 📦 Instalação Local

```bash
# Clone
git clone <your-repo>
cd pharmyrus-wipo-deploy

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Dependências
pip install -r requirements.txt
playwright install chromium

# Execute
python -m src.api_service
```

## 🔌 API Endpoints

### Health Check

```bash
GET /health
```

### Buscar Patente Única

```bash
POST /api/wipo/patent

{
  "wo_number": "WO2018162793",
  "use_cache": true
}
```

### Buscar Lote (com Pooling)

```bash
POST /api/wipo/patents/batch

{
  "wo_numbers": ["WO2018162793", "WO2016168716"],
  "use_cache": true,
  "use_pool": true,
  "pool_size": 3
}
```

### Limpar Cache

```bash
DELETE /api/cache/clear?wo_number=WO2018162793
```

## 🎯 Uso com n8n

### 1. Configure variável de ambiente:

```
WIPO_API_URL=https://seu-app.up.railway.app
```

### 2. Use HTTP Request node:

```json
{
  "method": "POST",
  "url": "{{ $env.WIPO_API_URL }}/api/wipo/patents/batch",
  "body": {
    "wo_numbers": ["{{ $json.wo_numbers }}"],
    "use_pool": true,
    "pool_size": 3
  }
}
```

## 📊 Performance

| Métrica | Valor |
|---------|-------|
| **Taxa de Sucesso** | > 95% |
| **Tempo/Patente (única)** | 10-30s |
| **Tempo/Patente (pool)** | 8-15s |
| **Cache Hit** | < 1s |

## 🏗️ Arquitetura

```
┌─────────────────┐
│   n8n Workflow  │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│  FastAPI Service│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│ Cache │ │Pool (3x) │
└───────┘ └─────┬────┘
                │
         ┌──────┼──────┐
         ▼      ▼      ▼
      [C1]   [C2]   [C3]
         │      │      │
         └──────┴──────┘
                │
                ▼
         WIPO Patentscope
```

## 🛠️ Variáveis de Ambiente

```bash
PORT=8000                 # Porta do serviço
CACHE_TTL=3600           # TTL do cache (segundos)
WIPO_MAX_RETRIES=5       # Máximo de tentativas
WIPO_TIMEOUT=60000       # Timeout (ms)
WIPO_POOL_SIZE=3         # Tamanho do pool
LOG_LEVEL=INFO           # Nível de log
```

## 📚 Estrutura do Projeto

```
pharmyrus-wipo-deploy/
├── src/
│   ├── __init__.py
│   ├── wipo_crawler.py      # Core crawler
│   ├── crawler_pool.py      # Pool manager
│   └── api_service.py       # FastAPI service
├── tests/
│   └── test_crawler.py      # Testes
├── docs/
│   ├── README.md           # Este arquivo
│   └── API.md              # Documentação da API
├── config/
│   └── logging.yaml        # Config de logging
├── Dockerfile              # Container
├── railway.json            # Config Railway
├── requirements.txt        # Dependências
├── .env.example           # Variáveis exemplo
└── .gitignore
```

## 🧪 Testes

```bash
# Execute testes
python -m pytest tests/

# Com coverage
python -m pytest --cov=src tests/
```

## 🐛 Troubleshooting

### ⚠️ Erro de Build: playwright install-deps

**Problema:** `E: Package 'ttf-unifont' has no installation candidate`

**Solução 1 (Recomendada):** Use o Dockerfile corrigido
```bash
# Já está corrigido! Apenas faça:
railway up
```

**Solução 2:** Use Dockerfile com imagem oficial Playwright
```bash
# Edite railway.json:
{
  "build": {
    "dockerfilePath": "Dockerfile.playwright"
  }
}

# Deploy:
railway up
```

**Solução 3:** Build local
```bash
./build.sh  # Escolha opção 2
```

📚 **Guia completo:** Veja `docs/BUILD_TROUBLESHOOTING.md`

---

### Timeout

```bash
# Aumente o timeout
railway variables set WIPO_TIMEOUT=90000
```

### Cache com dados antigos

```bash
# Limpe o cache
curl -X DELETE "https://seu-app.railway.app/api/cache/clear"
```

### Pool muito agressivo

```bash
# Reduza o pool size
railway variables set WIPO_POOL_SIZE=2
```

## 📄 Licença

MIT License - Pharmyrus Team

## 🆘 Suporte

- 📚 Docs: `/docs` endpoint
- 🐛 Issues: GitHub Issues
- 💬 Chat: contato@pharmyrus.com

---

**Desenvolvido para Pharmyrus Patent Intelligence Platform**

*Versão 1.0.0 - Dezembro 2024*
