# 📚 API Documentation

## Base URL

```
Production: https://seu-app.up.railway.app
Local: http://localhost:8000
```

## Endpoints

### 1. Health Check

Verifica status do serviço.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-09T10:30:00",
  "cache_size": 5,
  "pool_active": false
}
```

---

### 2. Buscar Patente Única

Busca uma patente WO específica.

**Endpoint:** `POST /api/wipo/patent`

**Request Body:**
```json
{
  "wo_number": "WO2018162793",
  "use_cache": true
}
```

**Response:**
```json
{
  "fonte": "WIPO",
  "pais": "WO",
  "publicacao": "WO2018162793",
  "pedido": "PCT/EP2018/055942",
  "titulo": "Imidazolylpyrrolidines as selective androgen receptor degraders",
  "titular": "Orion Corporation",
  "datas": {
    "deposito": "2018-03-09",
    "publicacao": "2018-09-13",
    "prioridade": "2017-03-10"
  },
  "inventores": ["Smith, John", "Doe, Jane"],
  "cpc_ipc": ["C07D401/12", "A61K31/4709"],
  "resumo": "The present invention relates to compounds...",
  "paises_familia": ["BR", "US", "EP", "CN", "JP"],
  "documentos": {
    "pdf_link": "https://patentscope.wipo.int/...",
    "patentscope_link": "https://patentscope.wipo.int/search/en/detail.jsf?docId=WO2018162793"
  },
  "worldwide_applications": {
    "BR": [],
    "US": [],
    "EP": []
  },
  "duracao_segundos": 12.34
}
```

---

### 3. Buscar Lote de Patentes

Busca múltiplas patentes, com opção de usar pooling.

**Endpoint:** `POST /api/wipo/patents/batch`

**Request Body:**
```json
{
  "wo_numbers": [
    "WO2018162793",
    "WO2016168716",
    "WO2015095053"
  ],
  "use_cache": true,
  "use_pool": true,
  "pool_size": 3
}
```

**Parameters:**
- `wo_numbers` (required): Lista de números WO
- `use_cache` (optional, default: true): Usar cache
- `use_pool` (optional, default: true): Usar pooling para paralelização
- `pool_size` (optional, default: 3, max: 5): Tamanho do pool

**Response:**
```json
{
  "total": 3,
  "cached": 1,
  "fetched": 2,
  "results": [
    {
      "fonte": "WIPO",
      "publicacao": "WO2018162793",
      "titulo": "...",
      ...
    },
    ...
  ]
}
```

---

### 4. Limpar Cache

Limpa o cache de uma patente específica ou todo o cache.

**Endpoint:** `DELETE /api/cache/clear`

**Query Parameters:**
- `wo_number` (optional): Número WO específico para limpar

**Examples:**

```bash
# Limpar patente específica
DELETE /api/cache/clear?wo_number=WO2018162793

# Limpar todo cache
DELETE /api/cache/clear
```

**Response:**
```json
{
  "message": "Cache limpo: WO2018162793"
}
```

---

### 5. Estatísticas do Cache

Retorna estatísticas do cache atual.

**Endpoint:** `GET /api/cache/stats`

**Response:**
```json
{
  "size": 5,
  "ttl_seconds": 3600,
  "entries": [
    {
      "wo_number": "WO2018162793",
      "age_seconds": 150.5,
      "expires_in": 3449.5
    },
    ...
  ]
}
```

---

## Exemplos de Uso

### cURL

```bash
# Health check
curl https://seu-app.railway.app/health

# Buscar patente única
curl -X POST https://seu-app.railway.app/api/wipo/patent \
  -H "Content-Type: application/json" \
  -d '{"wo_number": "WO2018162793"}'

# Buscar lote com pooling
curl -X POST https://seu-app.railway.app/api/wipo/patents/batch \
  -H "Content-Type: application/json" \
  -d '{
    "wo_numbers": ["WO2018162793", "WO2016168716"],
    "use_pool": true,
    "pool_size": 3
  }'

# Limpar cache
curl -X DELETE "https://seu-app.railway.app/api/cache/clear"
```

### Python

```python
import requests

BASE_URL = "https://seu-app.railway.app"

# Buscar patente
response = requests.post(
    f"{BASE_URL}/api/wipo/patent",
    json={"wo_number": "WO2018162793"}
)
data = response.json()
print(data['titulo'])

# Buscar lote
response = requests.post(
    f"{BASE_URL}/api/wipo/patents/batch",
    json={
        "wo_numbers": ["WO2018162793", "WO2016168716"],
        "use_pool": True,
        "pool_size": 3
    }
)
batch_data = response.json()
print(f"Total: {batch_data['total']}")
```

### JavaScript/Node.js

```javascript
const BASE_URL = "https://seu-app.railway.app";

// Buscar patente
const response = await fetch(`${BASE_URL}/api/wipo/patent`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ wo_number: 'WO2018162793' })
});

const data = await response.json();
console.log(data.titulo);

// Buscar lote
const batchResponse = await fetch(`${BASE_URL}/api/wipo/patents/batch`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    wo_numbers: ['WO2018162793', 'WO2016168716'],
    use_pool: true,
    pool_size: 3
  })
});

const batchData = await batchResponse.json();
console.log(`Total: ${batchData.total}`);
```

---

## Integração n8n

### HTTP Request Node

```json
{
  "method": "POST",
  "url": "{{ $env.WIPO_API_URL }}/api/wipo/patents/batch",
  "sendBody": true,
  "contentType": "json",
  "body": {
    "wo_numbers": "={{ $json.wo_list }}",
    "use_pool": true,
    "pool_size": 3
  },
  "options": {
    "timeout": 180000
  }
}
```

### Code Node (processar resultado)

```javascript
const data = $input.first().json;

// Filtra WOs com Brasil
const brWOs = data.results.filter(r => 
  r.paises_familia?.includes('BR')
);

return brWOs.map(wo => ({
  json: {
    wo_number: wo.publicacao,
    title: wo.titulo,
    applicant: wo.titular,
    has_br: true
  }
}));
```

---

## Rate Limits

- **Requests/minuto:** 30 (sem cache)
- **Requests/minuto:** Unlimited (com cache hit)
- **Pool máximo:** 5 crawlers simultâneos

## Performance

| Operação | Tempo Médio |
|----------|-------------|
| Cache Hit | < 1s |
| Busca Única | 10-30s |
| Busca Pool (3x) | 8-15s por patente |

## Erros Comuns

### 500 - Internal Server Error

```json
{
  "detail": "Erro ao buscar patente: timeout"
}
```

**Solução:** Aumente o timeout ou tente novamente.

### 422 - Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "wo_number"],
      "msg": "field required"
    }
  ]
}
```

**Solução:** Verifique os campos obrigatórios.

---

## Suporte

- 📚 Documentação Interativa: `/docs`
- 🐛 Issues: GitHub Issues
- 💬 Email: contato@pharmyrus.com
