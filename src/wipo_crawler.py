#!/usr/bin/env python3
"""
WIPO Patentscope Advanced Crawler
Pharmyrus - Patent Intelligence Platform
"""

import asyncio
import random
import time
from typing import Dict, List, Optional, Any
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import logging

logger = logging.getLogger(__name__)


class WIPOCrawler:
    """Crawler robusto para WIPO Patentscope com pooling e retry"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, max_retries: int = 5, timeout: int = 60000, headless: bool = True):
        self.max_retries = max_retries
        self.timeout = timeout
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def initialize(self):
        """Inicializa o browser"""
        logger.info("🚀 Inicializando Playwright...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-web-security',
                '--window-size=1920,1080'
            ]
        )
        
        logger.info("✅ Browser inicializado")
        
    async def close(self):
        """Fecha o browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def _create_stealth_page(self) -> Page:
        """Cria página com configurações stealth"""
        context = await self.browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            window.chrome = { runtime: {} };
        """)
        
        return await context.new_page()
    
    async def _wait_for_load(self, page: Page, selectors: List[str], timeout: int = 30000):
        """Espera inteligente por elementos"""
        start = time.time()
        
        while time.time() - start < timeout / 1000:
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000, state='visible')
                    return True
                except PlaywrightTimeout:
                    continue
            await asyncio.sleep(1)
        
        return False
    
    async def _extract_data(self, page: Page, wo_number: str) -> Dict[str, Any]:
        """Extrai dados da patente"""
        data = {
            'fonte': 'WIPO',
            'pais': 'WO',
            'publicacao': wo_number,
            'pedido': None,
            'titulo': None,
            'titular': None,
            'datas': {'deposito': None, 'publicacao': None, 'prioridade': None},
            'inventores': [],
            'cpc_ipc': [],
            'resumo': None,
            'paises_familia': [],
            'documentos': {
                'pdf_link': None,
                'patentscope_link': f"https://patentscope.wipo.int/search/en/detail.jsf?docId={wo_number}"
            },
            'worldwide_applications': {}
        }
        
        try:
            # Título
            title_elem = await page.query_selector('h3.tab_title, .patent-title, h1')
            if title_elem:
                data['titulo'] = (await title_elem.inner_text()).strip()
                
            # Resumo
            abstract_elem = await page.query_selector('div.abstract, .patent-abstract, #abstract')
            if abstract_elem:
                data['resumo'] = (await abstract_elem.inner_text()).strip()
                
            # Titular
            for selector in ['div.applicant', 'td:has-text("Applicant")+td']:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        data['titular'] = (await elem.inner_text()).strip()
                        break
                except:
                    continue
                    
            # Inventores
            inventor_elems = await page.query_selector_all('.inventor, td:has-text("Inventor")+td')
            for elem in inventor_elems:
                inv = (await elem.inner_text()).strip()
                if inv and inv not in data['inventores']:
                    data['inventores'].append(inv)
                    
            # Datas
            for selector in ['td:has-text("Filing Date")+td', 'td:has-text("Application Date")+td']:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        data['datas']['deposito'] = (await elem.inner_text()).strip()
                        break
                except:
                    continue
                    
            # CPC/IPC
            ipc_elems = await page.query_selector_all('.ipc, .cpc, td:has-text("IPC")+td, td:has-text("CPC")+td')
            for elem in ipc_elems:
                ipc_text = (await elem.inner_text()).strip()
                if ipc_text:
                    codes = [c.strip() for c in ipc_text.replace(';', ',').split(',')]
                    data['cpc_ipc'].extend(codes)
            data['cpc_ipc'] = list(set(data['cpc_ipc']))
            
            # Família - clica na aba National Phase
            try:
                national_tab = await page.query_selector('a:has-text("National Phase"), button:has-text("National Phase")')
                if national_tab:
                    await national_tab.click()
                    await asyncio.sleep(2)
            except:
                pass
                
            # Extrai países
            country_elems = await page.query_selector_all('table.nationalPhase td:first-child, .country-code')
            for elem in country_elems:
                country = (await elem.inner_text()).strip()
                if country and len(country) == 2 and country not in data['paises_familia']:
                    data['paises_familia'].append(country)
                    
            # Cria worldwide_applications
            for country in data['paises_familia']:
                if country not in data['worldwide_applications']:
                    data['worldwide_applications'][country] = []
                    
            # Link PDF
            pdf_link = await page.query_selector('a[href*=".pdf"], a:has-text("PDF")')
            if pdf_link:
                href = await pdf_link.get_attribute('href')
                if href:
                    data['documentos']['pdf_link'] = href if href.startswith('http') else f"https://patentscope.wipo.int{href}"
                    
        except Exception as e:
            logger.error(f"❌ Erro na extração: {e}")
            
        return data
    
    async def fetch_patent(self, wo_number: str, retry_count: int = 0) -> Dict[str, Any]:
        """
        Busca dados de uma patente WO
        
        Args:
            wo_number: Número WO (ex: WO2018162793)
            retry_count: Contador de tentativas
            
        Returns:
            Dicionário com dados da patente
        """
        start_time = time.time()
        wo_clean = wo_number.replace('WO', '').replace(' ', '').replace('/', '')
        url = f"https://patentscope.wipo.int/search/en/detail.jsf?docId=WO{wo_clean}"
        
        logger.info(f"🔍 Tentativa {retry_count + 1}/{self.max_retries} para {wo_number}")
        
        page = None
        
        try:
            page = await self._create_stealth_page()
            await asyncio.sleep(random.uniform(1, 3))
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=self.timeout)
            
            if not response or response.status != 200:
                raise Exception(f"Status HTTP: {response.status if response else 'No response'}")
                
            logger.info(f"✅ Página carregada (status {response.status})")
            
            # Espera elementos chave
            key_selectors = ['h3.tab_title', '.patent-title', 'div.abstract', 'h1']
            await self._wait_for_load(page, key_selectors, timeout=20000)
            
            await asyncio.sleep(random.uniform(2, 4))
            
            # Scroll
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
            
            # Extrai dados
            data = await self._extract_data(page, wo_number)
            data['duracao_segundos'] = round(time.time() - start_time, 2)
            
            if not data['titulo'] and not data['resumo'] and not data['titular']:
                raise Exception("Nenhum dado essencial extraído")
                
            logger.info(f"✅ Sucesso! Duração: {data['duracao_segundos']}s")
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro: {e}")
            
            if retry_count < self.max_retries - 1:
                wait_time = (2 ** retry_count) + random.uniform(0, 1)
                logger.info(f"⏳ Retry em {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                        
                return await self.fetch_patent(wo_number, retry_count + 1)
            else:
                logger.error(f"❌ Falha após {self.max_retries} tentativas")
                return {
                    'fonte': 'WIPO',
                    'pais': 'WO',
                    'publicacao': wo_number,
                    'erro': str(e),
                    'status': 'FALHA',
                    'duracao_segundos': round(time.time() - start_time, 2),
                    'documentos': {'patentscope_link': url},
                    'worldwide_applications': {}
                }
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass
    
    async def fetch_multiple_patents(self, wo_numbers: List[str]) -> List[Dict[str, Any]]:
        """Busca múltiplas patentes"""
        results = []
        
        for i, wo in enumerate(wo_numbers, 1):
            logger.info(f"\n📍 Patente {i}/{len(wo_numbers)}: {wo}")
            
            result = await self.fetch_patent(wo)
            results.append(result)
            
            if i < len(wo_numbers):
                delay = random.uniform(3, 6)
                await asyncio.sleep(delay)
                
        return results
