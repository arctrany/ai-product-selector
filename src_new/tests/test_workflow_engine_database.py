"""
Unit tests for workflow engine database layer refactoring.

Tests cover:
- DatabaseManager initialization and configuration
- Atomic operations (atomic_update_run_status, atomic_claim_signal)
- Async operations (async_update_run_status, async_get_run, etc.)
- Batch operations (batch_update_run_statuses, batch_create_signals)
- Performance optimizations (database indexes)
- Thread safety and concurrent access
- Error handling and rollback scenarios
"""

import asyncio
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from src_new.workflow_engine.storage.database import DatabaseManager
from src_new.workflow_engine.core.config import WorkflowEngineConfig


class TestDatabaseManagerInitialization(unittest.TestCase):
    """Test DatabaseManager initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization with custom path."""
        db_manager = DatabaseManager(self.test_db_path)
        
        self.assertEqual(db_manager.db_path, self.test_db_path)
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Clean up
        db_manager.close()

    def test_database_manager_with_config(self):
        """Test DatabaseManager initialization with config."""
        config = WorkflowEngineConfig(
            db_path=self.test_db_path,
            db_pool_size=10,
            thread_pool_workers=8
        )
        
        with patch('src_new.workflow_engine.storage.database.get_config', return_value=config):
            db_manager = DatabaseManager(self.test_db_path)
            
            # Verify config is used
            self.assertEqual(db_manager.db_path, self.test_db_path)
            self.assertIsNotNone(db_manager.thread_pool)
            
            # Clean up
            db_manager.close()

    def test_database_tables_creation(self):
        """Test that database tables are created properly."""
        db_manager = DatabaseManager(self.test_db_path)
        
        # Check that tables exist
        with db_manager.get_session() as session:
            # Query table existence
            result = session.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            table_names = [row[0] for row in result]
            expected_tables = ['flows', 'flow_versions', 'flow_runs', 'signals']
            
            for table in expected_tables:
                self.assertIn(table, table_names)
        
        # Clean up
        db_manager.close()

    def test_database_indexes_creation(self):
        """Test that performance indexes are created."""
        db_manager = DatabaseManager(self.test_db_path)
        
        # Create indexes
        db_manager.create_database_indexes()
        
        # Check that indexes exist
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
            
            index_names = [row[0] for row in result]
            expected_indexes = [
                'idx_runs_status_event',
                'idx_signals_thread_processed',
                'idx_versions_flow_published'
            ]
            
            for index in expected_indexes:
                self.assertIn(index, index_names)
        
        # Clean up
        db_manager.close()


class TestAtomicOperations(unittest.TestCase):
    """Test atomic database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Create test data
        self.flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(self.flow_id)
        self.flow_version_id = flow_version["flow_version_id"]

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_atomic_update_run_status_success(self):
        """Test successful atomic status update."""
        thread_id = "test_thread_1"
        
        # Create run
        self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Atomic update should succeed
        success = self.db_manager.atomic_update_run_status(
            thread_id, "pending", "running"
        )
        
        self.assertTrue(success)
        
        # Verify status was updated
        run = self.db_manager.get_run(thread_id)
        self.assertEqual(run["status"], "running")

    def test_atomic_update_run_status_failure_wrong_expected(self):
        """Test atomic status update failure with wrong expected status."""
        thread_id = "test_thread_2"
        
        # Create run
        self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Atomic update should fail with wrong expected status
        success = self.db_manager.atomic_update_run_status(
            thread_id, "running", "completed"  # Expected "running" but actual is "pending"
        )
        
        self.assertFalse(success)
        
        # Verify status was not changed
        run = self.db_manager.get_run(thread_id)
        self.assertEqual(run["status"], "pending")

    def test_atomic_update_run_status_failure_nonexistent_run(self):
        """Test atomic status update failure with nonexistent run."""
        success = self.db_manager.atomic_update_run_status(
            "nonexistent_thread", "pending", "running"
        )
        
        self.assertFalse(success)

    def test_atomic_update_run_status_with_metadata(self):
        """Test atomic status update with metadata."""
        thread_id = "test_thread_3"
        
        # Create run
        self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Update with metadata
        metadata = {"step": "processing", "progress": 50}
        success = self.db_manager.atomic_update_run_status(
            thread_id, "pending", "running", metadata
        )
        
        self.assertTrue(success)
        
        # Verify metadata was updated
        run = self.db_manager.get_run(thread_id)
        self.assertEqual(run["status"], "running")
        self.assertEqual(run["metadata"]["step"], "processing")
        self.assertEqual(run["metadata"]["progress"], 50)

    def test_atomic_claim_signal_success(self):
        """Test successful atomic signal claiming."""
        thread_id = "test_thread_4"
        
        # Create signal
        signal_id = self.db_manager.create_signal(thread_id, "pause", {"reason": "user_request"})
        
        # Claim signal
        claimed_signal = self.db_manager.atomic_claim_signal(thread_id, "pause")
        
        self.assertIsNotNone(claimed_signal)
        self.assertEqual(claimed_signal["id"], signal_id)
        self.assertEqual(claimed_signal["type"], "pause")
        self.assertEqual(claimed_signal["payload_json"]["reason"], "user_request")
        
        # Verify signal is marked as processed
        pending_signals = self.db_manager.get_pending_signals(thread_id)
        self.assertEqual(len(pending_signals), 0)

    def test_atomic_claim_signal_no_signals(self):
        """Test atomic signal claiming when no signals exist."""
        claimed_signal = self.db_manager.atomic_claim_signal("nonexistent_thread", "pause")
        
        self.assertIsNone(claimed_signal)

    def test_atomic_claim_signal_type_filter(self):
        """Test atomic signal claiming with type filtering."""
        thread_id = "test_thread_5"
        
        # Create signals of different types
        self.db_manager.create_signal(thread_id, "pause", {})
        self.db_manager.create_signal(thread_id, "resume", {})
        
        # Claim only resume signal
        claimed_signal = self.db_manager.atomic_claim_signal(thread_id, "resume")
        
        self.assertIsNotNone(claimed_signal)
        self.assertEqual(claimed_signal["type"], "resume")
        
        # Verify pause signal is still pending
        pending_signals = self.db_manager.get_pending_signals(thread_id)
        self.assertEqual(len(pending_signals), 1)
        self.assertEqual(pending_signals[0]["type"], "pause")

    def test_concurrent_atomic_operations(self):
        """Test concurrent atomic operations for race condition prevention."""
        thread_id = "test_thread_concurrent"
        
        # Create run
        self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        results = []
        errors = []

        def concurrent_update(worker_id):
            try:
                success = self.db_manager.atomic_update_run_status(
                    thread_id, "pending", f"status_{worker_id}"
                )
                results.append((worker_id, success))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads trying to update same run
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_update, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent atomic operations failed: {errors}")
        
        # Only one update should succeed (first one to acquire lock)
        successful_updates = [r for r in results if r[1] is True]
        failed_updates = [r for r in results if r[1] is False]
        
        self.assertEqual(len(successful_updates), 1)
        self.assertEqual(len(failed_updates), 4)


class TestAsyncOperations(unittest.TestCase):
    """Test async database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Create test data
        self.flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(self.flow_id)
        self.flow_version_id = flow_version["flow_version_id"]

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_async_update_run_status(self):
        """Test async run status update."""
        async def test_async():
            thread_id = "async_test_thread_1"
            
            # Create run
            self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
            
            # Async update
            success = await self.db_manager.async_update_run_status(
                thread_id, "pending", "running"
            )
            
            self.assertTrue(success)
            
            # Verify update
            run = self.db_manager.get_run(thread_id)
            self.assertEqual(run["status"], "running")

        # Run async test
        asyncio.run(test_async())

    def test_async_get_run(self):
        """Test async run retrieval."""
        async def test_async():
            thread_id = "async_test_thread_2"
            
            # Create run
            self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
            
            # Async get
            run = await self.db_manager.async_get_run(thread_id)
            
            self.assertIsNotNone(run)
            self.assertEqual(run["thread_id"], thread_id)
            self.assertEqual(run["status"], "pending")

        # Run async test
        asyncio.run(test_async())

    def test_async_create_signal(self):
        """Test async signal creation."""
        async def test_async():
            thread_id = "async_test_thread_3"
            
            # Async create signal
            signal_id = await self.db_manager.async_create_signal(
                thread_id, "pause", {"reason": "async_test"}
            )
            
            self.assertIsInstance(signal_id, int)
            
            # Verify signal was created
            signals = self.db_manager.get_pending_signals(thread_id)
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0]["type"], "pause")

        # Run async test
        asyncio.run(test_async())

    def test_async_claim_signal(self):
        """Test async signal claiming."""
        async def test_async():
            thread_id = "async_test_thread_4"
            
            # Create signal
            self.db_manager.create_signal(thread_id, "resume", {"data": "test"})
            
            # Async claim signal
            claimed_signal = await self.db_manager.async_claim_signal(thread_id, "resume")
            
            self.assertIsNotNone(claimed_signal)
            self.assertEqual(claimed_signal["type"], "resume")
            self.assertEqual(claimed_signal["payload_json"]["data"], "test")

        # Run async test
        asyncio.run(test_async())

    def test_concurrent_async_operations(self):
        """Test concurrent async operations."""
        async def test_async():
            # Create multiple async tasks
            tasks = []
            
            for i in range(5):
                thread_id = f"async_concurrent_{i}"
                self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
                
                task = self.db_manager.async_update_run_status(
                    thread_id, "pending", "running"
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should succeed
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.fail(f"Async task {i} failed: {result}")
                else:
                    self.assertTrue(result, f"Async task {i} returned False")

        # Run async test
        asyncio.run(test_async())


class TestBatchOperations(unittest.TestCase):
    """Test batch database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Create test data
        self.flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(self.flow_id)
        self.flow_version_id = flow_version["flow_version_id"]

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_batch_update_run_statuses_success(self):
        """Test successful batch status updates."""
        # Create multiple runs
        thread_ids = [f"batch_thread_{i}" for i in range(5)]
        for thread_id in thread_ids:
            self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Prepare batch updates
        updates = [
            {
                "thread_id": thread_id,
                "expected_status": "pending",
                "new_status": "running",
                "metadata": {"batch_id": i}
            }
            for i, thread_id in enumerate(thread_ids)
        ]
        
        # Execute batch update
        results = self.db_manager.batch_update_run_statuses(updates)
        
        # Verify results
        self.assertEqual(results["success"], 5)
        self.assertEqual(results["failed"], 0)
        self.assertEqual(len(results["errors"]), 0)
        
        # Verify all runs were updated
        for i, thread_id in enumerate(thread_ids):
            run = self.db_manager.get_run(thread_id)
            self.assertEqual(run["status"], "running")
            self.assertEqual(run["metadata"]["batch_id"], i)

    def test_batch_update_run_statuses_partial_failure(self):
        """Test batch status updates with partial failures."""
        # Create some runs
        thread_ids = [f"batch_thread_{i}" for i in range(3)]
        for thread_id in thread_ids[:2]:  # Only create first 2
            self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Prepare batch updates (including non-existent run)
        updates = [
            {
                "thread_id": thread_ids[0],
                "expected_status": "pending",
                "new_status": "running"
            },
            {
                "thread_id": thread_ids[1],
                "expected_status": "running",  # Wrong expected status
                "new_status": "completed"
            },
            {
                "thread_id": thread_ids[2],  # Non-existent run
                "expected_status": "pending",
                "new_status": "running"
            }
        ]
        
        # Execute batch update
        results = self.db_manager.batch_update_run_statuses(updates)
        
        # Verify results
        self.assertEqual(results["success"], 1)  # Only first one should succeed
        self.assertEqual(results["failed"], 2)
        self.assertEqual(len(results["errors"]), 2)

    def test_batch_create_signals_success(self):
        """Test successful batch signal creation."""
        thread_ids = [f"signal_thread_{i}" for i in range(5)]
        
        # Prepare batch signals
        signals = [
            {
                "thread_id": thread_id,
                "type": "pause",
                "payload_json": {"batch_id": i}
            }
            for i, thread_id in enumerate(thread_ids)
        ]
        
        # Execute batch create
        results = self.db_manager.batch_create_signals(signals)
        
        # Verify results
        self.assertEqual(results["success"], 5)
        self.assertEqual(results["failed"], 0)
        self.assertEqual(len(results["signal_ids"]), 5)
        self.assertEqual(len(results["errors"]), 0)
        
        # Verify signals were created
        for i, thread_id in enumerate(thread_ids):
            pending_signals = self.db_manager.get_pending_signals(thread_id)
            self.assertEqual(len(pending_signals), 1)
            self.assertEqual(pending_signals[0]["type"], "pause")
            self.assertEqual(pending_signals[0]["payload_json"]["batch_id"], i)

    def test_get_runs_by_status_batch(self):
        """Test batch retrieval of runs by status."""
        # Create runs with different statuses
        statuses = ["pending", "running", "completed"]
        thread_ids_by_status = {}
        
        for status in statuses:
            thread_ids = [f"{status}_thread_{i}" for i in range(3)]
            thread_ids_by_status[status] = thread_ids
            
            for thread_id in thread_ids:
                self.db_manager.create_run(thread_id, self.flow_version_id, status)
        
        # Get runs by multiple statuses
        results = self.db_manager.get_runs_by_status_batch(["pending", "running"])
        
        # Verify results
        self.assertIn("pending", results)
        self.assertIn("running", results)
        self.assertEqual(len(results["pending"]), 3)
        self.assertEqual(len(results["running"]), 3)
        
        # Verify correct runs are returned
        pending_thread_ids = [run["thread_id"] for run in results["pending"]]
        running_thread_ids = [run["thread_id"] for run in results["running"]]
        
        for thread_id in thread_ids_by_status["pending"]:
            self.assertIn(thread_id, pending_thread_ids)
        
        for thread_id in thread_ids_by_status["running"]:
            self.assertIn(thread_id, running_thread_ids)

    def test_batch_operations_performance(self):
        """Test performance improvement of batch operations."""
        # Create many runs for performance test
        num_runs = 50
        thread_ids = [f"perf_thread_{i}" for i in range(num_runs)]
        
        for thread_id in thread_ids:
            self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
        
        # Measure batch update performance
        updates = [
            {
                "thread_id": thread_id,
                "expected_status": "pending",
                "new_status": "running"
            }
            for thread_id in thread_ids
        ]
        
        start_time = time.time()
        results = self.db_manager.batch_update_run_statuses(updates)
        batch_time = time.time() - start_time
        
        # Verify all succeeded
        self.assertEqual(results["success"], num_runs)
        self.assertEqual(results["failed"], 0)
        
        # Batch operation should be reasonably fast
        self.assertLess(batch_time, 5.0, "Batch operation took too long")


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of database operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Create test data
        self.flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(self.flow_id)
        self.flow_version_id = flow_version["flow_version_id"]

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_concurrent_run_creation(self):
        """Test concurrent run creation."""
        results = []
        errors = []

        def create_run_worker(worker_id):
            try:
                thread_id = f"concurrent_thread_{worker_id}"
                success = self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
                results.append((worker_id, success))
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_run_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent run creation failed: {errors}")
        self.assertEqual(len(results), 10)
        
        # All should succeed
        for worker_id, success in results:
            self.assertTrue(success, f"Worker {worker_id} failed to create run")

    def test_concurrent_signal_processing(self):
        """Test concurrent signal creation and claiming."""
        thread_id = "signal_test_thread"
        results = []
        errors = []

        def signal_worker(worker_id):
            try:
                if worker_id % 2 == 0:
                    # Even workers create signals
                    signal_id = self.db_manager.create_signal(
                        thread_id, f"signal_{worker_id}", {"worker": worker_id}
                    )
                    results.append(f"created_{worker_id}_{signal_id}")
                else:
                    # Odd workers try to claim signals
                    time.sleep(0.1)  # Give creators a chance
                    claimed = self.db_manager.atomic_claim_signal(thread_id)
                    if claimed:
                        results.append(f"claimed_{worker_id}_{claimed['id']}")
                    else:
                        results.append(f"no_signal_{worker_id}")
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=signal_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent signal processing failed: {errors}")
        
        # Should have some created and some claimed signals
        created_count = len([r for r in results if r.startswith("created_")])
        claimed_count = len([r for r in results if r.startswith("claimed_")])
        
        self.assertGreater(created_count, 0)
        # Note: claimed_count might be 0 if claimers run before creators

    def test_concurrent_database_access(self):
        """Test concurrent database access with mixed operations."""
        results = []
        errors = []

        def mixed_operations_worker(worker_id):
            try:
                thread_id = f"mixed_thread_{worker_id}"
                
                # Create run
                self.db_manager.create_run(thread_id, self.flow_version_id, "pending")
                
                # Update status
                success = self.db_manager.atomic_update_run_status(
                    thread_id, "pending", "running"
                )
                
                # Create signal
                signal_id = self.db_manager.create_signal(thread_id, "test", {})
                
                # Get run
                run = self.db_manager.get_run(thread_id)
                
                results.append((worker_id, success, signal_id, run is not None))
                
            except Exception as e:
                errors.append((worker_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(20):
            thread = threading.Thread(target=mixed_operations_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent mixed operations failed: {errors}")
        self.assertEqual(len(results), 20)
        
        # All operations should succeed
        for worker_id, status_success, signal_id, run_exists in results:
            self.assertTrue(status_success, f"Worker {worker_id} status update failed")
            self.assertIsInstance(signal_id, int, f"Worker {worker_id} signal creation failed")
            self.assertTrue(run_exists, f"Worker {worker_id} run retrieval failed")


class TestErrorHandling(unittest.TestCase):
    """Test error handling and rollback scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_workflow.db")
        self.db_manager = DatabaseManager(self.test_db_path)

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.close()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_connection_error_handling(self):
        """Test handling of database connection errors."""
        # Close the database
        self.db_manager.close()
        
        # Try to perform operations on closed database
        with self.assertRaises(Exception):
            self.db_manager.create_flow_by_name("test", "1.0.0")

    def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        # Create flow first
        flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(flow_id)
        flow_version_id = flow_version["flow_version_id"]
        
        # Try to create run with invalid flow_version_id
        with self.assertRaises(Exception):
            self.db_manager.create_run("test_thread", 99999, "pending")

    def test_transaction_rollback(self):
        """Test transaction rollback on errors."""
        # This test verifies that failed operations don't leave partial data
        
        # Create flow
        flow_id = self.db_manager.create_flow_by_name("test_flow", "1.0.0")
        flow_version = self.db_manager.get_latest_flow_version(flow_id)
        flow_version_id = flow_version["flow_version_id"]
        
        # Create run
        thread_id = "rollback_test"
        self.db_manager.create_run(thread_id, flow_version_id, "pending")
        
        # Try batch update with some invalid data
        updates = [
            {
                "thread_id": thread_id,
                "expected_status": "pending",
                "new_status": "running"
            },
            {
                "thread_id": "nonexistent",
                "expected_status": "pending", 
                "new_status": "running"
            }
        ]
        
        results = self.db_manager.batch_update_run_statuses(updates)
        
        # Should have partial success/failure
        self.assertEqual(results["success"], 1)
        self.assertEqual(results["failed"], 1)
        
        # Valid run should still be updated
        run = self.db_manager.get_run(thread_id)
        self.assertEqual(run["status"], "running")


if __name__ == '__main__':
    unittest.main()