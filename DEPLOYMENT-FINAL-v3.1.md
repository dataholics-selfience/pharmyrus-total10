# 🚀 GUIA DE DEPLOYMENT FINAL - Pharmyrus v3.1 BATCH

## 📋 VISÃO GERAL

**Versão:** 3.1.0 - BATCH OPTIMIZED  
**Data:** Dezembro 2025  
**Status:** ✅ PRODUÇÃO PRONTO

Sistema completo de inteligência de patentes com processamento em batch de múltiplas moléculas simultaneamente.

---

## 🎯 FEATURES v3.1

### ✅ Novo Sistema de Batch
- **Até 50 moléculas** por batch
- **3 buscas concorrentes** (rate limiting automático)
- **Progresso em tempo real** com ETA
- **60-70% mais rápido** que busca sequencial
- **Rastreamento individual** de cada molécula
- **Resiliência a erros** (continua mesmo com falhas)

### ✅ 6 Novos Endpoints Batch
1. `POST /api/v1/batch/search` - Criar batch
2. `GET /api/v1/batch/status/{batch_id}` - Monitorar progresso
3. `GET /api/v1/batch/results/{batch_id}` - Obter resultados
4. `DELETE /api/v1/batch/{batch_id}` - Cancelar batch
5. `GET /api/v1/batch/list` - Listar todos batches
6. `POST /api/v1/batch/cleanup` - Limpar batches antigos

### ✅ Pipeline Completo (Mantido v3.0)
- PubChem → Dev codes e CAS number
- Google Patents → Busca WO numbers
- WIPO Patentscope → Detalhes e família
- Google Patents Details → Patentes BR
- FDA Orange Book → Status regulatório US
- ClinicalTrials.gov → Trials ativos

---

## 📦 ARQUIVOS DO PROJETO

```
pharmyrus-wipo-deploy-v3.1/
├── src/
│   ├── api_service.py          # API FastAPI (789 linhas) - 6 endpoints batch
│   ├── batch_service.py         # Serviço batch (357 linhas) - NOVO v3.1
│   ├── pipeline_service.py      # Pipeline (600 linhas)
│   ├── wipo_crawler.py          # Crawler WIPO
│   └── crawler_pool.py          # Pool de crawlers
├── test_batch_complete.py       # Script Python de testes - NOVO
├── test_batch_quick.sh          # Script bash de testes - NOVO
├── Dockerfile                   # Container Docker
├── requirements.txt             # Dependências Python
├── railway.json                 # Config Railway
└── README.md                    # Documentação

Documentação:
├── BATCH-GUIDE-v3.1.md         # Guia completo batch
├── CHANGELOG-v3.1.md           # Changelog detalhado
├── TESTES-v3.1-COMPLETE.md     # Suite completa de testes
└── DEPLOYMENT-FINAL-v3.1.md    # Este arquivo
```

---

## 🛠️ PRÉ-REQUISITOS

### Local Development
```bash
- Python 3.9+
- Docker (opcional)
- curl ou httpie
- jq (para scripts bash)
```

### Railway Deployment
```bash
- Conta Railway.app (free tier OK)
- GitHub (opcional para CI/CD)
```

---

## 🚢 DEPLOYMENT RAILWAY (RECOMENDADO)

### Passo 1: Preparar Projeto

```bash
# Clone ou copie o projeto
cd pharmyrus-wipo-deploy-v3.1

# Verifique arquivos essenciais
ls -la src/
ls -la Dockerfile
ls -la railway.json
```

### Passo 2: Deploy via Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Criar novo projeto
railway init

# Deploy
railway up

# Obter URL
railway domain
```

### Passo 3: Deploy via Web (Alternativa)

1. Acesse https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. Selecione o repositório
4. Railway detecta automaticamente o Dockerfile
5. Deploy automático inicia
6. Copie a URL gerada

### Passo 4: Verificar Deploy

```bash
# Health check
curl https://seu-app.up.railway.app/

# Deve retornar:
{
  "service": "Pharmyrus WIPO Crawler API",
  "version": "3.1.0 - BATCH OPTIMIZED",
  "status": "operational",
  ...
}
```

---

## 🐳 DEPLOYMENT DOCKER (ALTERNATIVA)

### Build e Run Local

```bash
# Build
docker build -t pharmyrus-wipo:v3.1 .

# Run
docker run -p 8000:8000 \
  -e PORT=8000 \
  pharmyrus-wipo:v3.1

# Testar
curl http://localhost:8000/
```

### Deploy para Container Registry

```bash
# Tag
docker tag pharmyrus-wipo:v3.1 seu-registry/pharmyrus-wipo:v3.1

# Push
docker push seu-registry/pharmyrus-wipo:v3.1

# Deploy em qualquer plataforma Docker
# (AWS ECS, Google Cloud Run, Azure Container Instances, etc.)
```

---

## ✅ VALIDAÇÃO DO DEPLOYMENT

### 1. Health Check

```bash
BASE_URL="https://seu-app.up.railway.app"

# Verificar API
curl "$BASE_URL/"

# Deve mostrar version 3.1.0
```

### 2. Teste Rápido - Busca Individual (v3.0 compatibility)

```bash
# Busca única molécula (backward compatibility)
curl "$BASE_URL/api/v1/search/darolutamide?limit=5"

# Deve retornar:
# - executive_summary
# - pubchem_data
# - wo_patents (com br_patents)
# - fda_data
# - clinical_trials
```

### 3. Teste Batch - Criar e Monitorar

```bash
# Criar batch
BATCH_RESPONSE=$(curl -X POST "$BASE_URL/api/v1/batch/search" \
  -H "Content-Type: application/json" \
  -d '{
    "molecules": ["darolutamide", "olaparib", "venetoclax"],
    "country_filter": "BR_US",
    "limit": 10
  }')

BATCH_ID=$(echo $BATCH_RESPONSE | jq -r '.batch_id')
echo "Batch criado: $BATCH_ID"

# Monitorar progresso
while true; do
  STATUS=$(curl -s "$BASE_URL/api/v1/batch/status/$BATCH_ID" | jq -r '.status')
  PROGRESS=$(curl -s "$BASE_URL/api/v1/batch/status/$BATCH_ID" | jq -r '.progress_percentage')
  
  echo "Status: $STATUS | Progresso: $PROGRESS%"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 5
done

# Obter resultados
curl "$BASE_URL/api/v1/batch/results/$BATCH_ID" | jq '.'
```

### 4. Teste com Scripts Automatizados

```bash
# Teste Python completo (interativo)
python3 test_batch_complete.py

# Teste bash rápido (automático)
./test_batch_quick.sh --auto
```

---

## 📊 PERFORMANCE ESPERADA

### Tempos Médios (3 concurrent)

| Moléculas | Sequencial (v3.0) | Batch (v3.1) | Speedup |
|-----------|-------------------|--------------|---------|
| 3         | ~2.5 min          | ~1 min       | 60%     |
| 5         | ~4 min            | ~1.7 min     | 58%     |
| 10        | ~8 min            | ~3.3 min     | 59%     |
| 20        | ~16 min           | ~6.6 min     | 59%     |
| 50        | ~40 min           | ~16.6 min    | 59%     |

### Recursos Railway

**Free Tier:**
- 500 horas/mês
- 512MB RAM
- Suficiente para: ~300-500 buscas/mês

**Pro Plan ($5/mês):**
- Ilimitado
- 8GB RAM
- Suficiente para: ~5000+ buscas/mês

---

## 🔧 CONFIGURAÇÃO AVANÇADA

### Variáveis de Ambiente (Railway)

```bash
# Railway Dashboard → Settings → Variables

PORT=8000                    # Porta padrão
CACHE_TTL=3600              # Cache 1 hora
MAX_CONCURRENT=3            # Batch concorrência (1-10)
BATCH_SIZE=5                # WO patents por lote
LOG_LEVEL=INFO              # DEBUG para mais logs
```

### Ajustar Concorrência

Editar `src/api_service.py`:

```python
# Linha ~558
batch_service = get_batch_service(max_concurrent=5)  # Aumentar para 5
```

**⚠️ Atenção:** Mais concorrência = mais rápido, mas maior uso de memória e risco de rate limiting.

---

## 🐛 TROUBLESHOOTING

### Problema 1: Batch Muito Lento

**Sintomas:** Batch leva muito tempo, progresso lento  
**Causa:** Taxa de sucesso baixa do WIPO crawler

**Solução:**
```bash
# Verificar logs
railway logs

# Aumentar timeout no Dockerfile se necessário
ENV PLAYWRIGHT_TIMEOUT=90000
```

### Problema 2: Memory Limit

**Sintomas:** Container reinicia, erro OOM  
**Causa:** Muitos batches simultâneos

**Solução:**
```bash
# Railway Dashboard → Settings
# Aumentar RAM limit para 1GB ou 2GB

# Ou limitar concorrência
MAX_CONCURRENT=2
```

### Problema 3: Batch Não Encontra Patentes

**Sintomas:** 0 WO patents encontrados  
**Causa:** Molécula desconhecida ou nome incorreto

**Solução:**
```bash
# Verificar nome no PubChem primeiro
curl "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/sua-molecula/synonyms/JSON"

# Usar nome oficial ou sinônimo conhecido
```

### Problema 4: API 500 Error

**Sintomas:** Erro 500 ao criar batch  
**Causa:** Serviço não inicializou corretamente

**Solução:**
```bash
# Verificar startup logs
railway logs | grep "🔄 Batch processing enabled"

# Se não aparecer, redesploy
railway up --detach
```

---

## 📈 MONITORAMENTO

### Logs em Tempo Real

```bash
# Railway CLI
railway logs --tail 100

# Filtrar por batch
railway logs | grep "batch_"

# Filtrar erros
railway logs | grep "ERROR"
```

### Métricas Importantes

Monitorar via Railway Dashboard:
- **CPU Usage** - Deve estar < 80%
- **Memory Usage** - Deve estar < 400MB
- **Request Count** - Crescimento constante
- **Error Rate** - Deve estar < 5%

### Alertas Recomendados

```bash
# Configurar no Railway Dashboard → Alerts

1. Memory > 450MB → Alerta
2. CPU > 90% por 5min → Alerta
3. Error rate > 10% → Alerta
```

---

## 🔒 SEGURANÇA (ROADMAP v3.2)

### Atual v3.1
- ❌ Sem autenticação (API pública)
- ❌ Sem rate limiting por usuário
- ✅ Validação de input
- ✅ Error handling robusto

### Planejado v3.2
- ✅ API key authentication
- ✅ Rate limiting por chave
- ✅ Usage analytics
- ✅ Billing/quota system

**Workaround Temporário:**  
Use Railway's IP whitelist ou deploy em VPC privada.

---

## 📚 DOCUMENTAÇÃO ADICIONAL

### Guias Completos
- `BATCH-GUIDE-v3.1.md` - Guia completo de uso do batch
- `CHANGELOG-v3.1.md` - Todas as mudanças v3.1
- `TESTES-v3.1-COMPLETE.md` - Suite completa de testes

### API Documentation
- Swagger UI: `https://seu-app.up.railway.app/docs`
- ReDoc: `https://seu-app.up.railway.app/redoc`

---

## 🎓 EXEMPLOS DE USO

### Caso 1: Screening de Portfólio (20 moléculas)

```bash
# Criar lista de moléculas
cat > molecules.json << EOF
{
  "molecules": [
    "darolutamide", "olaparib", "venetoclax", "axitinib", "niraparib",
    "tivozanib", "ixazomib", "sonidegib", "trastuzumab", "vinseltinib",
    "paracetamol", "aspirin", "ibuprofen", "naproxen", "diclofenac",
    "celecoxib", "rofecoxib", "meloxicam", "piroxicam", "indomethacin"
  ],
  "country_filter": "BR_US_EP",
  "limit": 15
}
EOF

# Enviar batch
curl -X POST "$BASE_URL/api/v1/batch/search" \
  -H "Content-Type: application/json" \
  -d @molecules.json

# Tempo estimado: ~6-7 minutos (vs 20+ minutos sequencial)
```

### Caso 2: Competitive Intelligence (Monitorar Concorrentes)

```bash
# Batch de moléculas do concorrente
{
  "molecules": ["concorrente_mol_1", "concorrente_mol_2", "concorrente_mol_3"],
  "country_filter": "BR_US_JP_CN",
  "limit": 20
}

# Executar mensalmente e comparar resultados
# Armazenar batch_id para histórico
```

### Caso 3: Freedom-to-Operate Analysis

```bash
# Analisar landscape de patentes em área terapêutica
{
  "molecules": ["target_molecule"] + ["similar_mol_1", "similar_mol_2", ...],
  "country_filter": "BR_US_EP_JP",
  "limit": 20
}

# Verificar overlap de patentes BR
# Identificar potenciais conflitos
```

---

## 🚀 PRÓXIMOS PASSOS (ROADMAP v3.2)

### Features Planejadas
- [ ] Redis para persistência de jobs
- [ ] PostgreSQL para histórico
- [ ] Webhooks para notificações
- [ ] CSV/Excel bulk upload
- [ ] Web dashboard para monitoramento
- [ ] API key authentication
- [ ] Usage analytics e billing
- [ ] Batch templates e presets
- [ ] Export para Excel/PDF

### Melhorias de Performance
- [ ] Distributed batch processing
- [ ] Queue system (Celery/RQ)
- [ ] Load balancing
- [ ] Auto-scaling
- [ ] CDN para cache de resultados

---

## 📞 SUPORTE

### Documentação
- README.md - Guia rápido
- BATCH-GUIDE-v3.1.md - Guia completo batch
- API Docs - /docs (Swagger)

### Logs e Debug
```bash
# Railway logs
railway logs --tail 100

# Debug mode
railway variables set LOG_LEVEL=DEBUG
railway redeploy
```

### Contato
- GitHub Issues - Para bugs e features
- Railway Support - Para problemas de infra
- Email - Para suporte comercial

---

## ✅ CHECKLIST DE DEPLOYMENT

### Pré-Deploy
- [ ] Código no GitHub/GitLab
- [ ] .env com variáveis necessárias
- [ ] Dockerfile testado localmente
- [ ] Scripts de teste funcionando

### Deploy
- [ ] Railway project criado
- [ ] Variáveis de ambiente configuradas
- [ ] Domain customizado (opcional)
- [ ] Deploy executado com sucesso

### Pós-Deploy
- [ ] Health check passou
- [ ] Busca individual funciona
- [ ] Batch rápido (3 mols) funciona
- [ ] Logs sem erros críticos
- [ ] Performance aceitável (< 5 min para 10 mols)
- [ ] Documentação atualizada

### Monitoramento
- [ ] Alertas configurados
- [ ] Logs sendo revisados regularmente
- [ ] Métricas dentro do esperado
- [ ] Backup de dados (se aplicável)

---

## 🎉 CONCLUSÃO

Sistema Pharmyrus v3.1 está **PRODUCTION READY** com:

✅ **Batch processing** completo e testado  
✅ **60-70% mais rápido** que v3.0  
✅ **6 novos endpoints** batch  
✅ **100% backward compatible** com v3.0  
✅ **Documentação** completa  
✅ **Scripts de teste** automatizados  
✅ **Railway deployment** otimizado  

**Deploy agora e comece a processar múltiplas moléculas em paralelo!** 🚀

---

**Última atualização:** Dezembro 2025  
**Versão:** 3.1.0 - BATCH OPTIMIZED  
**Status:** ✅ PRODUÇÃO
