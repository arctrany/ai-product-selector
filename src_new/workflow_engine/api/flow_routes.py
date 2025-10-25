"""Flow management API routes."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .dependencies import engine_dependency, db_manager_dependency, workflow_control_dependency
from .exceptions import FlowNotFoundException, ValidationException
from ..core.engine import WorkflowEngine
from ..core.models import WorkflowDefinition
from ..storage.database import DatabaseManager
from ..sdk.control import WorkflowControl
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Request/Response models
class CreateFlowRequest(BaseModel):
    name: str
    definition: WorkflowDefinition
    version: str = "1.0.0"

class StartFlowRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None

class FlowResponse(BaseModel):
    flow_version_id: int
    name: str
    version: str
    status: str

class StartFlowResponse(BaseModel):
    thread_id: str
    status: str
    message: str

def create_flow_router() -> APIRouter:
    """Create flow management routes."""
    router = APIRouter(prefix="/flows", tags=["flows"])

    @router.post("", response_model=FlowResponse)
    async def create_flow(
        request: CreateFlowRequest,
        engine: WorkflowEngine = Depends(engine_dependency)
    ):
        """Create a new workflow."""
        try:
            flow_version_id = engine.create_flow(
                name=request.name,
                definition=request.definition,
                version=request.version
            )

            logger.info(f"Created flow: {request.name} v{request.version}")

            return FlowResponse(
                flow_version_id=flow_version_id,
                name=request.name,
                version=request.version,
                status="created"
            )

        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            raise ValidationException(f"Failed to create flow: {str(e)}")

    @router.post("/{flow_version_id}/publish")
    async def publish_flow(
        flow_version_id: int,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Publish a flow version."""
        try:
            success = db_manager.publish_flow_version(flow_version_id)
            if not success:
                raise FlowNotFoundException(str(flow_version_id), "Flow version not found")

            logger.info(f"Published flow version: {flow_version_id}")
            return {"flow_version_id": flow_version_id, "status": "published"}

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to publish flow: {e}")
            raise ValidationException(f"Failed to publish flow: {str(e)}")

    @router.get("/{flow_id}")
    async def get_flow(
        flow_id: str,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Get flow information."""
        try:
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            return flow

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get flow {flow_id}: {e}")
            raise ValidationException(f"Failed to get flow: {str(e)}")

    @router.post("/{flow_id}/start", response_model=StartFlowResponse)
    async def start_flow_latest_version(
        flow_id: str,
        request: StartFlowRequest,
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Start workflow execution by flow ID using the latest version."""
        try:
            # Validate flow exists
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get the latest published version for this flow
            flow_version = db_manager.get_latest_flow_version(flow['flow_id'])
            if not flow_version:
                raise ValidationException(f"No published version found for flow {flow_id}")

            flow_version_id = flow_version['flow_version_id']

            # Start the workflow using the control
            thread_id = control.start_workflow(
                flow_version_id=flow_version_id,
                input_data=request.input_data,
                thread_id=request.thread_id
            )

            logger.info(f"Started workflow {flow_id} (latest version) with thread_id: {thread_id}")

            return StartFlowResponse(
                thread_id=thread_id,
                status="started",
                message=f"Workflow {flow_id} started successfully with latest version"
            )

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to start workflow {flow_id}: {e}")
            raise ValidationException(f"Failed to start workflow: {str(e)}")

    @router.post("/{flow_id_version}/start", response_model=StartFlowResponse)
    async def start_flow_specific_version(
        flow_id_version: str,
        request: StartFlowRequest,
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Start workflow execution by flow ID with specific version (format: flow_id-version)."""
        try:
            # Parse flow_id and version from flow_id_version parameter
            def parse_flow_version_id(flow_version_param: str) -> tuple[str, str]:
                """Parse flow_id-version parameter into flow_id and version."""
                if '-' in flow_version_param:
                    # Try to find version pattern from the end
                    parts = flow_version_param.split('-')

                    # Look for version-like patterns from the end
                    for i in range(len(parts) - 1, 0, -1):
                        potential_version = '-'.join(parts[i:])
                        # Check if this looks like a version (starts with digit and contains dots)
                        if potential_version and potential_version[0].isdigit() and ('.' in potential_version):
                            flow_id = '-'.join(parts[:i])
                            return flow_id, potential_version

                    # Fallback: check if last part is numeric
                    if parts[-1].isdigit():
                        return '-'.join(parts[:-1]), parts[-1]

                # If no version pattern found, treat as flow_id only
                raise ValidationException(f"Invalid flow_id-version format: {flow_version_param}")

            flow_id, version = parse_flow_version_id(flow_id_version)

            # Validate flow exists
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get specific version for this flow
            flow_version = db_manager.get_flow_version_by_version(flow['flow_id'], version)
            if not flow_version:
                raise ValidationException(f"Version {version} not found for flow {flow_id}")

            flow_version_id = flow_version['flow_version_id']

            # Start the workflow using the control
            thread_id = control.start_workflow(
                flow_version_id=flow_version_id,
                input_data=request.input_data,
                thread_id=request.thread_id
            )

            logger.info(f"Started workflow {flow_id} v{version} with thread_id: {thread_id}")

            return StartFlowResponse(
                thread_id=thread_id,
                status="started",
                message=f"Workflow {flow_id} v{version} started successfully"
            )

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to start workflow {flow_id_version}: {e}")
            raise ValidationException(f"Failed to start workflow: {str(e)}")

    return router