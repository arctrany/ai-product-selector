"""Logging utilities for workflow engine."""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional



def setup_logging(log_level: str = "INFO", log_dir: Optional[str] = None, enable_console: bool = True) -> None:
    """Setup structured logging for the workflow engine."""

    # Configure standard library logging with console output
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Get log directory from configuration
    if log_dir is None:
        from ..config import get_config
        config = get_config()
        log_dir_path = config.get_logging_directory_path()
        log_dir = str(log_dir_path)

    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    handlers = []
    if enable_console:
        handlers.append(logging.StreamHandler(sys.stdout))

    handlers.append(logging.FileHandler(
        os.path.join(log_dir, "workflow_engine.log"),
        encoding='utf-8'
    ))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

    # Standard logging is already configured above

def get_logger(name: str):
    """Get a logger instance."""
    return logging.getLogger(name)

class WorkflowLogger:
    """Workflow-specific logger with file output, rotation, console output, and WebSocket push."""

    def __init__(self, thread_id: str, log_dir: Optional[str] = None, enable_console: bool = True):
        self.thread_id = thread_id

        # Get log directory from configuration
        if log_dir is None:
            from ..config import get_config
            config = get_config()
            log_dir_path = config.get_logging_directory_path()
            self.log_dir = log_dir_path / "runs"
        else:
            self.log_dir = Path(log_dir)

        self.log_file = self.log_dir / thread_id / "logs.jsonl"
        self.enable_console = enable_console

        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.logger = get_logger(f"workflow.{thread_id}")

        # Setup console handler if enabled and not already present
        if self.enable_console and not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            self._setup_console_handler()

        # WebSocket connection manager reference (lazy loaded to avoid circular imports)
        self._connection_manager = None

    def _setup_console_handler(self):
        """Setup console handler for real-time log output."""
        # For structlog, we rely on the global configuration
        pass

    def _get_connection_manager(self):
        """Lazy load connection manager to avoid circular imports."""
        if self._connection_manager is None:
            try:
                from ..api.workflow_ws import get_connection_manager
                self._connection_manager = get_connection_manager()
            except ImportError:
                # Connection manager not available, skip WebSocket push
                self._connection_manager = None
        return self._connection_manager

    def _push_log_to_websocket(self, log_entry: Dict[str, Any]):
        """Push log entry to WebSocket connections asynchronously."""
        connection_manager = self._get_connection_manager()
        if connection_manager is None:
            return

        # Create WebSocket message
        ws_message = {
            "type": "log",
            "data": log_entry,
            "timestamp": log_entry.get("ts", datetime.utcnow().isoformat())
        }

        # Try to send message using the sync method for cross-thread compatibility
        try:
            connection_manager.send_message_sync(self.thread_id, ws_message)
        except Exception as e:
            # Don't let WebSocket errors break logging
            print(f"Warning: Failed to push log to WebSocket: {e}")
            pass

    def log(self, level: str, message: str, node_id: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None) -> None:
        """Log a message to both structured logger, file, console, and WebSocket."""

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

        # Format message for console output
        if self.enable_console:
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            level_str = f"[{level.upper()}]"

            if node_id:
                console_message = f"[{timestamp}] {level_str} 工作流节点执行: {node_id} - {message}"
            else:
                console_message = f"[{timestamp}] {level_str} {message}"

            # Print to console directly for immediate visibility
            print(console_message)
            sys.stdout.flush()

        # Push to WebSocket for real-time frontend updates
        self._push_log_to_websocket(log_entry)

        # Log to standard logger
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        # Format message with extra information for standard logging
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

    def debug(self, message: str, node_id: Optional[str] = None,
              context: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        self.log("DEBUG", message, node_id, context)

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

# Initialize logging on module import with console output enabled by default
setup_logging(enable_console=True)