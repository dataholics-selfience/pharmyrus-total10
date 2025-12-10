#!/usr/bin/env python3
"""
Testes básicos para WIPO Crawler
"""

import asyncio
import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.wipo_crawler import WIPOCrawler
from src.crawler_pool import WIPOCrawlerPool


async def test_single_patent():
    """Teste de busca única"""
    print("\n🧪 Teste 1: Busca Única")
    print("="*50)
    
    async with WIPOCrawler() as crawler:
        result = await crawler.fetch_patent('WO2018162793')
        
        assert result['publicacao'] == 'WO2018162793'
        assert result.get('titulo') is not None
        assert result.get('titular') is not None
        assert 'BR' in result.get('paises_familia', [])
        
        print(f"✅ Título: {result['titulo'][:50]}...")
        print(f"✅ Titular: {result['titular']}")
        print(f"✅ Família: {len(result['paises_familia'])} países")
        print(f"✅ Brasil na família: {'Sim' if 'BR' in result['paises_familia'] else 'Não'}")
        print(f"✅ Duração: {result['duracao_segundos']}s")


async def test_batch_sequential():
    """Teste de busca em lote sequencial"""
    print("\n🧪 Teste 2: Busca em Lote (Sequencial)")
    print("="*50)
    
    wo_list = ['WO2018162793', 'WO2016168716']
    
    async with WIPOCrawler() as crawler:
        results = await crawler.fetch_multiple_patents(wo_list)
        
        assert len(results) == len(wo_list)
        success = sum(1 for r in results if r.get('titulo'))
        
        print(f"✅ Total: {len(results)}")
        print(f"✅ Sucesso: {success}/{len(results)}")


async def test_pool():
    """Teste de pooling"""
    print("\n🧪 Teste 3: Pool de Crawlers")
    print("="*50)
    
    wo_list = ['WO2018162793', 'WO2016168716', 'WO2015095053']
    
    async with WIPOCrawlerPool(pool_size=2) as pool:
        results = await pool.process_batch(wo_list)
        
        assert len(results) == len(wo_list)
        success = sum(1 for r in results if r.get('titulo'))
        
        print(f"✅ Total: {len(results)}")
        print(f"✅ Sucesso: {success}/{len(results)}")
        
        stats = pool.get_stats()
        print(f"✅ Taxa de sucesso: {stats['success_rate']:.1f}%")


async def run_tests():
    """Executa todos os testes"""
    print("\n" + "="*50)
    print("PHARMYRUS WIPO CRAWLER - TESTES")
    print("="*50)
    
    try:
        await test_single_patent()
        await asyncio.sleep(3)
        
        await test_batch_sequential()
        await asyncio.sleep(3)
        
        await test_pool()
        
        print("\n" + "="*50)
        print("✅ TODOS OS TESTES PASSARAM!")
        print("="*50 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
