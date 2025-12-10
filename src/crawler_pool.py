#!/usr/bin/env python3
"""
WIPO Crawler Pool Manager
Gerencia múltiplos crawlers para paralelização eficiente
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .wipo_crawler import WIPOCrawler

logger = logging.getLogger(__name__)


class WIPOCrawlerPool:
    """Pool de crawlers WIPO para processamento paralelo"""
    
    def __init__(
        self,
        pool_size: int = 3,
        max_retries: int = 5,
        timeout: int = 60000,
        max_queue_size: int = 100
    ):
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_queue_size = max_queue_size
        
        self.crawlers: List[WIPOCrawler] = []
        self.active_tasks = 0
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        
        self._queue: asyncio.Queue = None
        self._results: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def initialize(self):
        """Inicializa o pool de crawlers"""
        logger.info(f"🚀 Inicializando pool com {self.pool_size} crawlers...")
        
        self._queue = asyncio.Queue(maxsize=self.max_queue_size)
        
        # Inicializa crawlers
        for i in range(self.pool_size):
            crawler = WIPOCrawler(
                max_retries=self.max_retries,
                timeout=self.timeout,
                headless=True
            )
            await crawler.initialize()
            self.crawlers.append(crawler)
            logger.info(f"✅ Crawler {i+1}/{self.pool_size} pronto")
            
        logger.info(f"✅ Pool inicializado com {len(self.crawlers)} crawlers")
        
    async def close(self):
        """Fecha todos os crawlers"""
        logger.info("🔒 Fechando pool...")
        
        for crawler in self.crawlers:
            try:
                await crawler.close()
            except Exception as e:
                logger.error(f"Erro ao fechar crawler: {e}")
                
        logger.info("✅ Pool fechado")
        
    async def _worker(self, worker_id: int, crawler: WIPOCrawler):
        """Worker que processa itens da fila"""
        logger.info(f"👷 Worker {worker_id} iniciado")
        
        while True:
            try:
                # Pega item da fila
                wo_number = await self._queue.get()
                
                if wo_number is None:  # Sinal de parada
                    self._queue.task_done()
                    break
                    
                async with self._lock:
                    self.active_tasks += 1
                    
                logger.info(f"👷 Worker {worker_id} processando: {wo_number}")
                
                # Processa patente
                start_time = datetime.now()
                result = await crawler.fetch_patent(wo_number)
                duration = (datetime.now() - start_time).total_seconds()
                
                # Adiciona metadados
                result['worker_id'] = worker_id
                result['processed_at'] = datetime.now().isoformat()
                
                # Salva resultado
                async with self._lock:
                    self._results.append(result)
                    self.total_processed += 1
                    
                    if result.get('titulo'):
                        self.total_success += 1
                        logger.info(f"✅ Worker {worker_id} sucesso: {wo_number} ({duration:.1f}s)")
                    else:
                        self.total_failed += 1
                        logger.warning(f"⚠️ Worker {worker_id} falha: {wo_number}")
                        
                    self.active_tasks -= 1
                    
                self._queue.task_done()
                
            except Exception as e:
                logger.error(f"❌ Worker {worker_id} erro: {e}")
                async with self._lock:
                    self.active_tasks -= 1
                self._queue.task_done()
                
        logger.info(f"👷 Worker {worker_id} finalizado")
        
    async def process_batch(
        self,
        wo_numbers: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Processa lote de patentes em paralelo
        
        Args:
            wo_numbers: Lista de números WO
            progress_callback: Função callback para progresso (opcional)
            
        Returns:
            Lista de resultados
        """
        logger.info(f"🎯 Processando lote de {len(wo_numbers)} patentes")
        
        # Reseta estado
        self._results = []
        self.total_processed = 0
        self.total_success = 0
        self.total_failed = 0
        
        # Adiciona itens na fila
        for wo in wo_numbers:
            await self._queue.put(wo)
            
        # Inicia workers
        workers = [
            asyncio.create_task(self._worker(i, crawler))
            for i, crawler in enumerate(self.crawlers, 1)
        ]
        
        # Monitora progresso
        if progress_callback:
            asyncio.create_task(self._monitor_progress(progress_callback, len(wo_numbers)))
            
        # Aguarda conclusão
        await self._queue.join()
        
        # Envia sinal de parada para workers
        for _ in self.crawlers:
            await self._queue.put(None)
            
        # Aguarda workers finalizarem
        await asyncio.gather(*workers)
        
        # Estatísticas finais
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 ESTATÍSTICAS FINAIS")
        logger.info(f"{'='*60}")
        logger.info(f"Total processado: {self.total_processed}")
        logger.info(f"Sucesso: {self.total_success} ({self.total_success/max(1, self.total_processed)*100:.1f}%)")
        logger.info(f"Falhas: {self.total_failed} ({self.total_failed/max(1, self.total_processed)*100:.1f}%)")
        logger.info(f"{'='*60}\n")
        
        return self._results
        
    async def _monitor_progress(self, callback: callable, total: int):
        """Monitora e reporta progresso"""
        while self.total_processed < total:
            progress = {
                'total': total,
                'processed': self.total_processed,
                'success': self.total_success,
                'failed': self.total_failed,
                'active': self.active_tasks,
                'percentage': (self.total_processed / total * 100) if total > 0 else 0
            }
            
            await callback(progress)
            await asyncio.sleep(2)
            
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do pool"""
        return {
            'pool_size': self.pool_size,
            'active_tasks': self.active_tasks,
            'total_processed': self.total_processed,
            'total_success': self.total_success,
            'total_failed': self.total_failed,
            'success_rate': (self.total_success / max(1, self.total_processed) * 100),
            'queue_size': self._queue.qsize() if self._queue else 0
        }


# Exemplo de uso
async def example_usage():
    """Exemplo de como usar o pool"""
    
    wo_numbers = [
        'WO2018162793',
        'WO2016168716',
        'WO2015095053',
        'WO2011092143',
        'WO2007129058'
    ]
    
    async def progress_callback(progress):
        print(f"Progresso: {progress['percentage']:.1f}% "
              f"({progress['processed']}/{progress['total']}) - "
              f"Ativos: {progress['active']}")
    
    async with WIPOCrawlerPool(pool_size=3) as pool:
        results = await pool.process_batch(wo_numbers, progress_callback)
        
        print(f"\n✅ Processamento concluído!")
        print(f"Resultados: {len(results)}")
        
        for result in results:
            print(f"  - {result['publicacao']}: {result.get('titulo', 'N/A')[:50]}...")


if __name__ == "__main__":
    asyncio.run(example_usage())
