"""Automatic data cleanup scheduler for workflow engine."""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Optional

from ..storage.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataCleanupScheduler:
    """Scheduler for automatic data cleanup tasks."""
    
    def __init__(self, db_manager: DatabaseManager, retention_days: int = 30):
        self.db_manager = db_manager
        self.retention_days = retention_days
        self.cleanup_interval_hours = 24  # Run cleanup daily
        self.running = False
        self.cleanup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self):
        """Start the cleanup scheduler."""
        if self.running:
            logger.warning("Cleanup scheduler is already running")
            return
        
        self.running = True
        self._stop_event.clear()
        self.cleanup_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.cleanup_thread.start()
        logger.info(f"Data cleanup scheduler started (retention: {self.retention_days} days, interval: {self.cleanup_interval_hours}h)")
    
    def stop(self):
        """Stop the cleanup scheduler."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5.0)
        
        logger.info("Data cleanup scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        # Run initial cleanup on startup
        self._perform_cleanup()
        
        while self.running and not self._stop_event.is_set():
            # Wait for next cleanup interval
            if self._stop_event.wait(timeout=self.cleanup_interval_hours * 3600):
                break  # Stop event was set
            
            if self.running:
                self._perform_cleanup()
    
    def _perform_cleanup(self):
        """Perform the actual cleanup operation."""
        try:
            logger.info("Starting scheduled data cleanup")
            
            # Get stats before cleanup
            stats_before = self.db_manager.get_data_retention_stats()
            
            # Perform cleanup
            cleanup_result = self.db_manager.cleanup_old_data(self.retention_days)
            
            # Clean up orphaned signals
            orphaned_signals = self.db_manager.cleanup_orphaned_signals()
            if orphaned_signals > 0:
                cleanup_result["orphaned_signals_deleted"] = orphaned_signals
            
            # Get stats after cleanup
            stats_after = self.db_manager.get_data_retention_stats()
            
            # Log cleanup summary
            logger.info(f"Scheduled cleanup completed: {cleanup_result}")
            logger.info(f"Data retention stats - Before: {stats_before['total_runs']} runs, {stats_before['total_signals']} signals")
            logger.info(f"Data retention stats - After: {stats_after['total_runs']} runs, {stats_after['total_signals']} signals")
            
        except Exception as e:
            logger.error(f"Scheduled cleanup failed: {e}")
    
    def force_cleanup(self) -> dict:
        """Force immediate cleanup and return results."""
        logger.info("Forcing immediate data cleanup")
        
        try:
            # Get stats before cleanup
            stats_before = self.db_manager.get_data_retention_stats()
            
            # Perform cleanup
            cleanup_result = self.db_manager.cleanup_old_data(self.retention_days)
            
            # Clean up orphaned signals
            orphaned_signals = self.db_manager.cleanup_orphaned_signals()
            if orphaned_signals > 0:
                cleanup_result["orphaned_signals_deleted"] = orphaned_signals
            
            # Get stats after cleanup
            stats_after = self.db_manager.get_data_retention_stats()
            
            # Return comprehensive results
            return {
                "cleanup_result": cleanup_result,
                "stats_before": stats_before,
                "stats_after": stats_after,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
            raise

# Global scheduler instance
_cleanup_scheduler: Optional[DataCleanupScheduler] = None

def get_cleanup_scheduler() -> Optional[DataCleanupScheduler]:
    """Get the global cleanup scheduler instance."""
    return _cleanup_scheduler

def initialize_cleanup_scheduler(db_manager: DatabaseManager, retention_days: int = 30, auto_start: bool = True) -> DataCleanupScheduler:
    """Initialize and optionally start the global cleanup scheduler."""
    global _cleanup_scheduler
    
    if _cleanup_scheduler is not None:
        _cleanup_scheduler.stop()
    
    _cleanup_scheduler = DataCleanupScheduler(db_manager, retention_days)
    
    if auto_start:
        _cleanup_scheduler.start()
    
    return _cleanup_scheduler

def shutdown_cleanup_scheduler():
    """Shutdown the global cleanup scheduler."""
    global _cleanup_scheduler
    
    if _cleanup_scheduler is not None:
        _cleanup_scheduler.stop()
        _cleanup_scheduler = None