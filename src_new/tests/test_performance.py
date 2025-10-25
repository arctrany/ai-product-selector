"""Performance tests for workflow engine components."""

import pytest
import time
import asyncio
import threading
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import statistics

# Import workflow engine components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from workflow_engine.core.engine import WorkflowEngine
from workflow_engine.core.config import WorkflowEngineConfig
from workflow_engine.storage.database import DatabaseManager
from workflow_engine.core.models import WorkflowDefinition, NodeDefinition, NodeType


class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.fixture
    def perf_db_manager(self):
        """Create database manager for performance testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_manager = DatabaseManager(db_path)
        yield db_manager
        Path(db_path).unlink(missing_ok=True)

    def test_bulk_flow_creation_performance(self, perf_db_manager):
        """Test performance of bulk flow creation."""
        num_flows = 100
        start_time = time.time()
        
        flow_ids = []
        for i in range(num_flows):
            flow_id = perf_db_manager.create_flow_by_name(
                flow_name=f"perf-flow-{i}",
                version="1.0.0",
                dsl_json={"nodes": [{"id": f"node-{i}"}], "edges": []},
                published=True
            )
            flow_ids.append(flow_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert len(flow_ids) == num_flows
        assert duration < 10.0, f"Bulk creation took too long: {duration:.2f}s"
        assert len(set(flow_ids)) == num_flows, "Duplicate flow IDs generated"
        
        # Calculate throughput
        throughput = num_flows / duration
        print(f"Flow creation throughput: {throughput:.2f} flows/second")
        assert throughput > 10, f"Throughput too low: {throughput:.2f} flows/second"

    def test_concurrent_run_operations_performance(self, perf_db_manager):
        """Test performance of concurrent run operations."""
        # Create a flow first
        flow_id = perf_db_manager.create_flow_by_name(
            flow_name="concurrent-perf-flow",
            version="1.0.0",
            dsl_json={"nodes": [], "edges": []},
            published=True
        )
        
        num_threads = 20
        operations_per_thread = 10
        
        def run_operations(thread_id):
            """Perform database operations in a thread."""
            times = []
            for i in range(operations_per_thread):
                start = time.time()
                
                thread_run_id = f"perf-thread-{thread_id}-{i}"
                
                # Create run
                perf_db_manager.create_run(
                    thread_run_id, flow_id, "pending", {"thread_id": thread_id, "op": i}
                )
                
                # Update status
                perf_db_manager.atomic_update_run_status(
                    thread_run_id, "pending", "running"
                )
                
                # Add log
                perf_db_manager.add_run_log(
                    thread_run_id, "info", f"Operation {i} completed", {"thread": thread_id}
                )
                
                # Get run
                run = perf_db_manager.get_run(thread_run_id)
                assert run is not None
                
                end = time.time()
                times.append(end - start)
            
            return times
        
        # Execute concurrent operations
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(run_operations, thread_id)
                for thread_id in range(num_threads)
            ]
            
            all_times = []
            for future in as_completed(futures):
                thread_times = future.result()
                all_times.extend(thread_times)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Performance analysis
        total_operations = num_threads * operations_per_thread
        throughput = total_operations / total_duration
        avg_operation_time = statistics.mean(all_times)
        p95_operation_time = statistics.quantiles(all_times, n=20)[18]  # 95th percentile
        
        print(f"Concurrent operations throughput: {throughput:.2f} ops/second")
        print(f"Average operation time: {avg_operation_time*1000:.2f}ms")
        print(f"95th percentile operation time: {p95_operation_time*1000:.2f}ms")
        
        # Performance assertions
        assert throughput > 50, f"Concurrent throughput too low: {throughput:.2f} ops/second"
        assert avg_operation_time < 0.5, f"Average operation time too high: {avg_operation_time:.3f}s"
        assert p95_operation_time < 1.0, f"95th percentile too high: {p95_operation_time:.3f}s"

    def test_large_dataset_query_performance(self, perf_db_manager):
        """Test query performance with large datasets."""
        # Create large dataset
        num_flows = 50
        runs_per_flow = 20
        
        print("Creating large dataset for query performance test...")
        flow_ids = []
        for i in range(num_flows):
            flow_id = perf_db_manager.create_flow_by_name(
                flow_name=f"large-dataset-flow-{i}",
                version="1.0.0",
                dsl_json={"nodes": [], "edges": []},
                published=True
            )
            flow_ids.append(flow_id)
            
            # Create multiple runs for each flow
            for j in range(runs_per_flow):
                thread_id = f"large-dataset-thread-{i}-{j}"
                perf_db_manager.create_run(
                    thread_id, flow_id, "completed", {"flow_index": i, "run_index": j}
                )
        
        # Test query performance
        query_times = []
        
        # Test 1: Get flow by name
        for i in range(10):  # Test multiple queries
            start = time.time()
            flow = perf_db_manager.get_flow_by_name(f"large-dataset-flow-{i}")
            end = time.time()
            assert flow is not None
            query_times.append(end - start)
        
        # Test 2: Get runs (this would typically return multiple results)
        for flow_id in flow_ids[:10]:
            start = time.time()
            # Simulate getting runs for a flow (would need custom query method)
            # For now, test individual run retrieval
            for j in range(5):  # Test subset
                thread_id = f"large-dataset-thread-{flow_ids.index(flow_id)}-{j}"
                run = perf_db_manager.get_run(thread_id)
                assert run is not None
            end = time.time()
            query_times.append(end - start)
        
        # Performance analysis
        avg_query_time = statistics.mean(query_times)
        max_query_time = max(query_times)
        
        print(f"Average query time: {avg_query_time*1000:.2f}ms")
        print(f"Maximum query time: {max_query_time*1000:.2f}ms")
        
        # Performance assertions
        assert avg_query_time < 0.1, f"Average query time too high: {avg_query_time:.3f}s"
        assert max_query_time < 0.5, f"Maximum query time too high: {max_query_time:.3f}s"


class TestWorkflowEnginePerformance:
    """Performance tests for workflow engine operations."""

    @pytest.fixture
    def perf_engine(self):
        """Create workflow engine for performance testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False,
            thread_pool_workers=8,
            batch_size=50
        )
        engine = WorkflowEngine(config=config)
        yield engine
        Path(db_path).unlink(missing_ok=True)

    def test_workflow_compilation_performance(self, perf_engine):
        """Test workflow compilation performance."""
        # Create workflows of varying complexity
        test_cases = [
            ("simple", 2, 1),      # 2 nodes, 1 edge
            ("medium", 10, 9),     # 10 nodes, 9 edges (linear)
            ("complex", 20, 30),   # 20 nodes, 30 edges (more complex)
        ]
        
        compilation_times = {}
        
        for case_name, num_nodes, num_edges in test_cases:
            # Create workflow definition
            nodes = [
                NodeDefinition(id="start", type=NodeType.START, config={})
            ]
            
            # Add intermediate nodes
            for i in range(1, num_nodes - 1):
                nodes.append(NodeDefinition(
                    id=f"node_{i}",
                    type=NodeType.PYTHON,
                    config={"code": f"return {{'step': {i}, 'data': data}}"}
                ))
            
            nodes.append(NodeDefinition(id="end", type=NodeType.END, config={}))
            
            # Create edges (simplified - linear + some additional for complex case)
            edges = []
            for i in range(num_nodes - 1):
                edges.append({"from": nodes[i].id, "to": nodes[i + 1].id})
            
            # Add extra edges for complex case
            if case_name == "complex" and num_nodes > 10:
                for i in range(2, min(num_nodes - 2, 10)):
                    edges.append({"from": f"node_{i}", "to": f"node_{i + 5}"})
            
            definition = WorkflowDefinition(nodes=nodes, edges=edges[:num_edges])
            
            # Measure compilation time
            start_time = time.time()
            graph = perf_engine.compile_workflow(definition)
            end_time = time.time()
            
            compilation_time = end_time - start_time
            compilation_times[case_name] = compilation_time
            
            assert graph is not None
            print(f"{case_name.capitalize()} workflow compilation: {compilation_time*1000:.2f}ms")
        
        # Performance assertions
        assert compilation_times["simple"] < 0.1, "Simple workflow compilation too slow"
        assert compilation_times["medium"] < 0.5, "Medium workflow compilation too slow"
        assert compilation_times["complex"] < 2.0, "Complex workflow compilation too slow"

    def test_concurrent_workflow_execution_performance(self, perf_engine):
        """Test concurrent workflow execution performance."""
        # Create simple workflow for testing
        definition = WorkflowDefinition(
            nodes=[
                NodeDefinition(id="start", type=NodeType.START, config={}),
                NodeDefinition(
                    id="process",
                    type=NodeType.PYTHON,
                    config={"code": "import time; time.sleep(0.01); return {'processed': True}"}
                ),
                NodeDefinition(id="end", type=NodeType.END, config={})
            ],
            edges=[
                {"from": "start", "to": "process"},
                {"from": "process", "to": "end"}
            ]
        )
        
        flow_version_id = perf_engine.create_flow("perf-concurrent-flow", definition, "1.0.0")
        
        num_concurrent_workflows = 10
        
        def start_workflow(workflow_index):
            """Start a workflow and measure execution time."""
            with patch('workflow_engine.core.engine.get_container') as mock_container:
                mock_app_manager = Mock()
                mock_app_manager.load_workflow_definition.return_value = None
                mock_container.return_value.get.return_value = mock_app_manager
                
                start_time = time.time()
                thread_id = perf_engine.start_workflow(
                    flow_version_id=flow_version_id,
                    input_data={"workflow_index": workflow_index}
                )
                end_time = time.time()
                
                return thread_id, end_time - start_time
        
        # Execute workflows concurrently
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent_workflows) as executor:
            futures = [
                executor.submit(start_workflow, i)
                for i in range(num_concurrent_workflows)
            ]
            
            results = []
            for future in as_completed(futures):
                thread_id, execution_time = future.result()
                results.append((thread_id, execution_time))
        
        total_time = time.time() - start_time
        
        # Performance analysis
        execution_times = [result[1] for result in results]
        avg_execution_time = statistics.mean(execution_times)
        throughput = num_concurrent_workflows / total_time
        
        print(f"Concurrent workflow throughput: {throughput:.2f} workflows/second")
        print(f"Average workflow start time: {avg_execution_time*1000:.2f}ms")
        
        # Performance assertions
        assert len(results) == num_concurrent_workflows, "Not all workflows completed"
        assert throughput > 5, f"Concurrent throughput too low: {throughput:.2f} workflows/second"
        assert avg_execution_time < 1.0, f"Average execution time too high: {avg_execution_time:.3f}s"


class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.fixture
    def perf_client(self):
        """Create test client for performance testing."""
        from fastapi.testclient import TestClient
        from workflow_engine.api.server import create_app
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        config = WorkflowEngineConfig(
            db_path=db_path,
            checkpoint_enabled=False
        )
        
        app = create_app(config=config)
        client = TestClient(app)
        yield client
        Path(db_path).unlink(missing_ok=True)

    def test_api_response_time_performance(self, perf_client):
        """Test API response time performance."""
        # Mock dependencies for consistent testing
        with patch('workflow_engine.api.dependencies.get_database_manager') as mock_db, \
             patch('workflow_engine.api.dependencies.get_workflow_engine') as mock_engine, \
             patch('workflow_engine.api.dependencies.get_workflow_control') as mock_control:
            
            # Setup mocks
            mock_db_instance = Mock()
            mock_db_instance.get_flow_by_name.return_value = {"flow_id": 1, "name": "test-flow"}
            mock_db_instance.get_latest_flow_version.return_value = {"flow_version_id": 1, "version": "1.0.0"}
            mock_db_instance.get_run.return_value = {"thread_id": "test-123", "status": "running", "flow_version_id": 1}
            mock_db.return_value = mock_db_instance
            
            mock_engine_instance = Mock()
            mock_engine_instance.start_workflow.return_value = "test-thread-123"
            mock_engine.return_value = mock_engine_instance
            
            mock_control_instance = Mock()
            mock_control_instance.pause_workflow.return_value = True
            mock_control.return_value = mock_control_instance
            
            # Test different API endpoints
            endpoints = [
                ("POST", "/api/flows/test-flow/start", {"input_data": {"test": "value"}}),
                ("GET", "/api/thread/test-123/status", None),
                ("POST", "/api/thread/test-123/pause", None),
                ("GET", "/api/thread/test-123/logs", None),
            ]
            
            response_times = {}
            
            for method, endpoint, data in endpoints:
                times = []
                
                # Test each endpoint multiple times
                for _ in range(20):
                    start_time = time.time()
                    
                    if method == "POST":
                        response = perf_client.post(endpoint, json=data or {})
                    else:
                        response = perf_client.get(endpoint)
                    
                    end_time = time.time()
                    
                    # Verify response is successful
                    assert response.status_code in [200, 201], f"Failed request to {endpoint}: {response.status_code}"
                    
                    times.append(end_time - start_time)
                
                # Calculate statistics
                avg_time = statistics.mean(times)
                p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
                response_times[endpoint] = {"avg": avg_time, "p95": p95_time}
                
                print(f"{method} {endpoint}: avg={avg_time*1000:.2f}ms, p95={p95_time*1000:.2f}ms")
            
            # Performance assertions
            for endpoint, times in response_times.items():
                assert times["avg"] < 0.1, f"Average response time too high for {endpoint}: {times['avg']:.3f}s"
                assert times["p95"] < 0.2, f"95th percentile too high for {endpoint}: {times['p95']:.3f}s"

    def test_api_concurrent_load_performance(self, perf_client):
        """Test API performance under concurrent load."""
        with patch('workflow_engine.api.dependencies.get_database_manager') as mock_db:
            # Setup mock
            mock_db_instance = Mock()
            mock_db_instance.get_run.return_value = {
                "thread_id": "load-test-123", 
                "status": "running", 
                "flow_version_id": 1
            }
            mock_db.return_value = mock_db_instance
            
            num_concurrent_requests = 50
            
            def make_request(request_id):
                """Make a single API request."""
                start_time = time.time()
                response = perf_client.get(f"/api/thread/load-test-{request_id}/status")
                end_time = time.time()
                
                return response.status_code, end_time - start_time
            
            # Execute concurrent requests
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [
                    executor.submit(make_request, i)
                    for i in range(num_concurrent_requests)
                ]
                
                results = []
                for future in as_completed(futures):
                    status_code, response_time = future.result()
                    results.append((status_code, response_time))
            
            total_time = time.time() - start_time
            
            # Analyze results
            successful_requests = [r for r in results if r[0] == 200]
            response_times = [r[1] for r in successful_requests]
            
            success_rate = len(successful_requests) / num_concurrent_requests
            throughput = len(successful_requests) / total_time
            avg_response_time = statistics.mean(response_times) if response_times else 0
            
            print(f"Concurrent load test results:")
            print(f"Success rate: {success_rate*100:.1f}%")
            print(f"Throughput: {throughput:.2f} requests/second")
            print(f"Average response time: {avg_response_time*1000:.2f}ms")
            
            # Performance assertions
            assert success_rate >= 0.95, f"Success rate too low: {success_rate*100:.1f}%"
            assert throughput > 100, f"Throughput too low: {throughput:.2f} requests/second"
            assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"


class TestMemoryPerformance:
    """Memory usage and leak detection tests."""

    def test_memory_usage_stability(self):
        """Test memory usage stability during operations."""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create temporary engine for memory testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            config = WorkflowEngineConfig(
                db_path=db_path,
                checkpoint_enabled=False
            )
            
            memory_samples = [initial_memory]
            
            # Perform operations that might cause memory leaks
            for iteration in range(10):
                engine = WorkflowEngine(config=config)
                
                # Create and compile workflows
                for i in range(10):
                    definition = WorkflowDefinition(
                        nodes=[
                            NodeDefinition(id="start", type=NodeType.START, config={}),
                            NodeDefinition(id="end", type=NodeType.END, config={})
                        ],
                        edges=[{"from": "start", "to": "end"}]
                    )
                    
                    flow_id = engine.create_flow(f"memory-test-{iteration}-{i}", definition)
                    graph = engine.compile_workflow(definition)
                
                # Force garbage collection
                del engine
                gc.collect()
                
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(current_memory)
                
                print(f"Iteration {iteration}: Memory usage: {current_memory:.2f} MB")
            
            # Analyze memory usage
            final_memory = memory_samples[-1]
            memory_growth = final_memory - initial_memory
            max_memory = max(memory_samples)
            
            print(f"Initial memory: {initial_memory:.2f} MB")
            print(f"Final memory: {final_memory:.2f} MB")
            print(f"Memory growth: {memory_growth:.2f} MB")
            print(f"Peak memory: {max_memory:.2f} MB")
            
            # Memory assertions (allow some growth but detect significant leaks)
            assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.2f} MB"
            assert max_memory < initial_memory + 100, f"Peak memory too high: {max_memory:.2f} MB"
            
        finally:
            Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])