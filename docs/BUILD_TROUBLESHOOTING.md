# 🔧 Build Troubleshooting Guide

## Erro: playwright install-deps falha

### Problema
```
E: Package 'ttf-unifont' has no installation candidate
E: Package 'ttf-ubuntu-font-family' has no installation candidate
```

### Causa
O Playwright tenta instalar fontes que não estão disponíveis em todas as distribuições Linux.

### Soluções

#### ✅ Solução 1: Use o Dockerfile corrigido (Recomendado)

O novo `Dockerfile` já está corrigido e usa:
- Base: `python:3.11-bullseye` (mais estável)
- Instala dependências manualmente (sem `playwright install-deps`)
- Inclui apenas fontes essenciais

```bash
# Use o Dockerfile padrão (já corrigido)
railway up
```

#### ✅ Solução 2: Use a imagem oficial do Playwright

Use o `Dockerfile.playwright`:

```bash
# No railway.json, altere:
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.playwright"
  }
}

# Depois:
railway up
```

#### ✅ Solução 3: Build local e push da imagem

Se os erros persistirem, faça build local:

```bash
# Build local
docker build -t pharmyrus-wipo .

# Tag para Railway
docker tag pharmyrus-wipo registry.railway.app/pharmyrus-wipo:latest

# Push
docker push registry.railway.app/pharmyrus-wipo:latest
```

---

## Erro: Timeout durante build

### Problema
```
Build timeout after 30 minutes
```

### Soluções

#### 1. Otimize o Dockerfile
```dockerfile
# Use cache de layers eficientemente
RUN apt-get update && apt-get install -y ... \
    && rm -rf /var/lib/apt/lists/*  # Limpa cache
```

#### 2. Use .dockerignore
```
__pycache__/
*.pyc
.git/
.venv/
*.log
```

#### 3. Pré-instale Playwright
```dockerfile
# Instale Playwright antes de copiar código
COPY requirements.txt .
RUN pip install playwright
RUN playwright install chromium
COPY . .
```

---

## Erro: Module not found

### Problema
```
ModuleNotFoundError: No module named 'src'
```

### Solução

Verifique estrutura do projeto:
```
/app/
├── src/
│   ├── __init__.py  ← Importante!
│   ├── wipo_crawler.py
│   └── api_service.py
```

Execute como módulo:
```bash
python -m src.api_service
# OU
uvicorn src.api_service:app
```

---

## Erro: Playwright browser not found

### Problema
```
Error: Executable doesn't exist at /root/.cache/ms-playwright/chromium-1097/chrome-linux/chrome
```

### Soluções

#### 1. Defina PLAYWRIGHT_BROWSERS_PATH
```dockerfile
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
```

#### 2. Instale como root, execute como user
```dockerfile
# Instale como root
RUN playwright install chromium

# Depois mude para user
USER appuser
```

#### 3. Permissões corretas
```dockerfile
RUN mkdir -p /ms-playwright && \
    chown -R appuser:appuser /ms-playwright
```

---

## Erro: Memory limit exceeded

### Problema
```
OOMKilled: Out of memory
```

### Soluções

#### 1. Aumente memória no Railway
```bash
railway settings
# Memory: 1GB → 2GB
```

#### 2. Reduza pool size
```bash
railway variables set WIPO_POOL_SIZE=2
```

#### 3. Use workers=1
```dockerfile
CMD uvicorn src.api_service:app --workers 1
```

---

## Erro: Port binding

### Problema
```
Address already in use: 0.0.0.0:8000
```

### Solução

Use variável PORT do Railway:
```python
import os
port = int(os.getenv('PORT', '8000'))

# FastAPI
uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## ✅ Checklist de Build Bem-Sucedido

- [ ] Dockerfile usa base estável (bullseye/jammy)
- [ ] Dependências instaladas em camada única
- [ ] Cache APT limpo (`rm -rf /var/lib/apt/lists/*`)
- [ ] Playwright instalado sem `install-deps`
- [ ] Non-root user configurado
- [ ] PORT como variável de ambiente
- [ ] .dockerignore presente
- [ ] Estrutura src/__init__.py existe

---

## 🚀 Comando de Deploy Recomendado

```bash
# 1. Verifique estrutura
ls -la src/

# 2. Teste build local (opcional)
docker build -t test-wipo .

# 3. Deploy
railway up

# 4. Monitore logs
railway logs
```

---

## 📊 Logs Úteis

### Build bem-sucedido
```
✓ Playwright Chromium downloaded
✓ Application copied
✓ User created
✓ Build complete
```

### Build com erro
```
✗ E: Package has no installation candidate
✗ exit code: 1
```

---

## 🆘 Ainda com problemas?

### 1. Use a imagem oficial do Playwright
```bash
# Edite railway.json
{
  "build": {
    "dockerfilePath": "Dockerfile.playwright"
  }
}
```

### 2. Contate suporte
- Railway Discord: https://discord.gg/railway
- GitHub Issues: seu-repo/issues

### 3. Deploy manual
```bash
# Build local + push para registry
docker build -t seu-app .
docker push registry.railway.app/seu-app
```

---

## 📚 Recursos

- [Playwright Docker](https://playwright.dev/python/docs/docker)
- [Railway Docs](https://docs.railway.app/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Atualizado: Dezembro 2024**
