"""
服务层包

导出所有服务类和协调层
"""

from .competitor_detection_service import CompetitorDetectionService
from .scraping_orchestrator import (
    ScrapingOrchestrator,
    ScrapingMode,
    OrchestrationConfig,
    get_global_scraping_orchestrator,
    reset_global_scraping_orchestrator
)

__all__ = [
    'CompetitorDetectionService',
    'ScrapingOrchestrator',
    'ScrapingMode',
    'OrchestrationConfig',
    'get_global_scraping_orchestrator',
    'reset_global_scraping_orchestrator'
]
