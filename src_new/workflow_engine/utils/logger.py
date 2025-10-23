
"""Logging utilities for workflow engine."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


def setup_logging(log_level: str = "INFO", log_dir: Optional[str] = None) -> None:
    """Setup structured logging for the workflow engine."""

    # Configure standard library logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if HAS_STRUCTLOG:
        # Configure structlog if available
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


def get_logger(name: str):
    """Get a logger instance (structured if available, standard otherwise)."""
    if HAS_STRUCTLOG:
        return structlog.get_logger(name)
    else:
        return logging.getLogger(name)


class WorkflowLogger:
    """Workflow-specific logger with file output and rotation."""
    
    def __init__(self, thread_id: str, log_dir: Optional[str] = None):
        self.thread_id = thread_id
        self.log_dir = Path(log_dir or os.path.expanduser("~/.ren/runs"))
        self.log_file = self.log_dir / thread_id / "logs.jsonl"
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger = get_logger(f"workflow.{thread_id}")
    
    def log(self, level: str, message: str, node_id: Optional[str] = None, 
            context: Optional[Dict[str, Any]] = None) -> None:
        """Log a message to both structured logger and file."""
        
        log_entry = {
            "ts": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "thread_id": self.thread_id,
            "node_id": node_id,
            "message": message,
            "context": context or {}
        }
        
        # Write to file
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # Log to structured logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        if HAS_STRUCTLOG:
            # structlog supports extra parameters
            log_method(message, node_id=node_id, context=context)
        else:
            # standard logging doesn't support extra parameters in the same way
            extra_info = f" [node_id={node_id}]" if node_id else ""
            context_info = f" [context={context}]" if context else ""
            log_method(f"{message}{extra_info}{context_info}")
    
    def info(self, message: str, node_id: Optional[str] = None, 
             context: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self.log("INFO", message, node_id, context)
    
    def warning(self, message: str, node_id: Optional[str] = None, 
                context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self.log("WARNING", message, node_id, context)
    
    def error(self, message: str, node_id: Optional[str] = None, 
              context: Optional[Dict[str, Any]] = None) -> None:
        """Log error message."""
        self.log("ERROR", message, node_id, context)
    
    def rotate_logs(self, max_size_mb: int = 10) -> None:
        """Rotate log file if it exceeds max size."""
        if not self.log_file.exists():
            return
        
        file_size_mb = self.log_file.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            # Rotate to .1, .2, etc.
            counter = 1
            while True:
                rotated_file = self.log_file.with_suffix(f".{counter}")
                if not rotated_file.exists():
                    self.log_file.rename(rotated_file)
                    break
                counter += 1


# Initialize logging on module import
setup_logging()