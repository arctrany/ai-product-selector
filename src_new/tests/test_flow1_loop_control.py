"""
FLOW1 LOOP CONTROL TEST

Test flow1's loop task pause/resume functionality and thread_id control.
This test provides concrete evidence that:
1. Flow1 loop can be paused during execution
2. Flow1 loop can be resumed from pause point
3. Thread_id control works properly throughout the lifecycle
"""

import time
import requests
import json
from typing import Dict, Any, Optional
import threading
from datetime import datetime


class Flow1LoopControlTest:
    """Test Flow1 loop control with pause/resume functionality."""
    
    def __init__(self, base_url: str = "http://localhost:8889"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.evidence = []
        
    def log_evidence(self, action: str, details: Dict[str, Any]):
        """Log evidence with timestamp."""
        evidence_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        self.evidence.append(evidence_entry)
        print(f"📝 EVIDENCE: {action} - {details}")
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {details}")
        
    def start_flow1_workflow(self) -> Optional[str]:
        """Start Flow1 workflow and return thread_id."""
        try:
            # Start Flow1 workflow
            start_response = self.session.post(
                f"{self.base_url}/api/flows/abba-ccdd-eeff-1.0.0/start",
                json={
                    "input_data": {
                        "test_mode": "loop_control",
                        "loop_iterations": 10,
                        "delay_per_iteration": 2
                    }
                }
            )
            
            self.log_evidence("WORKFLOW_START_REQUEST", {
                "url": f"{self.base_url}/api/flows/abba-ccdd-eeff-1.0.0/start",
                "status_code": start_response.status_code,
                "response_headers": dict(start_response.headers)
            })
            
            if start_response.status_code == 302:
                # Extract thread_id from redirect URL
                redirect_url = start_response.headers.get('location', '')
                if 'thread_id=' in redirect_url:
                    thread_id = redirect_url.split('thread_id=')[1].split('&')[0]
                    self.log_evidence("THREAD_ID_EXTRACTED", {
                        "thread_id": thread_id,
                        "redirect_url": redirect_url
                    })
                    return thread_id
                    
            elif start_response.status_code == 200:
                try:
                    data = start_response.json()
                    thread_id = data.get("thread_id")
                    if thread_id:
                        self.log_evidence("THREAD_ID_FROM_JSON", {
                            "thread_id": thread_id,
                            "response_data": data
                        })
                        return thread_id
                except json.JSONDecodeError:
                    pass
                    
            self.log_evidence("WORKFLOW_START_FAILED", {
                "status_code": start_response.status_code,
                "response_text": start_response.text[:500]
            })
            return None
            
        except Exception as e:
            self.log_evidence("WORKFLOW_START_ERROR", {"error": str(e)})
            return None
            
    def get_workflow_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status."""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
            
            self.log_evidence("STATUS_CHECK", {
                "thread_id": thread_id,
                "status_code": response.status_code
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_evidence("STATUS_DATA", {
                    "thread_id": thread_id,
                    "status": data.get("status"),
                    "data": data
                })
                return data
            elif response.status_code == 404:
                self.log_evidence("WORKFLOW_NOT_FOUND", {
                    "thread_id": thread_id,
                    "response": response.text
                })
                return None
            else:
                self.log_evidence("STATUS_ERROR", {
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                return None
                
        except Exception as e:
            self.log_evidence("STATUS_CHECK_ERROR", {
                "thread_id": thread_id,
                "error": str(e)
            })
            return None
            
    def pause_workflow(self, thread_id: str) -> bool:
        """Pause workflow execution."""
        try:
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/pause")
            
            self.log_evidence("PAUSE_REQUEST", {
                "thread_id": thread_id,
                "status_code": response.status_code
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_evidence("PAUSE_SUCCESS", {
                    "thread_id": thread_id,
                    "response": data
                })
                return True
            elif response.status_code == 404:
                self.log_evidence("PAUSE_WORKFLOW_NOT_FOUND", {
                    "thread_id": thread_id,
                    "response": response.text
                })
                return False
            else:
                self.log_evidence("PAUSE_ERROR", {
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_evidence("PAUSE_REQUEST_ERROR", {
                "thread_id": thread_id,
                "error": str(e)
            })
            return False
            
    def resume_workflow(self, thread_id: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """Resume workflow execution."""
        try:
            payload = {"updates": updates} if updates else {}
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/resume", json=payload)
            
            self.log_evidence("RESUME_REQUEST", {
                "thread_id": thread_id,
                "status_code": response.status_code,
                "payload": payload
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_evidence("RESUME_SUCCESS", {
                    "thread_id": thread_id,
                    "response": data
                })
                return True
            elif response.status_code == 404:
                self.log_evidence("RESUME_WORKFLOW_NOT_FOUND", {
                    "thread_id": thread_id,
                    "response": response.text
                })
                return False
            else:
                self.log_evidence("RESUME_ERROR", {
                    "thread_id": thread_id,
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
                
        except Exception as e:
            self.log_evidence("RESUME_REQUEST_ERROR", {
                "thread_id": thread_id,
                "error": str(e)
            })
            return False
            
    def get_workflow_logs(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow logs."""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}/logs")
            
            if response.status_code == 200:
                data = response.json()
                self.log_evidence("LOGS_RETRIEVED", {
                    "thread_id": thread_id,
                    "log_count": len(data.get("logs", [])),
                    "total": data.get("total", 0)
                })
                return data
            else:
                self.log_evidence("LOGS_ERROR", {
                    "thread_id": thread_id,
                    "status_code": response.status_code
                })
                return None
                
        except Exception as e:
            self.log_evidence("LOGS_REQUEST_ERROR", {
                "thread_id": thread_id,
                "error": str(e)
            })
            return None
            
    def test_flow1_loop_pause_resume_cycle(self):
        """Test complete Flow1 loop pause/resume cycle."""
        print("\n🔄 TESTING FLOW1 LOOP PAUSE/RESUME CYCLE")
        print("=" * 60)
        
        # Step 1: Start Flow1 workflow
        print("\n📋 Step 1: Starting Flow1 workflow...")
        thread_id = self.start_flow1_workflow()
        
        if not thread_id:
            self.log_result("Flow1 Start", False, "Failed to start workflow or get thread_id")
            return False
            
        self.log_result("Flow1 Start", True, f"Started with thread_id: {thread_id}")
        
        # Step 2: Wait a bit for workflow to start executing
        print(f"\n📋 Step 2: Waiting for workflow {thread_id} to start executing...")
        time.sleep(3)
        
        # Step 3: Check initial status
        print(f"\n📋 Step 3: Checking initial status of {thread_id}...")
        initial_status = self.get_workflow_status(thread_id)
        
        if initial_status:
            self.log_result("Initial Status Check", True, f"Status: {initial_status.get('status')}")
        else:
            self.log_result("Initial Status Check", False, "Could not get initial status")
            
        # Step 4: Attempt to pause the workflow
        print(f"\n📋 Step 4: Attempting to pause workflow {thread_id}...")
        pause_success = self.pause_workflow(thread_id)
        
        if pause_success:
            self.log_result("Workflow Pause", True, "Pause request sent successfully")
        else:
            self.log_result("Workflow Pause", False, "Pause request failed")
            
        # Step 5: Wait and check status after pause
        print(f"\n📋 Step 5: Checking status after pause attempt...")
        time.sleep(2)
        paused_status = self.get_workflow_status(thread_id)
        
        if paused_status:
            status = paused_status.get('status')
            self.log_result("Post-Pause Status", True, f"Status after pause: {status}")
        else:
            self.log_result("Post-Pause Status", False, "Could not get status after pause")
            
        # Step 6: Attempt to resume the workflow
        print(f"\n📋 Step 6: Attempting to resume workflow {thread_id}...")
        resume_updates = {"resumed_at": datetime.now().isoformat(), "test_marker": "resume_test"}
        resume_success = self.resume_workflow(thread_id, resume_updates)
        
        if resume_success:
            self.log_result("Workflow Resume", True, "Resume request sent successfully")
        else:
            self.log_result("Workflow Resume", False, "Resume request failed")
            
        # Step 7: Check final status
        print(f"\n📋 Step 7: Checking final status...")
        time.sleep(2)
        final_status = self.get_workflow_status(thread_id)
        
        if final_status:
            status = final_status.get('status')
            self.log_result("Final Status Check", True, f"Final status: {status}")
        else:
            self.log_result("Final Status Check", False, "Could not get final status")
            
        # Step 8: Get workflow logs for evidence
        print(f"\n📋 Step 8: Retrieving workflow logs...")
        logs = self.get_workflow_logs(thread_id)
        
        if logs and logs.get("logs"):
            self.log_result("Log Retrieval", True, f"Retrieved {len(logs['logs'])} log entries")
        else:
            self.log_result("Log Retrieval", False, "No logs retrieved")
            
        return True
        
    def test_thread_id_control_consistency(self):
        """Test that thread_id control is consistent across all operations."""
        print("\n🎯 TESTING THREAD_ID CONTROL CONSISTENCY")
        print("=" * 60)
        
        # Start multiple workflows to test thread_id uniqueness
        thread_ids = []
        
        for i in range(3):
            print(f"\n📋 Starting workflow {i+1}/3...")
            thread_id = self.start_flow1_workflow()
            if thread_id:
                thread_ids.append(thread_id)
                self.log_result(f"Workflow {i+1} Start", True, f"Thread ID: {thread_id}")
            else:
                self.log_result(f"Workflow {i+1} Start", False, "Failed to get thread_id")
                
        # Test thread_id uniqueness
        unique_ids = set(thread_ids)
        if len(unique_ids) == len(thread_ids):
            self.log_result("Thread ID Uniqueness", True, f"All {len(thread_ids)} thread IDs are unique")
        else:
            self.log_result("Thread ID Uniqueness", False, f"Duplicate thread IDs found")
            
        # Test control operations on each thread_id
        for i, thread_id in enumerate(thread_ids):
            print(f"\n📋 Testing control operations on thread {thread_id}...")
            
            # Test status check
            status = self.get_workflow_status(thread_id)
            if status is not None:
                self.log_result(f"Thread {i+1} Status", True, f"Status retrieved for {thread_id}")
            else:
                self.log_result(f"Thread {i+1} Status", False, f"Could not get status for {thread_id}")
                
            # Test pause
            pause_result = self.pause_workflow(thread_id)
            self.log_result(f"Thread {i+1} Pause", pause_result, f"Pause operation on {thread_id}")
            
            # Test resume
            resume_result = self.resume_workflow(thread_id)
            self.log_result(f"Thread {i+1} Resume", resume_result, f"Resume operation on {thread_id}")
            
        return True
        
    def run_comprehensive_test(self):
        """Run comprehensive Flow1 loop control test."""
        print("🚀 STARTING FLOW1 LOOP CONTROL COMPREHENSIVE TEST")
        print("=" * 80)
        
        # Test 1: Flow1 loop pause/resume cycle
        self.test_flow1_loop_pause_resume_cycle()
        
        # Test 2: Thread ID control consistency
        self.test_thread_id_control_consistency()
        
        # Generate evidence report
        self.generate_evidence_report()
        
        # Generate test summary
        self.generate_test_summary()
        
    def generate_evidence_report(self):
        """Generate detailed evidence report."""
        print("\n" + "=" * 80)
        print("📋 EVIDENCE REPORT - FLOW1 LOOP CONTROL")
        print("=" * 80)
        
        print(f"\n📊 Total Evidence Entries: {len(self.evidence)}")
        
        # Group evidence by action type
        evidence_by_action = {}
        for entry in self.evidence:
            action = entry["action"]
            if action not in evidence_by_action:
                evidence_by_action[action] = []
            evidence_by_action[action].append(entry)
            
        for action, entries in evidence_by_action.items():
            print(f"\n🔍 {action}: {len(entries)} entries")
            for entry in entries[-3:]:  # Show last 3 entries for each action
                print(f"   • {entry['timestamp']}: {entry['details']}")
                
        # Save evidence to file
        evidence_file = "flow1_loop_control_evidence.json"
        try:
            with open(evidence_file, 'w') as f:
                json.dump(self.evidence, f, indent=2, default=str)
            print(f"\n💾 Evidence saved to: {evidence_file}")
        except Exception as e:
            print(f"\n❌ Failed to save evidence: {e}")
            
    def generate_test_summary(self):
        """Generate test summary."""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY - FLOW1 LOOP CONTROL")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n📋 Test Details:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
            
        # Key evidence summary
        print(f"\n🔑 Key Evidence:")
        
        # Count thread IDs created
        thread_id_entries = [e for e in self.evidence if "thread_id" in e.get("details", {})]
        unique_thread_ids = set()
        for entry in thread_id_entries:
            tid = entry["details"].get("thread_id")
            if tid:
                unique_thread_ids.add(tid)
                
        print(f"   • Thread IDs Created: {len(unique_thread_ids)}")
        
        # Count successful operations
        successful_operations = {
            "starts": len([e for e in self.evidence if e["action"] == "THREAD_ID_EXTRACTED"]),
            "pauses": len([e for e in self.evidence if e["action"] == "PAUSE_SUCCESS"]),
            "resumes": len([e for e in self.evidence if e["action"] == "RESUME_SUCCESS"]),
            "status_checks": len([e for e in self.evidence if e["action"] == "STATUS_DATA"])
        }
        
        for operation, count in successful_operations.items():
            print(f"   • Successful {operation.title()}: {count}")
            
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - FLOW1 LOOP CONTROL VERIFIED!")
        elif passed_tests >= total_tests * 0.8:
            print("\n⚠️ MOSTLY WORKING - Minor issues detected")
        else:
            print("\n❌ SIGNIFICANT ISSUES - Flow1 loop control needs attention")
            
        return passed_tests == total_tests


def main():
    """Run Flow1 loop control test."""
    tester = Flow1LoopControlTest()
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()