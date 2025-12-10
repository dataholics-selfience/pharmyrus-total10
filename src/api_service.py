#!/usr/bin/env python3
"""
Pharmyrus WIPO API Service
FastAPI service otimizado para Railway
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
import logging
import os

from src.wipo_crawler import WIPOCrawler
from src.crawler_pool import WIPOCrawlerPool

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Pharmyrus WIPO Crawler API",
    description="API robusta para extração de patentes WIPO Patentscope",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache simples (em produção use Redis)
_cache: Dict[str, Dict[str, Any]] = {}
_cache_ttl = int(os.getenv('CACHE_TTL', '3600'))

# Pool global
_pool: Optional[WIPOCrawlerPool] = None


# Models
class PatentRequest(BaseModel):
    wo_number: str = Field(..., description="Número WO")
    use_cache: bool = Field(True, description="Usar cache")


class BatchRequest(BaseModel):
    wo_numbers: List[str] = Field(..., description="Lista de números WO")
    use_cache: bool = Field(True, description="Usar cache")
    use_pool: bool = Field(True, description="Usar pooling")
    pool_size: int = Field(3, ge=1, le=5, description="Tamanho do pool")


# Helper functions
def _get_cache_key(wo: str) -> str:
    return f"wipo_{wo.replace('WO', '').replace(' ', '')}"


def _get_from_cache(wo: str) -> Optional[Dict]:
    key = _get_cache_key(wo)
    if key in _cache:
        data = _cache[key]
        if (datetime.now().timestamp() - data.get('cached_at', 0)) < _cache_ttl:
            logger.info(f"✅ Cache HIT: {wo}")
            return data['result']
        del _cache[key]
    return None


def _set_cache(wo: str, result: Dict):
    key = _get_cache_key(wo)
    _cache[key] = {
        'result': result,
        'cached_at': datetime.now().timestamp()
    }


# Endpoints
@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "service": "Pharmyrus WIPO Crawler API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "# Browser-Friendly (GET)": {
                "test_wo": "/test/{wo_number}",
                "wipo_search": "/api/v1/wipo/{wo_number}?country=BR_US_JP",
                "molecule_search": "/api/v1/search/{molecule}?country=BR_US",
                "pipeline": "/api/v1/pipeline/{molecule} (em desenvolvimento)"
            },
            "# Advanced (POST)": {
                "single": "/api/wipo/patent",
                "batch": "/api/wipo/patents/batch"
            },
            "# Utilities": {
                "health": "/health",
                "cache_stats": "/api/cache/stats",
                "cache_clear": "/api/cache/clear",
                "docs": "/docs"
            }
        },
        "examples": {
            "simple_test": "/test/WO2018162793",
            "wipo_full": "/api/v1/wipo/WO2018162793?country=BR_US_JP",
            "molecule": "/api/v1/search/darolutamide?country=BR",
            "health": "/health",
            "docs": "/docs"
        },
        "known_molecules": {
            "darolutamide": ["WO2018162793", "WO2011103316"],
            "olaparib": ["WO2016168716"],
            "venetoclax": ["WO2013107291"],
            "axitinib": ["WO2011051540"]
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(_cache),
        "pool_active": _pool is not None,
        "features": {
            "browser_get": True,
            "post_api": True,
            "pooling": True,
            "cache": True
        }
    }


@app.post("/api/wipo/patent")
async def fetch_single_patent(request: PatentRequest):
    """Busca patente única"""
    wo = request.wo_number.strip().upper()
    
    logger.info(f"🔍 Request: {wo}")
    
    # Cache
    if request.use_cache:
        cached = _get_from_cache(wo)
        if cached:
            return JSONResponse(content=cached)
    
    try:
        async with WIPOCrawler() as crawler:
            result = await crawler.fetch_patent(wo)
        
        if request.use_cache and result.get('titulo'):
            _set_cache(wo, result)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wipo/patents/batch")
async def fetch_batch_patents(request: BatchRequest):
    """Busca lote de patentes"""
    wo_numbers = [wo.strip().upper() for wo in request.wo_numbers]
    
    logger.info(f"🔍 Batch: {len(wo_numbers)} patentes")
    
    results = []
    to_fetch = []
    
    # Verifica cache
    if request.use_cache:
        for wo in wo_numbers:
            cached = _get_from_cache(wo)
            if cached:
                results.append(cached)
            else:
                to_fetch.append(wo)
    else:
        to_fetch = wo_numbers
    
    logger.info(f"📊 Cache: {len(results)} | Buscar: {len(to_fetch)}")
    
    # Busca patentes
    if to_fetch:
        try:
            if request.use_pool and len(to_fetch) > 2:
                # Usa pool
                logger.info(f"🏊 Usando pool (size={request.pool_size})")
                async with WIPOCrawlerPool(pool_size=request.pool_size) as pool:
                    fetched = await pool.process_batch(to_fetch)
            else:
                # Sequencial
                logger.info("📝 Processamento sequencial")
                async with WIPOCrawler() as crawler:
                    fetched = await crawler.fetch_multiple_patents(to_fetch)
            
            # Adiciona aos resultados e cache
            for result in fetched:
                results.append(result)
                if request.use_cache and result.get('titulo'):
                    _set_cache(result['publicacao'], result)
                    
        except Exception as e:
            logger.error(f"❌ Erro no batch: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Ordena para manter ordem original
    def sort_key(item):
        try:
            return wo_numbers.index(item.get('publicacao', ''))
        except ValueError:
            return 999
    
    results.sort(key=sort_key)
    
    return JSONResponse(content={
        "total": len(results),
        "cached": len(results) - len(to_fetch),
        "fetched": len(to_fetch),
        "results": results
    })


@app.delete("/api/cache/clear")
async def clear_cache(wo_number: Optional[str] = None):
    """Limpa cache"""
    global _cache
    
    if wo_number:
        key = _get_cache_key(wo_number)
        if key in _cache:
            del _cache[key]
            return {"message": f"Cache limpo: {wo_number}"}
        return {"message": f"Cache não encontrado: {wo_number}"}
    else:
        count = len(_cache)
        _cache = {}
        return {"message": f"Cache completo limpo ({count} entradas)"}


@app.get("/api/cache/stats")
async def cache_stats():
    """Estatísticas do cache"""
    if not _cache:
        return {"size": 0, "entries": []}
    
    entries = []
    for key, data in _cache.items():
        age = datetime.now().timestamp() - data.get('cached_at', 0)
        entries.append({
            "wo_number": data['result'].get('publicacao'),
            "age_seconds": round(age, 2),
            "expires_in": round(_cache_ttl - age, 2)
        })
    
    return {
        "size": len(_cache),
        "ttl_seconds": _cache_ttl,
        "entries": sorted(entries, key=lambda x: x['age_seconds'])
    }


# ===== BROWSER-FRIENDLY GET ENDPOINTS =====

@app.get("/test/{wo_number}")
async def test_wo_simple(wo_number: str):
    """
    Endpoint simples para testar WO direto no browser
    Exemplo: /test/WO2018162793
    """
    wo = wo_number.strip().upper()
    logger.info(f"🧪 Test endpoint: {wo}")
    
    # Cache
    cached = _get_from_cache(wo)
    if cached:
        return JSONResponse(content=cached)
    
    try:
        async with WIPOCrawler() as crawler:
            result = await crawler.fetch_patent(wo)
        
        if result.get('titulo'):
            _set_cache(wo, result)
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/wipo/{wo_number}")
async def get_wipo_patent(
    wo_number: str,
    country: Optional[str] = None
):
    """
    Buscar patente WIPO por WO number (GET para browser)
    
    Exemplos:
    - /api/v1/wipo/WO2018162793
    - /api/v1/wipo/WO2018162793?country=BR_US_JP
    
    country: Filtrar países da família (BR, US, JP, EP, CN, etc)
    """
    wo = wo_number.strip().upper()
    logger.info(f"🔍 WIPO GET: {wo} | countries={country}")
    
    # Cache
    cached = _get_from_cache(wo)
    if cached:
        result = cached.copy()
    else:
        try:
            async with WIPOCrawler() as crawler:
                result = await crawler.fetch_patent(wo)
            
            if result.get('titulo'):
                _set_cache(wo, result)
                
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Filtrar países se solicitado
    if country and result.get('worldwide_applications'):
        countries = [c.strip().upper() for c in country.split('_')]
        filtered_apps = {
            k: v for k, v in result['worldwide_applications'].items()
            if k.upper() in countries
        }
        result['worldwide_applications'] = filtered_apps
        result['paises_familia'] = [p for p in result.get('paises_familia', []) if p.upper() in countries]
        result['filter_applied'] = country
    
    return JSONResponse(content=result)


@app.get("/api/v1/search/{molecule}")
async def search_by_molecule(
    molecule: str,
    country: Optional[str] = None,
    limit: int = 10
):
    """
    Buscar patentes por nome de molécula (GET para browser)
    
    Esta API busca WIPO diretamente. Para buscar WOs use o endpoint completo
    da Pharmyrus que integra PubChem + Google Patents + EPO.
    
    Exemplos:
    - /api/v1/search/darolutamide
    - /api/v1/search/darolutamide?country=BR_US_JP
    - /api/v1/search/olaparib?country=BR&limit=5
    
    Parâmetros:
    - molecule: Nome da molécula
    - country: Países alvo separados por _ (BR_US_JP)
    - limit: Número máximo de resultados (padrão 10)
    
    NOTA: Este endpoint busca no WIPO Patentscope diretamente.
    Para pipeline completo (PubChem > Google > EPO > WIPO > INPI),
    use o endpoint /api/v1/pipeline/{molecule}
    """
    mol = molecule.strip()
    logger.info(f"🔬 Busca molécula: {mol} | countries={country} | limit={limit}")
    
    return JSONResponse(content={
        "error": "Endpoint em desenvolvimento",
        "message": f"Para buscar '{mol}', use os WO numbers conhecidos",
        "suggestion": "Use o endpoint /api/v1/wipo/WO2018162793",
        "known_wos": {
            "darolutamide": ["WO2018162793", "WO2011103316"],
            "olaparib": ["WO2016168716", "WO2005012305"],
            "venetoclax": ["WO2013107291"],
            "axitinib": ["WO2011051540"]
        },
        "alternative": f"Ou use: /api/v1/wipo/WO[número] ou /test/WO[número]",
        "status": "use_wo_numbers_instead"
    })


@app.get("/api/v1/pipeline/{molecule}")
async def pipeline_search(
    molecule: str,
    country: Optional[str] = "BR_US_JP",
    sources: str = "pubchem,google,epo,wipo"
):
    """
    Pipeline completo de busca de patentes (futuro)
    
    Fluxo: PubChem > Google Patents > EPO > WIPO > INPI
    
    Exemplos:
    - /api/v1/pipeline/darolutamide
    - /api/v1/pipeline/darolutamide?country=BR_US
    
    NOTA: Este endpoint requer integração completa com outros serviços.
    Por enquanto, use os endpoints de WO direto.
    """
    return JSONResponse(content={
        "error": "Pipeline completo em desenvolvimento",
        "message": "Para busca completa, use o n8n workflow existente",
        "workflow_url": "https://seu-n8n.com/workflow/pharmyrus",
        "alternative": "Use /api/v1/wipo/WO[número] para buscar WIPO diretamente",
        "status": "under_development"
    })


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Startup"""
    logger.info("🚀 Pharmyrus WIPO API iniciando...")
    logger.info(f"📦 Cache TTL: {_cache_ttl}s")
    logger.info("✅ API pronta!")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown"""
    global _pool
    
    logger.info("🔒 Pharmyrus WIPO API encerrando...")
    
    if _pool:
        await _pool.close()
    
    logger.info(f"💾 Cache final: {len(_cache)} entradas")
    logger.info("✅ Encerrado")


# Main
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv('PORT', '8000'))
    
    uvicorn.run(
        "src.api_service:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
