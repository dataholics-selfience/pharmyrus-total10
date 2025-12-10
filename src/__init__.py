"""
Pharmyrus WIPO Crawler
Patent Intelligence Platform
"""

__version__ = "1.0.0"
__author__ = "Pharmyrus Team"

from .wipo_crawler import WIPOCrawler
from .crawler_pool import WIPOCrawlerPool

__all__ = ['WIPOCrawler', 'WIPOCrawlerPool']
