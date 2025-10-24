"""Custom exceptions and error handlers for API."""

from typing import Any, Dict
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowEngineException(Exception):
    """Base exception for workflow engine."""

    def __init__(self, message: str, status_code: int = 500, details: Dict[str, Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class FlowNotFoundException(WorkflowEngineException):
    """Exception raised when flow is not found."""

    def __init__(self, flow_id: str, message: str = None):
        self.flow_id = flow_id
        message = message or f"Flow '{flow_id}' not found"
        super().__init__(message, status_code=404, details={"flow_id": flow_id})


class WorkflowNotFoundException(WorkflowEngineException):
    """Exception raised when workflow is not found."""

    def __init__(self, thread_id: str, message: str = None):
        self.thread_id = thread_id
        message = message or f"Workflow '{thread_id}' not found"
        super().__init__(message, status_code=404, details={"thread_id": thread_id})


class AppNotFoundException(WorkflowEngineException):
    """Exception raised when application is not found."""

    def __init__(self, app_name: str, message: str = None):
        self.app_name = app_name
        message = message or f"Application '{app_name}' not found"
        super().__init__(message, status_code=404, details={"app_name": app_name})


class ValidationException(WorkflowEngineException):
    """Exception raised for validation errors."""

    def __init__(self, message: str, field: str = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, status_code=400, details=details)


# Error handlers
async def workflow_engine_exception_handler(request: Request, exc: WorkflowEngineException):
    """Handle WorkflowEngineException."""
    logger.error(f"WorkflowEngineException: {exc.message}", extra={"details": exc.details})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "type": "HTTPException"
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.errors(),
            "type": "ValidationError"
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "InternalError"
        }
    )


def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI app."""
    app.add_exception_handler(WorkflowEngineException, workflow_engine_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    logger.info("Exception handlers configured")
