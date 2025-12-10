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
from src.pipeline_service import pipeline_service

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
        "version": "3.1.0 - BATCH OPTIMIZED",
        "status": "operational",
        "description": "Complete patent intelligence pipeline with multi-source search + BATCH PROCESSING",
        "pipeline_features": [
            "✅ PubChem - Chemical data & synonyms",
            "✅ Google Patents - WO number discovery",
            "✅ WIPO Patentscope - Worldwide applications", 
            "✅ INPI Brasil - Brazilian patents",
            "✅ FDA - Regulatory data",
            "✅ ClinicalTrials.gov - Clinical studies",
            "✅ Parallel batch processing",
            "✅ Country filtering",
            "✅ Rich debug information",
            "🆕 BATCH: Multiple molecules with job tracking",
            "🆕 BATCH: Rate limiting & concurrency control"
        ],
        "endpoints": {
            "🚀 PIPELINE COMPLETO": {
                "search_molecule": "/api/v1/search/{molecule}",
                "description": "Complete pipeline: PubChem → Google → WIPO → INPI → FDA → ClinicalTrials",
                "examples": [
                    "/api/v1/search/darolutamide",
                    "/api/v1/search/darolutamide?country=BR",
                    "/api/v1/search/darolutamide?country=BR_US_JP",
                    "/api/v1/search/olaparib?country=BR_US&limit=5"
                ],
                "parameters": {
                    "molecule": "Molecule name (required)",
                    "country": "Country filter BR_US_JP_EP_CN_CA_AU_KR_IN (optional)",
                    "limit": "Max WO patents to fetch (default 10)"
                },
                "output": {
                    "executive_summary": "Totals, jurisdictions, FDA status, clinical trials",
                    "pubchem_data": "Complete chemical properties",
                    "wo_patents": "Detailed WO patent list with worldwide applications",
                    "br_patents_inpi": "Brazilian patents from INPI",
                    "all_patents": "Aggregated patents from all sources",
                    "fda_data": "Regulatory information",
                    "clinical_trials_data": "Clinical studies information",
                    "debug_info": "Layer timings, errors, warnings"
                }
            },
            "📦 BATCH PROCESSING (NEW v3.1)": {
                "create_batch": "POST /api/v1/batch/search",
                "get_status": "/api/v1/batch/status/{batch_id}",
                "get_results": "/api/v1/batch/results/{batch_id}",
                "cancel_batch": "DELETE /api/v1/batch/{batch_id}",
                "list_batches": "/api/v1/batch/list?status=processing",
                "cleanup": "POST /api/v1/batch/cleanup?max_age_hours=24",
                "description": "Process multiple molecules concurrently with job tracking",
                "features": [
                    "Up to 50 molecules per batch",
                    "3 concurrent searches (configurable)",
                    "Real-time progress tracking",
                    "Estimated time remaining",
                    "Individual molecule status",
                    "Automatic rate limiting"
                ],
                "example_request": {
                    "molecules": ["darolutamide", "olaparib", "venetoclax"],
                    "country_filter": "BR_US",
                    "limit": 10
                },
                "batch_time": "~3-5 minutes for 10 molecules (vs 8-10 minutes sequential)"
            },
            "🔍 WIPO Direct Search": {
                "test_simple": "/test/{wo_number}",
                "wipo_detailed": "/api/v1/wipo/{wo_number}",
                "examples": [
                    "/test/WO2018162793",
                    "/api/v1/wipo/WO2018162793",
                    "/api/v1/wipo/WO2018162793?country=BR",
                    "/api/v1/wipo/WO2018162793?country=BR_US_JP"
                ]
            },
            "💾 Cache Management": {
                "cache_stats": "/api/cache/stats",
                "clear_cache": "DELETE /api/cache/clear?wo_number=WO..."
            },
            "📚 Documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc"
            }
        },
        "tested_molecules": {
            "oncology": ["darolutamide", "olaparib", "venetoclax", "axitinib", "niraparib", "tivozanib"],
            "note": "Pipeline works with any molecule name"
        },
        "performance": {
            "single_molecule": "~30-60s (all layers parallel)",
            "batch_3_concurrent": "~3-5 min for 10 molecules",
            "batch_speedup": "60-70% faster than sequential"
        },
        "data_sources": [
            "PubChem (NIH)",
            "Google Patents (SerpAPI)",
            "WIPO Patentscope (Direct crawler)",
            "INPI Brasil (API)",
            "FDA APIs",
            "ClinicalTrials.gov"
        ]
    }
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
    🚀 PIPELINE COMPLETO: Buscar patentes por nome de molécula
    
    Fluxo completo de busca:
    1. PubChem → Sinônimos, dev codes, CAS, propriedades químicas
    2. Google Patents → Busca WO numbers com múltiplas queries
    3. WIPO + Google Details → Detalhes completos de cada WO (em batch)
    4. INPI Brasil → Patentes BR diretas
    5. FDA → Dados regulatórios
    6. ClinicalTrials → Estudos clínicos
    
    Exemplos:
    - /api/v1/search/darolutamide
    - /api/v1/search/darolutamide?country=BR
    - /api/v1/search/darolutamide?country=BR_US_JP
    - /api/v1/search/olaparib?country=BR&limit=5
    
    Parâmetros:
    - molecule: Nome da molécula (ex: darolutamide, olaparib, venetoclax)
    - country: Filtrar países (BR_US_JP_EP_CN_CA_AU_KR_IN) - opcional
    - limit: Número máximo de WO patents a buscar (padrão 10)
    
    Retorna JSON rico com:
    - executive_summary: Resumo executivo com totais
    - pubchem_data: Dados químicos completos
    - wo_patents: Lista de patentes WO com detalhes
    - br_patents_inpi: Patentes BR do INPI
    - all_patents: Agregação de todas as patentes
    - fda_data: Dados FDA
    - clinical_trials_data: Estudos clínicos
    - debug_info: Informações de debug com timings por camada
    """
    mol = molecule.strip()
    logger.info(f"\n{'='*80}")
    logger.info(f"🔬 PIPELINE COMPLETO: {mol}")
    logger.info(f"   Filtro países: {country or 'Todos'}")
    logger.info(f"{'='*80}")
    
    try:
        # Executar pipeline completo
        result = await pipeline_service.execute_full_pipeline(
            mol, 
            country_filter=country,
            limit=limit
        )
        
        logger.info(f"✅ Pipeline completo: {result.get('debug_info', {}).get('total_duration_seconds', 0)}s")
        logger.info(f"   Patentes encontradas: {result.get('executive_summary', {}).get('total_patents', 0)}")
            
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"❌ Erro no pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Pipeline execution failed",
                "message": str(e),
                "molecule": mol,
                "timestamp": datetime.now().isoformat()
            }
        )


# =============================================================================
# BATCH PROCESSING ENDPOINTS v3.1
# =============================================================================

from src.batch_service import get_batch_service, BatchStatus

# Pydantic models for batch
class BatchSearchRequest(BaseModel):
    """Request model for batch search"""
    molecules: List[str] = Field(..., description="List of molecule names to search")
    country_filter: Optional[str] = Field(None, description="Country filter (e.g., BR_US_JP)")
    limit: int = Field(10, ge=1, le=20, description="Max WO patents per molecule")


@app.post("/api/v1/batch/search")
async def create_batch_search(request: BatchSearchRequest, background_tasks: BackgroundTasks):
    """
    Create a batch job to search multiple molecules
    
    - **molecules**: List of molecule names (e.g., ["darolutamide", "olaparib", "venetoclax"])
    - **country_filter**: Optional filter BR_US_JP_EP_CN_CA_AU_KR_IN
    - **limit**: Max WO patents per molecule (1-20, default 10)
    
    Returns batch_id for tracking progress
    """
    try:
        if not request.molecules:
            raise HTTPException(status_code=400, detail="At least one molecule required")
        
        if len(request.molecules) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 molecules per batch")
        
        # Create batch job
        batch_service = get_batch_service(max_concurrent=3)
        batch_id = batch_service.create_batch(
            molecules=request.molecules,
            country_filter=request.country_filter,
            limit=request.limit
        )
        
        # Process in background
        background_tasks.add_task(batch_service.process_batch, batch_id)
        
        logger.info(f"📦 Created batch {batch_id} with {len(request.molecules)} molecules")
        
        return {
            "batch_id": batch_id,
            "status": "created",
            "total_molecules": len(request.molecules),
            "message": "Batch job created and processing started",
            "endpoints": {
                "status": f"/api/v1/batch/status/{batch_id}",
                "results": f"/api/v1/batch/results/{batch_id}",
                "cancel": f"/api/v1/batch/{batch_id}"
            },
            "estimated_time_seconds": len(request.molecules) * 50 / 3  # ~50s per molecule, 3 concurrent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create batch: {str(e)}")


@app.get("/api/v1/batch/status/{batch_id}")
async def get_batch_status(batch_id: str):
    """
    Get current status of a batch job
    
    Returns detailed progress information including:
    - Overall status (pending/processing/completed/failed)
    - Progress percentage
    - Completed/failed counts
    - Estimated time remaining
    - Status of each molecule in the batch
    """
    try:
        batch_service = get_batch_service()
        status = batch_service.get_batch_status(batch_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting batch status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/batch/results/{batch_id}")
async def get_batch_results(batch_id: str):
    """
    Get results of a batch job
    
    Returns:
    - Complete results for all successfully processed molecules
    - Error messages for failed molecules
    - Summary statistics
    
    Note: Results are only available after batch completes
    """
    try:
        batch_service = get_batch_service()
        results = batch_service.get_batch_results(batch_id)
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting batch results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/batch/{batch_id}")
async def cancel_batch(batch_id: str):
    """
    Cancel a pending or processing batch job
    
    Note: Already completed or failed batches cannot be cancelled
    """
    try:
        batch_service = get_batch_service()
        cancelled = batch_service.cancel_batch(batch_id)
        
        if not cancelled:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch {batch_id} cannot be cancelled (not found or already completed)"
            )
        
        logger.info(f"🚫 Cancelled batch {batch_id}")
        
        return {
            "batch_id": batch_id,
            "status": "cancelled",
            "message": "Batch job cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cancelling batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/batch/list")
async def list_batches(status: Optional[str] = None):
    """
    List all batch jobs
    
    - **status**: Optional filter by status (pending/processing/completed/failed/cancelled)
    
    Returns list of batch summaries sorted by creation time (newest first)
    """
    try:
        batch_service = get_batch_service()
        
        # Validate status filter if provided
        status_filter = None
        if status:
            try:
                status_filter = BatchStatus(status.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: pending, processing, completed, failed, cancelled"
                )
        
        batches = batch_service.list_batches(status_filter=status_filter)
        
        return {
            "total_batches": len(batches),
            "filter": status if status else "all",
            "batches": batches
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch/cleanup")
async def cleanup_old_batches(max_age_hours: int = 24):
    """
    Remove old completed/failed batch jobs
    
    - **max_age_hours**: Maximum age in hours to keep jobs (default 24)
    
    Helps manage memory by removing old job data
    """
    try:
        if max_age_hours < 1:
            raise HTTPException(status_code=400, detail="max_age_hours must be at least 1")
        
        batch_service = get_batch_service()
        deleted_count = batch_service.cleanup_old_jobs(max_age_hours=max_age_hours)
        
        logger.info(f"🗑️  Cleaned up {deleted_count} old batch jobs")
        
        return {
            "deleted_count": deleted_count,
            "max_age_hours": max_age_hours,
            "message": f"Cleaned up {deleted_count} batch jobs older than {max_age_hours} hours"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error cleaning up batches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# END BATCH PROCESSING ENDPOINTS
# =============================================================================


# Startup/Shutdown
@app.on_event("startup")
async def startup_event():
    """Startup"""
    logger.info("🚀 Pharmyrus WIPO API iniciando...")
    logger.info(f"📦 Cache TTL: {_cache_ttl}s")
    logger.info("🔄 Batch processing enabled with max 3 concurrent searches")
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
