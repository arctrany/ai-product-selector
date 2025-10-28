"""Flow management API routes."""

from typing import Any, Dict, Optional, List
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


class UpdateFlowRequest(BaseModel):
    definition: WorkflowDefinition
    version: Optional[str] = None
    auto_increment_version: bool = True


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
    flow_id: Optional[str] = None
    version: Optional[str] = None


class FlowVersionResponse(BaseModel):
    flow_version_id: int
    flow_id: int
    version: str
    published: bool
    created_at: Optional[str] = None


class FlowListResponse(BaseModel):
    flows: List[Dict[str, Any]]
    total: int


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

    @router.put("/{flow_id}", response_model=FlowResponse)
    async def update_flow(
            flow_id: str,
            request: UpdateFlowRequest,
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Update an existing workflow definition with version upgrade."""
        try:
            # Get existing flow
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get latest version to determine next version
            latest_version = db_manager.get_latest_flow_version(flow['flow_id'])

            if request.version:
                new_version = request.version
            elif request.auto_increment_version and latest_version:
                # Auto-increment version (simple semantic versioning)
                current_version = latest_version['version']
                try:
                    # Parse version like "1.2.3" and increment patch version
                    version_parts = current_version.split('.')
                    if len(version_parts) >= 3:
                        version_parts[2] = str(int(version_parts[2]) + 1)
                    elif len(version_parts) == 2:
                        version_parts.append('1')
                    else:
                        version_parts = ['1', '0', '1']
                    new_version = '.'.join(version_parts)
                except (ValueError, IndexError):
                    # Fallback to timestamp-based versioning
                    from datetime import datetime
                    new_version = f"1.0.{int(datetime.utcnow().timestamp())}"
            else:
                new_version = "1.0.0"

            # Create new flow version with updated definition
            flow_version_id = db_manager.create_flow_version(
                flow_id=flow['flow_id'],
                version=new_version,
                dsl_json=request.definition.dict()
            )

            # Publish the new version
            db_manager.publish_flow_version(flow_version_id)

            logger.info(f"Updated flow: {flow_id} to version {new_version}")

            return FlowResponse(
                flow_version_id=flow_version_id,
                name=flow_id,
                version=new_version,
                status="updated"
            )

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update flow {flow_id}: {e}")
            raise ValidationException(f"Failed to update flow: {str(e)}")

    @router.delete("/{flow_id}")
    async def delete_flow(
            flow_id: str,
            force: bool = False,
            db_manager: DatabaseManager = Depends(db_manager_dependency),
            control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Delete a workflow and all its versions."""
        try:
            # Get flow
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Check for running workflows if not force delete
            if not force:
                # Get all versions of this flow
                with db_manager.get_session() as session:
                    from ..storage.database import FlowVersion, FlowRun

                    # Check for running workflows
                    running_runs = session.query(FlowRun).join(FlowVersion).filter(
                        FlowVersion.flow_id == flow['flow_id'],
                        FlowRun.status.in_(['pending', 'running', 'paused'])
                    ).count()

                    if running_runs > 0:
                        raise ValidationException(
                            f"Cannot delete flow {flow_id}: {running_runs} workflows are still running. "
                            "Use force=true to cancel running workflows and delete."
                        )

            # Force cancel all running workflows if force=True
            if force:
                with db_manager.get_session() as session:
                    from ..storage.database import FlowVersion, FlowRun

                    running_runs = session.query(FlowRun).join(FlowVersion).filter(
                        FlowVersion.flow_id == flow['flow_id'],
                        FlowRun.status.in_(['pending', 'running', 'paused'])
                    ).all()

                    for run in running_runs:
                        try:
                            control.cancel_workflow(run.thread_id, "Flow deleted")
                        except Exception as e:
                            logger.warning(f"Failed to cancel workflow {run.thread_id}: {e}")

            # Delete flow and all its versions (cascade delete)
            with db_manager.get_session() as session:
                from ..storage.database import Flow, FlowVersion, FlowRun, Signal

                # Delete signals for all runs of this flow
                session.query(Signal).filter(
                    Signal.thread_id.in_(
                        session.query(FlowRun.thread_id).join(FlowVersion).filter(
                            FlowVersion.flow_id == flow['flow_id']
                        )
                    )
                ).delete(synchronize_session=False)

                # Delete runs for all versions of this flow
                session.query(FlowRun).filter(
                    FlowRun.flow_version_id.in_(
                        session.query(FlowVersion.id).filter(
                            FlowVersion.flow_id == flow['flow_id']
                        )
                    )
                ).delete(synchronize_session=False)

                # Delete all versions of this flow
                session.query(FlowVersion).filter(
                    FlowVersion.flow_id == flow['flow_id']
                ).delete(synchronize_session=False)

                # Delete the flow itself
                session.query(Flow).filter(Flow.id == flow['flow_id']).delete()

                session.commit()

            logger.info(f"Deleted flow: {flow_id} (force={force})")
            return {"flow_id": flow_id, "status": "deleted", "force": force}

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
            raise ValidationException(f"Failed to delete flow: {str(e)}")

    @router.get("/{flow_id}/versions", response_model=List[FlowVersionResponse])
    async def list_flow_versions(
            flow_id: str,
            include_unpublished: bool = False,
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """List all versions of a flow."""
        try:
            # Get flow
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get all versions
            with db_manager.get_session() as session:
                from ..storage.database import FlowVersion

                query = session.query(FlowVersion).filter(
                    FlowVersion.flow_id == flow['flow_id']
                )

                if not include_unpublished:
                    query = query.filter(FlowVersion.published == True)

                versions = query.order_by(FlowVersion.created_at.desc()).all()

            return [
                FlowVersionResponse(
                    flow_version_id=version.id,
                    flow_id=version.flow_id,
                    version=version.version,
                    published=version.published,
                    created_at=version.created_at.isoformat() if version.created_at else None
                )
                for version in versions
            ]

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to list versions for flow {flow_id}: {e}")
            raise ValidationException(f"Failed to list flow versions: {str(e)}")

    @router.delete("/{flow_id}/versions/{version}")
    async def delete_flow_version(
            flow_id: str,
            version: str,
            force: bool = False,
            db_manager: DatabaseManager = Depends(db_manager_dependency),
            control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Delete a specific version of a flow."""
        try:
            # Get flow
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get specific version
            flow_version = db_manager.get_flow_version_by_version(flow['flow_id'], version)
            if not flow_version:
                raise ValidationException(f"Version {version} not found for flow {flow_id}")

            # Check for running workflows if not force delete
            if not force:
                with db_manager.get_session() as session:
                    from ..storage.database import FlowRun

                    running_runs = session.query(FlowRun).filter(
                        FlowRun.flow_version_id == flow_version['flow_version_id'],
                        FlowRun.status.in_(['pending', 'running', 'paused'])
                    ).count()

                    if running_runs > 0:
                        raise ValidationException(
                            f"Cannot delete version {version} of flow {flow_id}: "
                            f"{running_runs} workflows are still running. Use force=true to cancel and delete."
                        )

            # Force cancel running workflows if force=True
            if force:
                with db_manager.get_session() as session:
                    from ..storage.database import FlowRun

                    running_runs = session.query(FlowRun).filter(
                        FlowRun.flow_version_id == flow_version['flow_version_id'],
                        FlowRun.status.in_(['pending', 'running', 'paused'])
                    ).all()

                    for run in running_runs:
                        try:
                            control.cancel_workflow(run.thread_id, f"Flow version {version} deleted")
                        except Exception as e:
                            logger.warning(f"Failed to cancel workflow {run.thread_id}: {e}")

            # Delete the specific version and its related data
            with db_manager.get_session() as session:
                from ..storage.database import FlowVersion, FlowRun, Signal

                # Delete signals for runs of this version
                session.query(Signal).filter(
                    Signal.thread_id.in_(
                        session.query(FlowRun.thread_id).filter(
                            FlowRun.flow_version_id == flow_version['flow_version_id']
                        )
                    )
                ).delete(synchronize_session=False)

                # Delete runs for this version
                session.query(FlowRun).filter(
                    FlowRun.flow_version_id == flow_version['flow_version_id']
                ).delete(synchronize_session=False)

                # Delete the version
                session.query(FlowVersion).filter(
                    FlowVersion.id == flow_version['flow_version_id']
                ).delete()

                session.commit()

            logger.info(f"Deleted flow version: {flow_id} v{version} (force={force})")
            return {
                "flow_id": flow_id,
                "version": version,
                "status": "deleted",
                "force": force
            }

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete flow version {flow_id} v{version}: {e}")
            raise ValidationException(f"Failed to delete flow version: {str(e)}")

    @router.post("/{flow_id}/versions/{version}/publish")
    async def publish_flow_version(
            flow_id: str,
            version: str,
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Publish a specific flow version."""
        try:
            # Get flow
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get specific version (including unpublished ones)
            with db_manager.get_session() as session:
                from ..storage.database import FlowVersion

                flow_version = session.query(FlowVersion).filter(
                    FlowVersion.flow_id == flow['flow_id'],
                    FlowVersion.version == version
                ).first()

                if not flow_version:
                    raise ValidationException(f"Version {version} not found for flow {flow_id}")

                # Publish the version
                success = db_manager.publish_flow_version(flow_version.id)
                if not success:
                    raise ValidationException(f"Failed to publish version {version}")

            logger.info(f"Published flow version: {flow_id} v{version}")
            return {
                "flow_id": flow_id,
                "version": version,
                "flow_version_id": flow_version.id,
                "status": "published"
            }

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to publish flow version {flow_id} v{version}: {e}")
            raise ValidationException(f"Failed to publish flow version: {str(e)}")

    @router.get("", response_model=FlowListResponse)
    async def list_flows(
            limit: int = 100,
            offset: int = 0,
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """List all flows with their latest versions."""
        try:
            with db_manager.get_session() as session:
                from ..storage.database import Flow, FlowVersion

                # Get flows with pagination
                flows_query = session.query(Flow).offset(offset).limit(limit)
                flows = flows_query.all()

                # Get total count
                total = session.query(Flow).count()

                # Get latest version for each flow
                flow_list = []
                for flow in flows:
                    latest_version = db_manager.get_latest_flow_version(flow.id)

                    flow_data = {
                        "flow_id": flow.id,
                        "name": flow.name,
                        "created_at": flow.created_at.isoformat() if flow.created_at else None,
                        "latest_version": latest_version['version'] if latest_version else None,
                        "latest_version_id": latest_version['flow_version_id'] if latest_version else None
                    }
                    flow_list.append(flow_data)

            return FlowListResponse(flows=flow_list, total=total)

        except Exception as e:
            logger.error(f"Failed to list flows: {e}")
            raise ValidationException(f"Failed to list flows: {str(e)}")

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

    @router.post("/{flow_id}/start/latest", response_model=StartFlowResponse)
    async def start_flow_latest_version(
            flow_id: str,
            request: StartFlowRequest,
            control: WorkflowControl = Depends(workflow_control_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Start workflow execution by flow ID using the latest published version."""
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

            # Start the workflow asynchronously using the control
            thread_id = await control.start_workflow_async(
                flow_version_id=flow_version_id,
                input_data=request.input_data,
                thread_id=request.thread_id
            )

            logger.info(f"Started workflow {flow_id} (latest version) with thread_id: {thread_id}")

            return StartFlowResponse(
                thread_id=thread_id,
                status="started",
                message=f"Workflow {flow_id} started successfully with latest version",
                flow_id=flow_id,
                version=flow_version['version']
            )

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to start workflow {flow_id}: {e}")
            raise ValidationException(f"Failed to start workflow: {str(e)}")

    @router.post("/{flow_id}/start/version/{version}", response_model=StartFlowResponse)
    async def start_flow_specific_version(
            flow_id: str,
            version: str,
            request: StartFlowRequest,
            control: WorkflowControl = Depends(workflow_control_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Start workflow execution by flow ID with specific version number."""
        try:
            # flow_id and version are now separate parameters, no parsing needed

            # Validate flow exists
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            # Get specific version for this flow
            flow_version = db_manager.get_flow_version_by_version(flow['flow_id'], version)
            if not flow_version:
                raise ValidationException(f"Version {version} not found for flow {flow_id}")

            flow_version_id = flow_version['flow_version_id']

            # Start the workflow asynchronously using the control
            thread_id = await control.start_workflow_async(
                flow_version_id=flow_version_id,
                input_data=request.input_data,
                thread_id=request.thread_id
            )

            logger.info(f"Started workflow {flow_id} v{version} with thread_id: {thread_id}")

            return StartFlowResponse(
                thread_id=thread_id,
                status="started",
                message=f"Workflow {flow_id} v{version} started successfully",
                flow_id=flow_id,
                version=version
            )

        except FlowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to start workflow {flow_id} v{version}: {e}")
            raise ValidationException(f"Failed to start workflow: {str(e)}")

    return router
