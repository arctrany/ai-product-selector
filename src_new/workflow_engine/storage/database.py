"""Database layer for workflow engine using SQLite."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Integer, JSON, String, Text, create_engine, and_
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()

class Flow(Base):
    """Flow definition table."""
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FlowVersion(Base):
    """Flow version table."""
    __tablename__ = "flow_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flow_id = Column(Integer, nullable=False)
    version = Column(String(50), nullable=False)
    dsl_json = Column(JSON, nullable=False)
    compiled_meta = Column(JSON)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FlowRun(Base):
    """Flow run table."""
    __tablename__ = "runs"

    thread_id = Column(String(255), primary_key=True)
    flow_version_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    last_event_at = Column(DateTime)
    run_metadata = Column(JSON, default=dict)

class Signal(Base):
    """Control signal table."""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    payload_json = Column(JSON, default=dict)
    ts = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class DatabaseManager:
    """Database manager for workflow engine."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_dir = Path.home() / ".ren"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "workflow.db")

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized at {db_path}")

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def cleanup_old_data(self, retention_days: int = 30) -> Dict[str, int]:
        """
        Clean up old thread data beyond retention period.

        Args:
            retention_days: Number of days to retain data (default: 30)

        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        cleanup_stats = {
            "runs_deleted": 0,
            "signals_deleted": 0,
            "cutoff_date": cutoff_date.isoformat()
        }

        logger.info(f"Starting data cleanup for records older than {cutoff_date}")

        with self.get_session() as session:
            try:
                # Find old runs to delete (using last_event_at as primary criteria)
                old_runs_query = session.query(FlowRun).filter(
                    FlowRun.last_event_at < cutoff_date
                )

                # Also include runs that have no last_event_at but have old started_at
                old_runs_query_no_event = session.query(FlowRun).filter(
                    and_(
                        FlowRun.last_event_at.is_(None),
                        FlowRun.started_at < cutoff_date
                    )
                )

                # Get thread_ids before deletion for signal cleanup
                old_thread_ids = set()

                # Collect thread_ids from both queries
                for run in old_runs_query.all():
                    old_thread_ids.add(run.thread_id)

                for run in old_runs_query_no_event.all():
                    old_thread_ids.add(run.thread_id)

                # Delete old runs
                runs_deleted = old_runs_query.delete(synchronize_session=False)
                runs_deleted += old_runs_query_no_event.delete(synchronize_session=False)

                cleanup_stats["runs_deleted"] = runs_deleted

                # Delete signals for old thread_ids
                if old_thread_ids:
                    signals_deleted = session.query(Signal).filter(
                        Signal.thread_id.in_(old_thread_ids)
                    ).delete(synchronize_session=False)
                    cleanup_stats["signals_deleted"] = signals_deleted

                # Also delete very old signals (older than retention period)
                old_signals_deleted = session.query(Signal).filter(
                    Signal.ts < cutoff_date
                ).delete(synchronize_session=False)

                cleanup_stats["signals_deleted"] += old_signals_deleted

                session.commit()

                logger.info(f"Data cleanup completed: {cleanup_stats}")

            except Exception as e:
                session.rollback()
                logger.error(f"Data cleanup failed: {e}")
                raise

        return cleanup_stats

    def get_data_retention_stats(self) -> Dict[str, Any]:
        """
        Get statistics about data retention and storage usage.

        Returns:
            Dictionary with retention statistics
        """
        stats = {
            "total_runs": 0,
            "runs_by_age": {
                "last_24h": 0,
                "last_7d": 0,
                "last_30d": 0,
                "older_than_30d": 0
            },
            "total_signals": 0,
            "signals_by_age": {
                "last_24h": 0,
                "last_7d": 0,
                "last_30d": 0,
                "older_than_30d": 0
            },
            "oldest_run": None,
            "newest_run": None
        }

        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        with self.get_session() as session:
            # Run statistics
            stats["total_runs"] = session.query(FlowRun).count()

            # Runs by age (using last_event_at or started_at)
            stats["runs_by_age"]["last_24h"] = session.query(FlowRun).filter(
                FlowRun.last_event_at >= day_ago
            ).count()

            stats["runs_by_age"]["last_7d"] = session.query(FlowRun).filter(
                FlowRun.last_event_at >= week_ago
            ).count()

            stats["runs_by_age"]["last_30d"] = session.query(FlowRun).filter(
                FlowRun.last_event_at >= month_ago
            ).count()

            stats["runs_by_age"]["older_than_30d"] = session.query(FlowRun).filter(
                FlowRun.last_event_at < month_ago
            ).count()

            # Signal statistics
            stats["total_signals"] = session.query(Signal).count()

            stats["signals_by_age"]["last_24h"] = session.query(Signal).filter(
                Signal.ts >= day_ago
            ).count()

            stats["signals_by_age"]["last_7d"] = session.query(Signal).filter(
                Signal.ts >= week_ago
            ).count()

            stats["signals_by_age"]["last_30d"] = session.query(Signal).filter(
                Signal.ts >= month_ago
            ).count()

            stats["signals_by_age"]["older_than_30d"] = session.query(Signal).filter(
                Signal.ts < month_ago
            ).count()

            # Oldest and newest runs
            oldest_run = session.query(FlowRun).order_by(
                FlowRun.last_event_at.asc()
            ).first()
            if oldest_run and oldest_run.last_event_at:
                stats["oldest_run"] = oldest_run.last_event_at.isoformat()

            newest_run = session.query(FlowRun).order_by(
                FlowRun.last_event_at.desc()
            ).first()
            if newest_run and newest_run.last_event_at:
                stats["newest_run"] = newest_run.last_event_at.isoformat()

        return stats

    def cleanup_orphaned_signals(self) -> int:
        """
        Clean up signals that reference non-existent thread_ids.

        Returns:
            Number of orphaned signals deleted
        """
        with self.get_session() as session:
            # Get all existing thread_ids
            existing_thread_ids = {
                row[0] for row in session.query(FlowRun.thread_id).all()
            }

            if not existing_thread_ids:
                # No runs exist, delete all signals
                orphaned_count = session.query(Signal).delete(synchronize_session=False)
            else:
                # Delete signals with thread_ids not in existing runs
                orphaned_count = session.query(Signal).filter(
                    ~Signal.thread_id.in_(existing_thread_ids)
                ).delete(synchronize_session=False)

            session.commit()

            if orphaned_count > 0:
                logger.info(f"Cleaned up {orphaned_count} orphaned signals")

            return orphaned_count

    def create_flow_by_name(self, flow_name: str, version: str = "1.0.0",
                           dsl_json: Optional[Dict[str, Any]] = None, published: bool = True) -> int:
        """Create a new flow by name with simplified parameters."""
        with self.get_session() as session:
            # Check if flow already exists
            existing_flow = session.query(Flow).filter(Flow.name == flow_name).first()
            if existing_flow:
                return existing_flow.id

            # Create new flow
            flow = Flow(name=flow_name)
            session.add(flow)
            session.commit()
            session.refresh(flow)

            # Create flow version with default DSL if not provided
            if dsl_json is None:
                dsl_json = {
                    "name": flow_name,
                    "description": f"Auto-generated flow for {flow_name}",
                    "nodes": [],
                    "edges": []
                }

            flow_version = FlowVersion(
                flow_id=flow.id,
                version=version,
                dsl_json=dsl_json,
                published=published
            )
            session.add(flow_version)
            session.commit()
            session.refresh(flow_version)

            logger.info(f"Created flow: {flow_name} (ID: {flow.id}) with version {version}")
            return flow.id

    def create_flow_version(self, flow_id: int, version: str, dsl_json: Dict[str, Any],
                           compiled_meta: Optional[Dict[str, Any]] = None) -> int:
        """Create a new flow version."""
        with self.get_session() as session:
            flow_version = FlowVersion(
                flow_id=flow_id,
                version=version,
                dsl_json=dsl_json,
                compiled_meta=compiled_meta
            )
            session.add(flow_version)
            session.commit()
            session.refresh(flow_version)
            logger.info(f"Created flow version: {flow_id}@{version} (ID: {flow_version.id})")
            return flow_version.id

    def publish_flow_version(self, flow_version_id: int) -> bool:
        """Publish a flow version."""
        with self.get_session() as session:
            flow_version = session.query(FlowVersion).filter(
                FlowVersion.id == flow_version_id
            ).first()

            if not flow_version:
                return False

            flow_version.published = True
            session.commit()
            logger.info(f"Published flow version: {flow_version_id}")
            return True

    def get_flow_version(self, flow_version_id: int) -> Optional[Dict[str, Any]]:
        """Get flow version by ID."""
        with self.get_session() as session:
            flow_version = session.query(FlowVersion).filter(
                FlowVersion.id == flow_version_id
            ).first()

            if not flow_version:
                return None

            return {
                "id": flow_version.id,
                "flow_id": flow_version.flow_id,
                "version": flow_version.version,
                "dsl_json": flow_version.dsl_json,
                "compiled_meta": flow_version.compiled_meta,
                "published": flow_version.published,
                "created_at": flow_version.created_at.isoformat() if flow_version.created_at else None
            }

    def create_run(self, thread_id: str, flow_version_id: int, status: str = "pending",
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Create a new flow run."""
        with self.get_session() as session:
            run = FlowRun(
                thread_id=thread_id,
                flow_version_id=flow_version_id,
                status=status,
                started_at=datetime.utcnow() if status == "running" else None,
                run_metadata=metadata or {}
            )
            session.add(run)
            session.commit()
            logger.info(f"Created run: {thread_id} (status: {status})")
            return True

    def update_run_status(self, thread_id: str, status: str,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update run status."""
        with self.get_session() as session:
            run = session.query(FlowRun).filter(FlowRun.thread_id == thread_id).first()

            if not run:
                return False

            run.status = status
            run.last_event_at = datetime.utcnow()

            if status == "running" and not run.started_at:
                run.started_at = datetime.utcnow()
            elif status in ["completed", "failed", "cancelled"]:
                run.finished_at = datetime.utcnow()

            if metadata:
                run.run_metadata.update(metadata)

            session.commit()
            logger.info(f"Updated run status: {thread_id} -> {status}")
            return True

    def get_run(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get run by thread ID."""
        with self.get_session() as session:
            run = session.query(FlowRun).filter(FlowRun.thread_id == thread_id).first()

            if not run:
                return None

            return {
                "thread_id": run.thread_id,
                "flow_version_id": run.flow_version_id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "last_event_at": run.last_event_at.isoformat() if run.last_event_at else None,
                "metadata": run.run_metadata
            }

    def list_runs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent runs."""
        with self.get_session() as session:
            runs = session.query(FlowRun).order_by(
                FlowRun.last_event_at.desc()
            ).limit(limit).all()

            return [
                {
                    "thread_id": run.thread_id,
                    "flow_version_id": run.flow_version_id,
                    "status": run.status,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                    "last_event_at": run.last_event_at.isoformat() if run.last_event_at else None,
                    "metadata": run.run_metadata
                }
                for run in runs
            ]

    def create_signal(self, thread_id: str, signal_type: str,
                     payload: Optional[Dict[str, Any]] = None) -> int:
        """Create a control signal."""
        with self.get_session() as session:
            signal = Signal(
                thread_id=thread_id,
                type=signal_type,
                payload_json=payload or {}
            )
            session.add(signal)
            session.commit()
            session.refresh(signal)
            logger.info(f"Created signal: {signal_type} for {thread_id}")
            return signal.id

    def get_pending_signals(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get pending signals for a thread."""
        with self.get_session() as session:
            signals = session.query(Signal).filter(
                Signal.thread_id == thread_id,
                Signal.processed == False
            ).order_by(Signal.ts).all()

            return [
                {
                    "id": signal.id,
                    "thread_id": signal.thread_id,
                    "type": signal.type,
                    "payload_json": signal.payload_json,
                    "ts": signal.ts.isoformat() if signal.ts else None
                }
                for signal in signals
            ]

    def mark_signal_processed(self, signal_id: int) -> bool:
        """Mark a signal as processed."""
        with self.get_session() as session:
            signal = session.query(Signal).filter(Signal.id == signal_id).first()

            if not signal:
                return False

            signal.processed = True
            session.commit()
            return True

    def get_flow_by_name(self, flow_name: str) -> Optional[Dict[str, Any]]:
        """Get flow by name."""
        with self.get_session() as session:
            flow = session.query(Flow).filter(Flow.name == flow_name).first()

            if not flow:
                return None

            return {
                "flow_id": flow.id,
                "name": flow.name,
                "created_at": flow.created_at.isoformat() if flow.created_at else None
            }

    def get_latest_flow_version(self, flow_id: int) -> Optional[Dict[str, Any]]:
        """Get latest published flow version."""
        with self.get_session() as session:
            flow_version = session.query(FlowVersion).filter(
                FlowVersion.flow_id == flow_id,
                FlowVersion.published == True
            ).order_by(FlowVersion.created_at.desc()).first()

            if not flow_version:
                return None

            return {
                "flow_version_id": flow_version.id,
                "flow_id": flow_version.flow_id,
                "version": flow_version.version,
                "dsl_json": flow_version.dsl_json,
                "compiled_meta": flow_version.compiled_meta,
                "published": flow_version.published,
                "created_at": flow_version.created_at.isoformat() if flow_version.created_at else None
            }

    def get_flow_version_by_version(self, flow_id: int, version: str) -> Optional[Dict[str, Any]]:
        """Get specific flow version by flow_id and version."""
        with self.get_session() as session:
            flow_version = session.query(FlowVersion).filter(
                FlowVersion.flow_id == flow_id,
                FlowVersion.version == version,
                FlowVersion.published == True
            ).first()

            if not flow_version:
                return None

            return {
                "flow_version_id": flow_version.id,
                "flow_id": flow_version.flow_id,
                "version": flow_version.version,
                "dsl_json": flow_version.dsl_json,
                "compiled_meta": flow_version.compiled_meta,
                "published": flow_version.published,
                "created_at": flow_version.created_at.isoformat() if flow_version.created_at else None
            }

    def get_flow_by_name_and_version(self, flow_name: str, version: str) -> Optional[Dict[str, Any]]:
        """Get flow by name and version (flow+version combination is unique)."""
        with self.get_session() as session:
            # First get the flow by name
            flow = session.query(Flow).filter(Flow.name == flow_name).first()
            if not flow:
                return None

            # Then get the specific version
            flow_version = session.query(FlowVersion).filter(
                FlowVersion.flow_id == flow.id,
                FlowVersion.version == version,
                FlowVersion.published == True
            ).first()

            if not flow_version:
                return None

            return {
                "flow_version_id": flow_version.id,
                "flow_id": flow_version.flow_id,
                "flow_name": flow.name,
                "version": flow_version.version,
                "dsl_json": flow_version.dsl_json,
                "compiled_meta": flow_version.compiled_meta,
                "published": flow_version.published,
                "created_at": flow_version.created_at.isoformat() if flow_version.created_at else None
            }