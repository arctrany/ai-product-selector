#!/usr/bin/env python3
"""
Complete Test Runner
===================

This script runs all tests with proper environment configuration
and generates comprehensive reports.
"""

import os
import sys
import subprocess
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).resolve().parents[2]
src_path = project_root / "src_new"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import test environment configuration
try:
    from test_environment_config import setup_test_environment, auto_configure_test_environment
except ImportError:
    print("Warning: Could not import test environment config, using defaults")
    def setup_test_environment(env_type):
        return None
    def auto_configure_test_environment():
        return "test"

class TestRunner:
    """Complete test runner with environment management."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.datetime.now().isoformat(),
            "environment": auto_configure_test_environment(),
            "test_suites": {},
            "summary": {}
        }
        self.src_dir = src_path
    
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        
        test_file = self.src_dir / "tests" / "test_api_refactor.py"
        if not test_file.exists():
            return {"status": "skipped", "reason": "test file not found"}
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                str(test_file), 
                "-v", "--tb=short", "--no-header"
            ], 
            cwd=str(self.src_dir),
            capture_output=True, 
            text=True, 
            timeout=60
            )
            
            return {
                "status": "completed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "success": False}
        except Exception as e:
            return {"status": "error", "error": str(e), "success": False}
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        
        test_file = self.src_dir / "tests" / "test_integration_fixed.py"
        if not test_file.exists():
            return {"status": "skipped", "reason": "test file not found"}
        
        try:
            # Set up integration test environment
            with setup_test_environment("integration") as env:
                env_vars = os.environ.copy()
                if env:
                    config = env.get_config()
                    env_vars.update({
                        "TEST_DB_PATH": config.get("db_path", ":memory:"),
                        "TEST_ENVIRONMENT": "integration"
                    })
                
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(test_file), 
                    "-v", "--tb=short", "--no-header"
                ], 
                cwd=str(self.src_dir),
                env=env_vars,
                capture_output=True, 
                text=True, 
                timeout=120
                )
                
                return {
                    "status": "completed",
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "success": False}
        except Exception as e:
            return {"status": "error", "error": str(e), "success": False}
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        
        test_file = self.src_dir / "tests" / "test_performance.py"
        if not test_file.exists():
            return {"status": "skipped", "reason": "test file not found"}
        
        try:
            # Set up performance test environment
            with setup_test_environment("performance") as env:
                env_vars = os.environ.copy()
                if env:
                    config = env.get_config()
                    env_vars.update({
                        "TEST_DB_PATH": config.get("db_path", ":memory:"),
                        "TEST_ENVIRONMENT": "performance"
                    })
                
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    str(test_file), 
                    "-v", "--tb=short", "--no-header"
                ], 
                cwd=str(self.src_dir),
                env=env_vars,
                capture_output=True, 
                text=True, 
                timeout=180
                )
                
                return {
                    "status": "completed",
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "success": result.returncode == 0
                }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "success": False}
        except Exception as e:
            return {"status": "error", "error": str(e), "success": False}
    
    def analyze_test_output(self, output: str) -> Dict[str, Any]:
        """Analyze pytest output to extract test statistics."""
        lines = output.split('\n')
        
        stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "success_rate": 0
        }
        
        # Look for pytest summary line
        for line in lines:
            if "failed" in line and "passed" in line:
                # Parse line like "2 failed, 13 passed in 1.27s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "failed," and i > 0:
                        stats["failed"] = int(parts[i-1])
                    elif part == "passed" and i > 0:
                        stats["passed"] = int(parts[i-1])
                    elif part == "error," and i > 0:
                        stats["errors"] = int(parts[i-1])
                    elif part == "skipped," and i > 0:
                        stats["skipped"] = int(parts[i-1])
            elif "passed in" in line and "failed" not in line:
                # Parse line like "15 passed in 1.27s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        stats["passed"] = int(parts[i-1])
        
        stats["total"] = stats["passed"] + stats["failed"] + stats["errors"] + stats["skipped"]
        if stats["total"] > 0:
            stats["success_rate"] = round((stats["passed"] / stats["total"]) * 100, 1)
        
        return stats
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites."""
        print("🎯 Starting Complete Test Run")
        print("=" * 50)
        
        # Run unit tests
        unit_result = self.run_unit_tests()
        if unit_result.get("stdout"):
            unit_result["stats"] = self.analyze_test_output(unit_result["stdout"])
        self.results["test_suites"]["unit"] = unit_result
        
        # Run integration tests
        integration_result = self.run_integration_tests()
        if integration_result.get("stdout"):
            integration_result["stats"] = self.analyze_test_output(integration_result["stdout"])
        self.results["test_suites"]["integration"] = integration_result
        
        # Run performance tests
        performance_result = self.run_performance_tests()
        if performance_result.get("stdout"):
            performance_result["stats"] = self.analyze_test_output(performance_result["stdout"])
        self.results["test_suites"]["performance"] = performance_result
        
        # Calculate overall summary
        self._calculate_summary()
        
        return self.results
    
    def _calculate_summary(self):
        """Calculate overall test summary."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        successful_suites = 0
        total_suites = 0
        
        for suite_name, suite_result in self.results["test_suites"].items():
            total_suites += 1
            if suite_result.get("success"):
                successful_suites += 1
            
            stats = suite_result.get("stats", {})
            total_tests += stats.get("total", 0)
            total_passed += stats.get("passed", 0)
            total_failed += stats.get("failed", 0) + stats.get("errors", 0)
        
        overall_success_rate = 0
        if total_tests > 0:
            overall_success_rate = round((total_passed / total_tests) * 100, 1)
        
        self.results["summary"] = {
            "total_suites": total_suites,
            "successful_suites": successful_suites,
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_success_rate": overall_success_rate,
            "suite_success_rate": round((successful_suites / total_suites) * 100, 1) if total_suites > 0 else 0
        }
    
    def generate_report(self) -> str:
        """Generate human-readable test report."""
        summary = self.results["summary"]
        
        report = []
        report.append("🎯 COMPLETE TEST EXECUTION REPORT")
        report.append("=" * 60)
        report.append(f"📅 Timestamp: {self.results['timestamp']}")
        report.append(f"🌍 Environment: {self.results['environment']}")
        report.append("")
        
        # Overall Summary
        report.append("📊 OVERALL SUMMARY")
        report.append("-" * 30)
        report.append(f"Total Test Suites: {summary['total_suites']}")
        report.append(f"Successful Suites: {summary['successful_suites']}")
        report.append(f"Total Tests: {summary['total_tests']}")
        report.append(f"Passed: {summary['total_passed']} ✅")
        report.append(f"Failed: {summary['total_failed']} ❌")
        report.append(f"Overall Success Rate: {summary['overall_success_rate']}%")
        report.append(f"Suite Success Rate: {summary['suite_success_rate']}%")
        report.append("")
        
        # Individual Suite Results
        report.append("📋 INDIVIDUAL SUITE RESULTS")
        report.append("-" * 40)
        
        for suite_name, suite_result in self.results["test_suites"].items():
            status_icon = "✅" if suite_result.get("success") else "❌"
            report.append(f"{status_icon} {suite_name.upper()} Tests:")
            
            if suite_result["status"] == "skipped":
                report.append(f"   Status: SKIPPED ({suite_result.get('reason', 'unknown')})")
            elif suite_result["status"] == "error":
                report.append(f"   Status: ERROR ({suite_result.get('error', 'unknown')})")
            elif suite_result["status"] == "timeout":
                report.append(f"   Status: TIMEOUT")
            else:
                stats = suite_result.get("stats", {})
                if stats:
                    report.append(f"   Tests: {stats['passed']}/{stats['total']} passed ({stats['success_rate']}%)")
                    if stats['failed'] > 0:
                        report.append(f"   Failed: {stats['failed']}")
                    if stats['errors'] > 0:
                        report.append(f"   Errors: {stats['errors']}")
                else:
                    report.append(f"   Return Code: {suite_result.get('return_code', 'unknown')}")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 30)
        
        if summary['overall_success_rate'] >= 90:
            report.append("🎉 Excellent! Test suite is in great shape.")
        elif summary['overall_success_rate'] >= 75:
            report.append("👍 Good test coverage. Consider fixing remaining failures.")
        elif summary['overall_success_rate'] >= 50:
            report.append("⚠️  Moderate success rate. Focus on fixing critical failures.")
        else:
            report.append("🔴 Low success rate. Immediate attention required.")
        
        if summary['total_failed'] > 0:
            report.append(f"• Fix {summary['total_failed']} failing test(s)")
        
        for suite_name, suite_result in self.results["test_suites"].items():
            if suite_result["status"] == "skipped":
                report.append(f"• Enable {suite_name} tests by fixing import issues")
            elif not suite_result.get("success"):
                report.append(f"• Investigate {suite_name} test failures")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_results(self, filename: str = None):
        """Save test results to JSON file."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_results_{timestamp}.json"
        
        filepath = self.src_dir / "tests" / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        return filepath

def main():
    """Main test runner function."""
    runner = TestRunner()
    
    try:
        # Run all tests
        results = runner.run_all_tests()
        
        # Generate and display report
        report = runner.generate_report()
        print(report)
        
        # Save results
        results_file = runner.save_results()
        print(f"📄 Detailed results saved to: {results_file}")
        
        # Return appropriate exit code
        summary = results["summary"]
        if summary["overall_success_rate"] >= 80:
            return 0  # Success
        else:
            return 1  # Failure
            
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        return 2  # Error

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)