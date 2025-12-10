# 🚀 Pharmyrus API v3.0 - URLs PARA TESTAR

## 🔬 PIPELINE COMPLETO (NOVO!)

Base URL: `https://pharmyrus-total10-production.up.railway.app`

### ✅ Busca Completa por Molécula

**Endpoint:** `/api/v1/search/{molecule}?country={filter}&limit={num}`

**O que faz:**
1. 📊 **PubChem** → Busca sinônimos, dev codes, CAS, propriedades químicas
2. 🔍 **Google Patents** → Descobre WO numbers (múltiplas queries em paralelo)
3. 📄 **WIPO + Google Details** → Busca detalhes completos de cada WO (batch)
4. 🇧🇷 **INPI Brasil** → Busca patentes BR diretas
5. 💊 **FDA** → Dados regulatórios e aprovações
6. 🏥 **ClinicalTrials.gov** → Estudos clínicos

**Tempo de resposta:** ~30-60 segundos (processamento paralelo)

---

## 🧪 MOLÉCULAS TESTADAS

### 1. Darolutamide (Oncologia - Próstata)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/darolutamide

✅ Filtro Brasil apenas:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/darolutamide?country=BR

✅ Filtro múltiplos países:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/darolutamide?country=BR_US_JP

✅ Com limit:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/darolutamide?country=BR&limit=5
```

### 2. Olaparib (Oncologia - PARP Inhibitor)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/olaparib

✅ Brasil + US:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/olaparib?country=BR_US

✅ Top 3 WO patents:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/olaparib?limit=3
```

### 3. Venetoclax (Oncologia - Leucemia)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/venetoclax

✅ Brasil + Europa + US:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/venetoclax?country=BR_EP_US
```

### 4. Axitinib (Oncologia - Renal)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/axitinib

✅ BRICS:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/axitinib?country=BR_CN_IN
```

### 5. Niraparib (Oncologia - Ovário)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/niraparib
```

### 6. Tivozanib (Oncologia - Renal)
```
✅ Básico:
https://pharmyrus-total10-production.up.railway.app/api/v1/search/tivozanib
```

---

## 📋 ESTRUTURA DO JSON DE RESPOSTA

```json
{
  "executive_summary": {
    "molecule_name": "darolutamide",
    "generic_name": "DAROLUTAMIDE",
    "commercial_name": "Nubeqa",
    "cas_number": "1297550-10-5",
    "dev_codes": ["ODM-201", "BAY-1841788"],
    "total_patents": 150,
    "total_wo_patents": 25,
    "total_br_patents": 13,
    "jurisdictions": {
      "brazil": 13,
      "usa": 55,
      "europe": 10,
      "china": 12,
      "japan": 8,
      "worldwide": 25
    },
    "fda_status": "Approved",
    "clinical_trials_count": 245,
    "search_timestamp": "2025-12-10T..."
  },
  
  "pubchem_data": {
    "cid": 123456,
    "iupac_name": "...",
    "molecular_formula": "C19H19ClF2N4O2",
    "molecular_weight": 408.8,
    "smiles": "...",
    "inchi": "...",
    "inchi_key": "...",
    "synonyms": ["ODM-201", "BAY-1841788", ...],
    "dev_codes": ["ODM-201", "BAY-1841788"],
    "cas_number": "1297550-10-5",
    "xlogp": 3.4,
    "tpsa": 92.5,
    "hydrogen_bond_donors": 2,
    "hydrogen_bond_acceptors": 6,
    "rotatable_bonds": 4,
    "heavy_atom_count": 28
  },
  
  "search_strategy": {
    "molecule_searched": "darolutamide",
    "country_filter": "BR_US_JP",
    "layers_executed": [
      "PubChem",
      "Google Patents WO Search", 
      "Patent Details Batch (WIPO+Google)",
      "INPI Brasil",
      "FDA",
      "ClinicalTrials.gov"
    ],
    "parallel_processing": true,
    "sources": ["PubChem", "Google Patents", "WIPO", "INPI Brasil", "FDA", "ClinicalTrials.gov"]
  },
  
  "wo_patents": [
    {
      "wo_number": "WO2018162793",
      "title": "Combination therapy...",
      "abstract": "The present invention...",
      "assignees": ["Bayer Pharma AG", "Orion Corporation"],
      "inventors": ["John Doe", "Jane Smith"],
      "priority_date": "2017-03-10",
      "filing_date": "2018-03-09",
      "publication_date": "2018-09-13",
      "patent_family": ["BR", "US", "EP", "JP", "CN", "CA"],
      "worldwide_applications": {
        "BR": [
          {"document_id": "BR112019018744A2", "date": "2019-09-10"},
          {"document_id": "BR112019018744B1", "date": "2023-05-15"}
        ],
        "US": [
          {"document_id": "US20200038443A1", "date": "2020-02-06"}
        ]
      },
      "claims_count": 25,
      "citations_count": 45,
      "legal_status": "Active",
      "source": "wipo+google"
    }
  ],
  
  "br_patents_inpi": [
    {
      "publication_number": "BR-112019018744",
      "title": "Bayer Pharma AG",
      "abstract": "Combinação farmacêutica...",
      "filing_date": "2019-09-10",
      "assignee": "Bayer Pharma AG",
      "link": "https://busca.inpi.gov.br/...",
      "source": "inpi"
    }
  ],
  
  "all_patents": [
    {
      "publication_number": "WO2018162793",
      "title": "...",
      "abstract": "...",
      "assignees": ["Bayer Pharma AG"],
      "inventors": ["..."],
      "filing_date": "2018-03-09",
      "publication_date": "2018-09-13",
      "priority_date": "2017-03-10",
      "jurisdiction": "WO",
      "legal_status": "Active",
      "source": "wipo",
      "patent_family_size": 25
    },
    {
      "publication_number": "BR112019018744A2",
      "title": "...",
      "assignees": ["Bayer Pharma AG"],
      "filing_date": "2019-09-10",
      "jurisdiction": "BR",
      "source": "wipo_worldwide",
      "parent_wo": "WO2018162793"
    }
  ],
  
  "fda_data": {
    "molecule_name": "darolutamide",
    "fda_approval_status": "Approved",
    "fda_applications": [...],
    "marketing_status": "HUMAN PRESCRIPTION DRUG",
    "approval_date": "2019-07-30",
    "sponsor": "Bayer HealthCare",
    "indications": ["Treatment of non-metastatic castration-resistant prostate cancer..."],
    "data_source": "FDA APIs",
    "fetch_timestamp": "2025-12-10T..."
  },
  
  "clinical_trials_data": {
    "molecule_name": "darolutamide",
    "total_trials": 245,
    "trials_by_phase": {
      "Phase 1": 15,
      "Phase 2": 45,
      "Phase 3": 120,
      "Phase 4": 65
    },
    "trials_by_status": {
      "Recruiting": 25,
      "Active, not recruiting": 50,
      "Completed": 150,
      "Terminated": 10,
      "Unknown": 10
    },
    "primary_sponsors": ["Bayer", "Orion Corporation", ...],
    "countries": ["United States", "Brazil", "Japan", "Germany", ...]
  },
  
  "debug_info": {
    "total_duration_seconds": 45.67,
    "layers": [
      {
        "name": "PubChem",
        "status": "success",
        "duration": 2.34,
        "data_points": {
          "cid": 123456,
          "synonyms_found": 45,
          "dev_codes_found": 3,
          "cas_found": true
        }
      },
      {
        "name": "Google Patents WO Search",
        "status": "success",
        "duration": 12.56,
        "queries_executed": 13,
        "wo_numbers_found": 25
      },
      {
        "name": "Patent Details Batch (WIPO+Google)",
        "status": "success",
        "duration": 25.34,
        "total_wos": 25,
        "successful": 24,
        "failed": 1
      },
      {
        "name": "INPI Brasil",
        "status": "success",
        "duration": 8.45,
        "search_terms": 8,
        "br_patents_found": 13
      },
      {
        "name": "FDA",
        "status": "success",
        "duration": 1.23,
        "approval_found": true
      },
      {
        "name": "ClinicalTrials.gov",
        "status": "success",
        "duration": 3.45,
        "trials_found": 245
      }
    ],
    "timings": {
      "pubchem": 2.34,
      "google_patents_search": 12.56,
      "patent_details_batch": 25.34,
      "inpi_brasil": 8.45,
      "fda": 1.23,
      "clinical_trials": 3.45
    },
    "errors_count": 0,
    "warnings_count": 2,
    "errors": [],
    "warnings": [
      {
        "layer": "Google Search",
        "query": "darolutamide patent WO2024",
        "error": "timeout"
      }
    ]
  },
  
  "generated_at": "2025-12-10T15:30:45.123456"
}
```

---

## 🎯 PARÂMETROS SUPORTADOS

### Country Filter (opcional)
Códigos de países separados por underscore:
- `BR` - Brasil
- `US` - Estados Unidos
- `EP` - Europa (EPO)
- `JP` - Japão
- `CN` - China
- `CA` - Canadá
- `AU` - Austrália
- `KR` - Coreia do Sul
- `IN` - Índia

**Exemplos:**
- `?country=BR` - Apenas Brasil
- `?country=BR_US` - Brasil + EUA
- `?country=BR_US_JP_EP` - 4 países
- Sem parâmetro = Todos os países

### Limit (opcional)
Número máximo de WO patents a buscar detalhes:
- `?limit=5` - Busca apenas top 5 WO numbers
- `?limit=10` - Padrão
- `?limit=20` - Máximo recomendado

---

## 🔧 ENDPOINTS AUXILIARES

### 1. Home / Documentação
```
https://pharmyrus-total10-production.up.railway.app/
```

### 2. Health Check
```
https://pharmyrus-total10-production.up.railway.app/health
```

### 3. Swagger UI
```
https://pharmyrus-total10-production.up.railway.app/docs
```

### 4. Cache Stats
```
https://pharmyrus-total10-production.up.railway.app/api/cache/stats
```

### 5. WIPO Direto (sem pipeline)
```
# Teste simples
https://pharmyrus-total10-production.up.railway.app/test/WO2018162793

# Com filtro de país
https://pharmyrus-total10-production.up.railway.app/api/v1/wipo/WO2018162793?country=BR
```

---

## ⏱️ PERFORMANCE ESPERADA

| Camada | Tempo Médio | Descrição |
|--------|-------------|-----------|
| PubChem | 1-3s | Dados químicos |
| Google Patents WO Search | 10-15s | Busca WO numbers (13 queries paralelas) |
| Patent Details Batch | 20-30s | Detalhes de cada WO (paralelo) |
| INPI Brasil | 5-10s | Patentes BR diretas |
| FDA | 1-2s | Dados regulatórios |
| ClinicalTrials | 2-4s | Estudos clínicos |
| **TOTAL** | **40-65s** | **Pipeline completo** |

---

## 🎨 DIFERENÇAS v2.0 → v3.0

### v2.0 (Antigo)
```
GET /api/v1/search/darolutamide
↓
{
  "error": "Endpoint em desenvolvimento",
  "suggestion": "Use /api/v1/wipo/WO2018162793"
}
```

### v3.0 (Novo) 🚀
```
GET /api/v1/search/darolutamide?country=BR
↓
{
  "executive_summary": {...},      ← Resumo executivo
  "pubchem_data": {...},            ← 50+ propriedades químicas
  "wo_patents": [25 patents],       ← 25 WO patents completos
  "br_patents_inpi": [13 patents],  ← 13 BR do INPI
  "all_patents": [150 patents],     ← Agregação total
  "fda_data": {...},                ← FDA completo
  "clinical_trials_data": {...},    ← 245 estudos
  "debug_info": {...}               ← Timings detalhados
}
```

---

## 📊 MÉTRICAS DE QUALIDADE

A resposta inclui métricas automáticas:

```json
{
  "debug_info": {
    "layers": [
      {
        "name": "PubChem",
        "status": "success",
        "duration": 2.34,
        "data_points": {
          "synonyms_found": 45,
          "dev_codes_found": 3,
          "cas_found": true
        }
      }
    ],
    "errors_count": 0,
    "warnings_count": 2
  }
}
```

---

## 🐛 DEBUG MODE

Toda resposta inclui `debug_info` com:
- ⏱️ Timing de cada camada
- ✅ Status de sucesso/falha
- ⚠️ Warnings (timeouts, queries sem resultado)
- ❌ Errors (falhas críticas)
- 📊 Data points coletados por camada

---

## 🔄 RETRY & FALLBACK

O pipeline é resiliente:
- Timeouts individuais por layer
- Continue-on-error para layers opcionais
- Cache automático de WO patents
- Retry automático para falhas temporárias

---

## 💡 DICAS DE USO

1. **Primeira busca**: Pode demorar 60s (sem cache)
2. **Buscas subsequentes**: WO patents ficam em cache (instantâneo)
3. **Filtro de país**: Aplique DEPOIS da busca (não reduz tempo)
4. **Limit**: Use para acelerar testes (limit=3)
5. **Molecules testadas**: Use as 6 oncológicas para garantir resultados

---

## 🚨 TROUBLESHOOTING

### Timeout (>60s)
```
Causa: Muitos WO numbers encontrados
Solução: Use ?limit=5
```

### Poucos resultados
```
Causa: Molécula muito nova ou genérica
Solução: Verifique nome correto no PubChem
```

### Erro 500
```
Causa: Serviço externo indisponível
Solução: Retry após 1min ou consulte debug_info
```

---

## 📞 SUPORTE

Base URL Railway: `https://pharmyrus-total10-production.up.railway.app`

Documentação interativa: `/docs`
