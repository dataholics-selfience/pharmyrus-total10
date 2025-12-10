# 🚀 Quick Start Guide

## Opção 1: Deploy Railway (2 minutos)

```bash
# 1. Clone o repositório
git clone <your-repo>
cd pharmyrus-wipo-deploy

# 2. Execute o deploy
chmod +x deploy.sh
./deploy.sh
```

Pronto! Seu serviço estará rodando em `https://seu-app.up.railway.app`

---

## Opção 2: Teste Local (5 minutos)

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Execute
python -m src.api_service

# 3. Teste
curl http://localhost:8000/health
```

---

## Opção 3: Docker (3 minutos)

```bash
# Build
docker build -t pharmyrus-wipo .

# Run
docker run -p 8000:8000 pharmyrus-wipo

# Teste
curl http://localhost:8000/health
```

---

## Primeiro Teste

```bash
# Busque uma patente
curl -X POST http://localhost:8000/api/wipo/patent \
  -H "Content-Type: application/json" \
  -d '{"wo_number": "WO2018162793"}'
```

**Resultado esperado:**
```json
{
  "publicacao": "WO2018162793",
  "titulo": "Imidazolylpyrrolidines...",
  "titular": "Orion Corporation",
  "paises_familia": ["BR", "US", "EP", ...],
  ...
}
```

---

## Integração n8n

### 1. Configure variável de ambiente

```
WIPO_API_URL=https://seu-app.up.railway.app
```

### 2. Use HTTP Request node

```json
{
  "method": "POST",
  "url": "{{ $env.WIPO_API_URL }}/api/wipo/patent",
  "body": {
    "wo_number": "{{ $json.wo_number }}"
  }
}
```

### 3. Processe resultado

```javascript
const data = $input.first().json;
const hasBR = data.paises_familia?.includes('BR');

return [{
  json: {
    wo: data.publicacao,
    title: data.titulo,
    has_br: hasBR
  }
}];
```

---

## Troubleshooting

### Erro: "playwright not found"

```bash
playwright install chromium
```

### Erro: "Permission denied"

```bash
chmod +x deploy.sh
```

### Timeout

```bash
# Aumente o timeout
railway variables set WIPO_TIMEOUT=90000
```

---

## Próximos Passos

1. ✅ Leia `README.md` para documentação completa
2. ✅ Veja `docs/API.md` para referência da API
3. ✅ Execute `python tests/test_crawler.py` para validar
4. ✅ Acesse `/docs` para documentação interativa

---

**🎉 Pronto para usar!**
