"""
Performance benchmarks for Excel calculation engines
"""

import time
import unittest
import statistics
from typing import List

from common.models import ProfitCalculatorInput
from common.excel_engine import create_engine


class TestEnginePerformance(unittest.TestCase):
    """Benchmark different calculation engines"""
    
    def setUp(self):
        """Setup test data"""
        # Create test inputs
        self.test_inputs = []
        for i in range(100):
            self.test_inputs.append(ProfitCalculatorInput(
                black_price=100.0 + i * 0.5,
                green_price=80.0 + i * 0.5,
                list_price=76.0 + i * 0.475,
                purchase_price=40.0 + i * 0.25,
                commission_rate=10.0 + (i % 5),
                weight=300.0 + i * 10,
                length=10.0,
                width=10.0,
                height=10.0
            ))
            
    def benchmark_engine(self, engine_type: str, iterations: int = 100) -> dict:
        """Benchmark a specific engine"""
        try:
            engine = create_engine(engine_type)
        except Exception as e:
            return {
                'engine': engine_type,
                'error': str(e),
                'available': False
            }
            
        # Warmup
        for _ in range(5):
            engine.calculate_profit(self.test_inputs[0])
            
        # Benchmark
        times = []
        for i in range(iterations):
            input_data = self.test_inputs[i % len(self.test_inputs)]
            
            start = time.perf_counter()
            result = engine.calculate_profit(input_data)
            end = time.perf_counter()
            
            times.append(end - start)
            
        # Calculate statistics
        return {
            'engine': engine_type,
            'available': True,
            'iterations': iterations,
            'mean_time': statistics.mean(times),
            'median_time': statistics.median(times),
            'min_time': min(times),
            'max_time': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0,
            'throughput': iterations / sum(times)  # calculations per second
        }
        
    def test_python_engine_performance(self):
        """Test Python engine performance"""
        results = self.benchmark_engine('python')
        
        self.assertTrue(results['available'])
        print(f"\nPython Engine Performance:")
        print(f"  Mean time: {results['mean_time']*1000:.2f}ms")
        print(f"  Throughput: {results['throughput']:.1f} calc/s")
        
        # Python engine should be fast
        self.assertLess(results['mean_time'], 0.01)  # Less than 10ms
        
    def test_compare_engines(self):
        """Compare all available engines"""
        engines_to_test = ['python', 'xlwings', 'formulas']
        results = []
        
        print("\n=== Engine Performance Comparison ===")
        
        for engine_type in engines_to_test:
            result = self.benchmark_engine(engine_type, iterations=50)
            results.append(result)
            
            if result['available']:
                print(f"\n{engine_type.capitalize()} Engine:")
                print(f"  Mean time: {result['mean_time']*1000:.2f}ms")
                print(f"  Median time: {result['median_time']*1000:.2f}ms")
                print(f"  Min/Max: {result['min_time']*1000:.2f}ms / {result['max_time']*1000:.2f}ms")
                print(f"  Throughput: {result['throughput']:.1f} calculations/second")
            else:
                print(f"\n{engine_type.capitalize()} Engine: Not available ({result['error']})")
                
        # Find fastest available engine
        available_results = [r for r in results if r['available']]
        if available_results:
            fastest = min(available_results, key=lambda x: x['mean_time'])
            print(f"\nFastest engine: {fastest['engine']} ({fastest['mean_time']*1000:.2f}ms mean)")
            
    def test_batch_processing_performance(self):
        """Test batch processing performance"""
        engine = create_engine('python')
        
        # Single calculations
        start = time.perf_counter()
        for input_data in self.test_inputs[:50]:
            engine.calculate_profit(input_data)
        single_time = time.perf_counter() - start
        
        # Batch calculation (if supported)
        if hasattr(engine, 'batch_calculate'):
            start = time.perf_counter()
            results = engine.batch_calculate(self.test_inputs[:50])
            batch_time = time.perf_counter() - start
            
            print(f"\nBatch Processing Performance:")
            print(f"  Single: {single_time:.3f}s for 50 items")
            print(f"  Batch: {batch_time:.3f}s for 50 items")
            print(f"  Speedup: {single_time/batch_time:.1f}x")
            
            # Batch should be at least as fast
            self.assertLessEqual(batch_time, single_time * 1.1)  # Allow 10% margin
            
    def test_memory_usage(self):
        """Test memory usage patterns"""
        import gc
        import sys
        
        engine = create_engine('python')
        
        # Force garbage collection
        gc.collect()
        
        # Get initial memory
        initial_objects = len(gc.get_objects())
        
        # Perform many calculations
        for _ in range(1000):
            engine.calculate_profit(self.test_inputs[0])
            
        # Check memory growth
        gc.collect()
        final_objects = len(gc.get_objects())
        
        growth = final_objects - initial_objects
        print(f"\nMemory Usage:")
        print(f"  Object count growth: {growth}")
        
        # Should not have excessive memory growth
        self.assertLess(growth, 1000)  # Arbitrary threshold


if __name__ == '__main__':
    unittest.main(verbosity=2)