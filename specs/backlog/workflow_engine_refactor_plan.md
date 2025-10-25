# Workflow Engine Refactor Plan

## Executive Summary
This document outlines a comprehensive refactor plan to address critical design and performance issues in the workflow engine. The plan is structured in phases to ensure stability while incrementally improving the system's reliability, performance, and maintainability.

## Current State Assessment

### Identified Issues
1. **Missing Checkpoint Persistence** - No state persistence across server restarts
2. **Incomplete Interrupt Handling** - Undefined exceptions and broken pause/resume
3. **Race Conditions** - Non-atomic database operations
4. **Performance Bottlenecks** - Inefficient queries and synchronous operations
5. **Thread Safety Issues** - Shared global state without proper synchronization
6. **Security Vulnerabilities** - Unsafe dynamic imports and dependency installations

## Refactor Plan

### Phase 1: Critical Stability Fixes (Sprint 1)

#### 1.1. Implement Proper Checkpointing
**Issue**: Missing checkpoint persistence (Critical #1)

**Solution**:
- Re-enable LangGraph checkpointing with SQLite checkpointer
- Implement proper initialization of `SqliteSaver` in WorkflowEngine
- Add configuration option to enable/disable checkpointing
- Create migration path for existing workflows

**Implementation Steps**:
```python
# In core/engine.py
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

class WorkflowEngine:
    def __init__(self, db_path: Optional[str] = None):
        # ... existing code ...
        # Initialize checkpoint saver
        checkpoint_db_path = db_path.replace('.db', '_checkpoints.db') if db_path else ":memory:"
        self.checkpointer = SqliteSaver(conn=sqlite3.connect(checkpoint_db_path, check_same_thread=False))
```

**Testing**:
- Test workflow persistence across server restarts
- Verify checkpoint integrity
- Performance impact assessment

**Estimated Effort**: 3 days

#### 1.2. Fix Interrupt Handling
**Issue**: Incomplete interrupt handling (Critical #2)

**Solution**:
- Define proper `InterruptedError` exception class
- Implement LangGraph-compatible interrupt mechanism
- Use proper state management for pause/resume
- Add proper error handling for interrupt scenarios

**Implementation Steps**:
```python
# In core/engine.py
class WorkflowInterrupt(Exception):
    """Custom exception for workflow interrupts"""
    def __init__(self, reason: str, data: Optional[Dict] = None):
        self.reason = reason
        self.data = data or {}
        super().__init__(f"Workflow interrupted: {reason}")

def _create_python_node_handler(self, node_def):
    def handler(state: WorkflowState) -> Dict[str, Any]:
        # ... existing code ...
        
        def interrupt(value=None, update=None):
            # Update state with provided data
            if update:
                for key, val in update.items():
                    setattr(state, key, val)
            
            # Update database status to paused
            self.db_manager.update_run_status(state.thread_id, "paused", {
                "interrupt_value": value,
                "last_node": node_def.id
            })
            
            # Raise proper exception for LangGraph
            raise WorkflowInterrupt("Manual interrupt", {"node_id": node_def.id, "value": value})
```

**Testing**:
- Test pause/resume functionality
- Verify state consistency after interrupts
- Error handling validation

**Estimated Effort**: 4 days

#### 1.3. Address Race Conditions
**Issue**: Race conditions in state management (Critical #3)

**Solution**:
- Implement atomic database operations using transactions
- Add proper synchronization for signal processing
- Use database-level locks where appropriate
- Add optimistic locking to prevent overwrites

**Implementation Steps**:
```python
# In storage/database.py
from sqlalchemy import select

class DatabaseManager:
    def atomic_update_run_status(self, thread_id: str, status: str, 
                                metadata: Optional[Dict[str, Any]] = None,
                                expected_current_status: Optional[str] = None) -> bool:
        """Atomically update run status with optional status verification."""
        with self.get_session() as session:
            try:
                # Get the run with FOR UPDATE lock
                stmt = select(FlowRun).where(FlowRun.thread_id == thread_id).with_for_update()
                run = session.execute(stmt).scalar_one_or_none()
                
                if not run:
                    return False
                
                # Verify expected status if provided
                if expected_current_status and run.status != expected_current_status:
                    logger.warning(f"Status mismatch for {thread_id}: expected {expected_current_status}, got {run.status}")
                    return False
                
                # Update the run
                run.status = status
                run.last_event_at = datetime.utcnow()
                
                if status == "running" and not run.started_at:
                    run.started_at = datetime.utcnow()
                elif status in ["completed", "failed", "cancelled"]:
                    run.finished_at = datetime.utcnow()
                
                if metadata:
                    run.run_metadata.update(metadata)
                
                session.commit()
                logger.info(f"Atomic update: {thread_id} -> {status}")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Atomic update failed for {thread_id}: {e}")
                return False
    
    def atomic_claim_signal(self, thread_id: str, signal_type: str) -> Optional[Dict[str, Any]]:
        """Atomically claim a signal to prevent multiple processors from handling the same signal."""
        with self.get_session() as session:
            try:
                # Find and lock an unprocessed signal
                stmt = (select(Signal)
                       .where(Signal.thread_id == thread_id)
                       .where(Signal.type == signal_type)
                       .where(Signal.processed == False)
                       .with_for_update()
                       .order_by(Signal.ts.asc())
                       .limit(1))
                
                signal = session.execute(stmt).scalar_one_or_none()
                
                if not signal:
                    return None
                
                # Mark as processed atomically
                signal.processed = True
                session.commit()
                
                return {
                    "id": signal.id,
                    "thread_id": signal.thread_id,
                    "type": signal.type,
                    "payload_json": signal.payload_json,
                    "ts": signal.ts.isoformat() if signal.ts else None
                }
                
            except Exception as e:
                session.rollback()
                logger.error(f"Atomic claim signal failed: {e}")
                return None
```

**Testing**:
- Concurrent workflow execution tests
- Signal processing race condition tests
- Transaction rollback validation

**Estimated Effort**: 5 days

### Phase 2: Performance Improvements (Sprint 2)

#### 2.1. Optimize Database Queries
**Issue**: Inefficient database queries (High #4)

**Solution**:
- Add proper database indexes
- Implement bulk operations
- Optimize complex queries with JOINs
- Add query result caching

**Implementation Steps**:
```python
# In storage/database.py
# Add database indexes
class FlowRun(Base):
    __tablename__ = "runs"
    __table_args__ = (
        # Add indexes for common query patterns
        Index('idx_runs_thread_id', 'thread_id'),
        Index('idx_runs_status', 'status'),
        Index('idx_runs_last_event', 'last_event_at'),
        Index('idx_runs_flow_version', 'flow_version_id'),
        Index('idx_runs_started_at', 'started_at'),
    )

    # ... existing fields ...

# Optimize get_data_retention_stats with single query
def get_data_retention_stats(self) -> Dict[str, Any]:
    """Get statistics about data retention and storage usage."""
    with self.get_session() as session:
        # Use a single query with CASE statements to count by age groups
        from sqlalchemy import func, case
        
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Stats for runs
        run_stats = session.query(
            func.count(FlowRun.thread_id).label('total_runs'),
            func.sum(case((FlowRun.last_event_at >= day_ago, 1), else_=0)).label('last_24h'),
            func.sum(case((FlowRun.last_event_at >= week_ago, 1), else_=0)).label('last_7d'),
            func.sum(case((FlowRun.last_event_at >= month_ago, 1), else_=0)).label('last_30d'),
            func.sum(case((FlowRun.last_event_at < month_ago, 1), else_=0)).label('older_than_30d'),
            func.min(FlowRun.last_event_at).label('oldest_run'),
            func.max(FlowRun.last_event_at).label('newest_run')
        ).one()
        
        # Stats for signals
        signal_stats = session.query(
            func.count(Signal.id).label('total_signals'),
            func.sum(case((Signal.ts >= day_ago, 1), else_=0)).label('last_24h_signals'),
            func.sum(case((Signal.ts >= week_ago, 1), else_=0)).label('last_7d_signals'),
            func.sum(case((Signal.ts >= month_ago, 1), else_=0)).label('last_30d_signals'),
            func.sum(case((Signal.ts < month_ago, 1), else_=0)).label('older_than_30d_signals')
        ).one()
        
        return {
            "total_runs": run_stats.total_runs or 0,
            "runs_by_age": {
                "last_24h": run_stats.last_24h or 0,
                "last_7d": run_stats.last_7d or 0,
                "last_30d": run_stats.last_30d or 0,
                "older_than_30d": run_stats.older_than_30d or 0
            },
            "total_signals": signal_stats.total_signals or 0,
            "signals_by_age": {
                "last_24h": signal_stats.last_24h_signals or 0,
                "last_7d": signal_stats.last_7d_signals or 0,
                "last_30d": signal_stats.last_30d_signals or 0,
                "older_than_30d": signal_stats.older_than_30d_signals or 0
            },
            "oldest_run": run_stats.oldest_run.isoformat() if run_stats.oldest_run else None,
            "newest_run": run_stats.newest_run.isoformat() if run_stats.newest_run else None
        }
```

**Testing**:
- Query performance benchmarks
- Load testing with large datasets
- Index effectiveness validation

**Estimated Effort**: 4 days

#### 2.2. Asynchronous Operations
**Issue**: Synchronous operations (High #5)

**Solution**:
- Implement async workflow execution methods
- Use async/await patterns throughout the engine
- Add proper async database operations
- Update API endpoints to support async operations

**Implementation Steps**:
```python
# In core/engine.py
import asyncio
from typing import Union, Awaitable

class WorkflowEngine:
    async def start_workflow_async(self, flow_version_id: int, input_data: Optional[Dict[str, Any]] = None,
                                  thread_id: Optional[str] = None) -> str:
        """Async version of start_workflow."""
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        # Get flow version
        flow_version = await self.db_manager.get_flow_version_async(flow_version_id)
        if not flow_version:
            raise ValueError(f"Flow version not found: {flow_version_id}")

        # Ensure functions are registered before execution
        await self._ensure_functions_registered_async(flow_version_id)

        # Create workflow definition
        definition = WorkflowDefinition(**flow_version["dsl_json"])

        # Compile workflow
        graph = self.compile_workflow(definition)
        compiled_graph = graph.compile(checkpointer=self.checkpointer)

        # Create initial state
        initial_state = WorkflowState(
            thread_id=thread_id,
            data=input_data or {},
            metadata={"flow_version_id": flow_version_id}
        )

        # Create run record
        existing_run = await self.db_manager.get_run_async(thread_id)
        if not existing_run:
            await self.db_manager.create_run_async(thread_id, flow_version_id, "pending", 
                                                 metadata={"inputs": input_data or {}})
        else:
            await self.db_manager.update_run_status_async(thread_id, "pending", 
                                                        metadata={"inputs": input_data or {}, "restarted": True})
        
        # Start execution async
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Execute workflow asynchronously
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: compiled_graph.invoke(initial_state, config)
            )
            
            logger.info(f"Workflow execution completed for thread: {thread_id}, result_keys: {list(result.keys())}")
            
        except WorkflowInterrupt as e:
            logger.info(f"Workflow execution interrupted for thread: {thread_id}, reason: {e.reason}")
        
        except Exception as e:
            logger.error(f"Workflow execution failed for thread: {thread_id}, error: {str(e)}, error_type: {type(e).__name__}")
            
            await self.db_manager.update_run_status_async(thread_id, "failed", {"error": str(e)})
            raise
        
        return thread_id
```

**Testing**:
- Concurrency testing with multiple simultaneous workflows
- Performance comparison between sync and async versions
- Memory usage monitoring

**Estimated Effort**: 6 days

### Phase 3: Thread Safety and Architecture (Sprint 3)

#### 3.1. Isolate Global State
**Issue**: Global state issues (High #6)

**Solution**:
- Replace global registry with dependency injection
- Implement registry per application context
- Add proper namespace isolation
- Use scoped registries for multi-tenant scenarios

**Implementation Steps**:
```python
# In core/registry.py
from typing import Protocol
from contextlib import contextmanager

class IFunctionRegistry(Protocol):
    """Protocol for function registry implementations."""
    
    def register_function(self, code_ref: str, func: Callable) -> None:
        ...
    
    def get_function(self, code_ref: str) -> Optional[Callable]:
        ...
    
    def list_functions(self) -> List[str]:
        ...

class ScopedFunctionRegistry:
    """Thread-safe, scoped function registry."""
    
    def __init__(self):
        self._registries = {}  # app_id -> registry
        self._lock = threading.RLock()
    
    def get_registry(self, scope: str = "default") -> Dict[str, Callable]:
        """Get registry for specific scope."""
        if scope not in self._registries:
            with self._lock:
                if scope not in self._registries:
                    self._registries[scope] = {}
        return self._registries[scope]
    
    def register_function(self, code_ref: str, func: Callable, scope: str = "default") -> None:
        """Register a function in a specific scope."""
        registry = self.get_registry(scope)
        with self._lock:
            registry[code_ref] = func
            logger.info(f"Registered function in scope {scope}: {code_ref} -> {func.__name__}")
    
    def get_function(self, code_ref: str, scope: str = "default") -> Optional[Callable]:
        """Get a function from a specific scope."""
        registry = self.get_registry(scope)
        return registry.get(code_ref)
    
    def list_functions(self, scope: str = "default") -> List[str]:
        """List all functions in a specific scope."""
        registry = self.get_registry(scope)
        return list(registry.keys())

# Global scoped registry instance
_SCOPED_REGISTRY = ScopedFunctionRegistry()

def register_function(code_ref: str, func: Optional[Callable] = None, scope: str = "default"):
    """Register function with optional scope."""
    def decorator(f: Callable) -> Callable:
        # Validate function signature
        sig = inspect.signature(f)
        params = list(sig.parameters.keys())

        if not params or params[0] != 'state':
            raise ValueError(f"Function {f.__name__} must have 'state' as first parameter")

        # Register the function in the specified scope
        _SCOPED_REGISTRY.register_function(code_ref, f, scope)
        
        # ... wrapper code ...
        return wrapper

    if func is not None:
        return decorator(func)
    else:
        return decorator

def get_registered_function(code_ref: str, scope: str = "default") -> Optional[Callable]:
    """Get registered function from specified scope."""
    return _SCOPED_REGISTRY.get_function(code_ref, scope)
```

**Testing**:
- Multi-tenant isolation tests
- Thread-safety validation
- Performance impact assessment

**Estimated Effort**: 5 days

#### 3.2. Improve Architecture
**Issue**: Tight coupling (Medium #7)

**Solution**:
- Implement proper dependency injection
- Separate concerns with distinct service layers
- Add proper configuration management
- Create interface-based architecture

**Implementation Steps**:
```python
# Create service interfaces
from abc import ABC, abstractmethod

class IWorkflowService(ABC):
    @abstractmethod
    async def start_workflow(self, flow_version_id: int, input_data: Optional[Dict] = None) -> str:
        pass

class IStateService(ABC):
    @abstractmethod
    async def save_state(self, thread_id: str, state: Any) -> bool:
        pass
    
    @abstractmethod
    async def load_state(self, thread_id: str) -> Optional[Any]:
        pass

class IDatabaseService(ABC):
    @abstractmethod
    async def get_flow_version(self, flow_version_id: int) -> Optional[Dict]:
        pass

# Implement concrete services
class DatabaseService(IDatabaseService):
    def __init__(self, db_path: Optional[str] = None):
        self.db_manager = DatabaseManager(db_path)
    
    async def get_flow_version(self, flow_version_id: int) -> Optional[Dict]:
        # Implementation with async support
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, 
                                        lambda: self.db_manager.get_flow_version(flow_version_id))

class WorkflowService(IWorkflowService):
    def __init__(self, 
                 db_service: IDatabaseService,
                 state_service: IStateService,
                 registry: IFunctionRegistry):
        self.db_service = db_service
        self.state_service = state_service
        self.registry = registry
        # ... other dependencies

# Dependency injection container
class ServiceContainer:
    def __init__(self, config):
        self.config = config
        self._services = {}
    
    def register_service(self, interface, implementation):
        self._services[interface] = implementation
    
    def get_service(self, interface):
        if interface in self._services:
            return self._services[interface]
        raise ValueError(f"Service not registered: {interface}")

# Usage in engine
class WorkflowEngine:
    def __init__(self, container: ServiceContainer):
        self.container = container
        self.db_service = container.get_service(IDatabaseService)
        self.workflow_service = container.get_service(IWorkflowService)
        # ... other services
```

**Testing**:
- Unit tests for each service
- Integration tests for service interactions
- Dependency injection validation

**Estimated Effort**: 6 days

### Phase 4: Security and Validation (Sprint 4)

#### 4.1. Secure Dynamic Imports
**Issue**: Security concerns (Low #10)

**Solution**:
- Add proper code_ref validation
- Implement import allowlists
- Add security checks for dynamic operations
- Sanitize all user inputs

**Implementation Steps**:
```python
# In core/registry.py
import re
from pathlib import Path

def validate_code_ref(code_ref: str) -> bool:
    """Validate code reference for security."""
    # Only allow alphanumeric, dots, underscores, and hyphens
    if not re.match(r'^[a-zA-Z0-9._-]+$', code_ref):
        return False
    
    # Prevent directory traversal
    if '..' in code_ref or code_ref.startswith('/') or ':' in code_ref[1:]:  # Avoid Windows drive letters
        return False
    
    # Check depth (limit to reasonable number of segments)
    segments = code_ref.split('.')
    if len(segments) > 10:  # Reasonable limit
        return False
    
    return True

def safe_import_module(module_path: str, allowed_modules: List[str] = None) -> Optional[ModuleType]:
    """Safely import module with validation."""
    if allowed_modules is None:
        allowed_modules = [
            "apps.",
            "workflow_engine.",
            "src_new."
        ]
    
    # Validate that module path is in allowed list
    if not any(module_path.startswith(prefix) for prefix in allowed_modules):
        logger.warning(f"Module {module_path} not in allowed list")
        return None
    
    try:
        import importlib
        # Additional security check: ensure path doesn't contain dangerous elements
        if not validate_code_ref(module_path.replace('.', '_')):
            logger.warning(f"Invalid module path: {module_path}")
            return None
            
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.error(f"Failed to import {module_path}: {e}")
        return None
```

**Testing**:
- Security validation tests
- Malicious input handling
- Allowlist validation

**Estimated Effort**: 3 days

## Implementation Timeline

| Sprint | Focus | Duration | Deliverables |
|--------|-------|----------|--------------|
| Sprint 1 | Critical stability fixes | 2 weeks | Fixed checkpointing, interrupt handling, race conditions |
| Sprint 2 | Performance improvements | 2 weeks | Optimized queries, async operations |
| Sprint 3 | Architecture improvements | 2 weeks | Thread safety, dependency injection |
| Sprint 4 | Security improvements | 1 week | Input validation, secure imports |

## Risk Mitigation

### High-Risk Areas
1. **Checkpoint Migration**: Risk of losing existing workflow data during checkpoint implementation
   - *Mitigation*: Implement gradual migration with fallback to old behavior

2. **Async Migration**: Risk of breaking existing synchronous integrations
   - *Mitigation*: Provide both sync and async APIs during transition period

3. **Database Schema Changes**: Risk of breaking backward compatibility
   - *Mitigation*: Implement proper migration scripts and maintain backward compatibility

### Testing Strategy
1. **Unit Tests**: 100% coverage for new functionality
2. **Integration Tests**: End-to-end workflow execution tests
3. **Performance Tests**: Load testing before and after each phase
4. **Regression Tests**: All existing functionality must continue to work

## Success Metrics

### Technical Metrics
- Database query performance improvement > 50%
- Workflow execution speed improvement > 30%
- Memory usage reduction > 20%
- Concurrent workflow capacity increase > 100%

### Business Metrics
- Workflow completion rate improvement
- System uptime increase
- Error rate reduction
- User satisfaction with pause/resume functionality

## Rollout Strategy

### Staging Deployment
1. Deploy changes to staging environment
2. Run comprehensive test suite
3. Load testing with realistic scenarios
4. Validate performance improvements

### Production Rollout
1. Gradual rollout to 10% of users
2. Monitor for issues for 48 hours
3. Roll out to 50% if no issues
4. Full rollout if stable

## Post-Implementation Review

### Documentation Updates
- Update API documentation
- Update architecture diagrams
- Add performance benchmarks
- Add security guidelines

### Knowledge Transfer
- Team training on new architecture
- Code walkthroughs
- Performance tuning guidelines
- Security best practices

## Conclusion

This refactor plan addresses all critical and high-priority issues identified in the workflow engine. The phased approach ensures stability while incrementally improving the system. Each phase builds upon the previous one, with proper testing and validation at each step.

The plan balances immediate stability improvements with long-term architectural improvements that will make the system more maintainable and scalable.