#!/usr/bin/env python3
"""工作流引擎集成测试"""

import asyncio
import json
import os
import sys
import time
import threading
from pathlib import Path
from typing import Dict, Any

import pytest
import requests
from fastapi.testclient import TestClient

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, 'src_new'))

# 确保可以导入应用模块
sys.path.insert(0, os.path.join(project_root, 'src_new', 'apps'))

from workflow_engine.api.server import create_app
from workflow_engine.apps.manager import AppManager
from workflow_engine.core.engine import WorkflowEngine


class WorkflowEngineTestSuite:
    """工作流引擎测试套件"""
    
    def __init__(self):
        self.app = None
        self.client = None
        self.engine = None
        self.app_manager = None
        self.server_thread = None
        self.server_port = 8002
        self.base_url = f"http://localhost:{self.server_port}"
        
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建测试数据目录
        test_data_dir = Path.home() / ".ren_test"
        test_data_dir.mkdir(exist_ok=True)
        
        # 初始化组件
        self.app = create_app(str(test_data_dir / "test_workflow.db"))
        self.client = TestClient(self.app)
        self.engine = WorkflowEngine(str(test_data_dir / "test_workflow.db"))
        # Use correct apps directory path
        apps_dir = os.path.join(project_root, 'src_new', 'apps')
        self.app_manager = AppManager(apps_dir)
        
        print("✅ 测试环境设置完成")
        
    def test_health_check(self):
        """测试健康检查"""
        print("\n🏥 测试健康检查...")
        
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "workflow-engine"
        
        print("✅ 健康检查通过")
        
    def test_app_manager_loading(self):
        """测试应用管理器加载"""
        print("\n📦 测试应用管理器...")
        
        # 获取应用列表
        apps = self.app_manager.list_apps()
        print(f"  发现应用数量: {len(apps)}")

        # 检查 sample_app
        sample_app = self.app_manager.get_app("sample_app")
        assert sample_app is not None, "sample_app 应该存在"

        print(f"  应用名称: {sample_app.name}")
        print(f"  工作流数量: {len(sample_app.flows) if sample_app.flows else 0}")

        # 检查工作流
        if sample_app.flows:
            flow_ids = list(sample_app.flows.keys())
            print(f"  工作流IDs: {flow_ids}")

            assert "flow1" in flow_ids, "flow1 应该存在"
            assert "flow2" in flow_ids, "flow2 应该存在"
        else:
            print("  ⚠️ 应用没有配置工作流")
        
        print("✅ 应用管理器测试通过")
        
    def test_workflow_definition_loading(self):
        """测试工作流定义加载"""
        print("\n🔄 测试工作流定义加载...")
        
        # 测试 Flow1
        print("  测试 Flow1...")
        try:
            flow1_def = self.app_manager.load_workflow_definition("sample_app", "flow1")
            assert flow1_def.name == "flow1"
            assert len(flow1_def.nodes) > 0
            assert len(flow1_def.edges) > 0
            print(f"    ✅ Flow1: {len(flow1_def.nodes)} 节点, {len(flow1_def.edges)} 边")
        except Exception as e:
            print(f"    ❌ Flow1 加载失败: {e}")
            raise
            
        # 测试 Flow2
        print("  测试 Flow2...")
        try:
            flow2_def = self.app_manager.load_workflow_definition("sample_app", "flow2")
            assert flow2_def.name == "flow2"
            assert len(flow2_def.nodes) > 0
            assert len(flow2_def.edges) > 0
            print(f"    ✅ Flow2: {len(flow2_def.nodes)} 节点, {len(flow2_def.edges)} 边")
        except Exception as e:
            print(f"    ❌ Flow2 加载失败: {e}")
            raise
            
        print("✅ 工作流定义加载测试通过")
        
    def test_workflow_creation_via_api(self):
        """测试通过API创建工作流"""
        print("\n🚀 测试工作流创建API...")
        
        # 加载 Flow1 定义
        flow1_def = self.app_manager.load_workflow_definition("sample_app", "flow1")
        
        # 通过API创建工作流
        create_request = {
            "name": "test_flow1",
            "definition": flow1_def.dict(),
            "version": "1.0.0"
        }
        
        response = self.client.post("/flows", json=create_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "flow_version_id" in data
        assert data["name"] == "test_flow1"
        assert data["status"] == "created"
        
        flow_version_id = data["flow_version_id"]
        print(f"  ✅ 工作流创建成功，ID: {flow_version_id}")
        
        return flow_version_id
        
    def test_workflow_execution_simulation(self):
        """测试工作流执行模拟"""
        print("\n⚡ 测试工作流执行模拟...")
        
        # 创建工作流
        flow_version_id = self.test_workflow_creation_via_api()
        
        # 发布工作流
        publish_response = self.client.post(f"/flows/{flow_version_id}/publish")
        assert publish_response.status_code == 200
        print("  ✅ 工作流发布成功")
        
        # 启动工作流执行
        start_request = {
            "flow_version_id": flow_version_id,
            "input_data": {"test_input": "hello world"}
        }
        
        start_response = self.client.post("/runs/start", json=start_request)
        assert start_response.status_code == 200
        
        start_data = start_response.json()
        thread_id = start_data["thread_id"]
        print(f"  ✅ 工作流启动成功，Thread ID: {thread_id}")
        
        # 检查工作流状态
        status_response = self.client.get(f"/runs/{thread_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        print(f"  📊 工作流状态: {status_data.get('status', 'unknown')}")
        
        return thread_id
        
    def test_workflow_control_operations(self):
        """测试工作流控制操作"""
        print("\n🎮 测试工作流控制操作...")
        
        # 启动一个工作流
        thread_id = self.test_workflow_execution_simulation()
        
        # 测试暂停
        pause_response = self.client.post(f"/runs/{thread_id}/pause")
        if pause_response.status_code == 200:
            print("  ✅ 暂停请求发送成功")
        else:
            print(f"  ⚠️ 暂停请求失败: {pause_response.status_code}")
            
        # 测试恢复
        resume_response = self.client.post(f"/runs/{thread_id}/resume")
        if resume_response.status_code == 200:
            print("  ✅ 恢复请求发送成功")
        else:
            print(f"  ⚠️ 恢复请求失败: {resume_response.status_code}")
            
        print("✅ 工作流控制操作测试完成")
        
    def test_console_endpoints(self):
        """测试控制台端点"""
        print("\n🖥️ 测试控制台端点...")
        
        # 测试应用列表API
        apps_response = self.client.get("/console/apps")
        if apps_response.status_code == 200:
            apps_data = apps_response.json()
            print(f"  ✅ 应用列表API: 找到 {len(apps_data)} 个应用")
        else:
            print(f"  ⚠️ 应用列表API失败: {apps_response.status_code}")
            
        # 测试工作流列表API
        flows_response = self.client.get("/console/sample_app/flows")
        if flows_response.status_code == 200:
            flows_data = flows_response.json()
            print(f"  ✅ 工作流列表API: 找到 {len(flows_data)} 个工作流")
        else:
            print(f"  ⚠️ 工作流列表API失败: {flows_response.status_code}")
            
        print("✅ 控制台端点测试完成")
        
    def run_all_tests(self):
        """运行所有测试"""
        print("🧪 开始工作流引擎集成测试")
        print("=" * 60)
        
        try:
            # 设置测试环境
            self.setup_test_environment()
            
            # 运行测试
            self.test_health_check()
            self.test_app_manager_loading()
            self.test_workflow_definition_loading()
            self.test_workflow_creation_via_api()
            self.test_workflow_execution_simulation()
            self.test_workflow_control_operations()
            self.test_console_endpoints()
            
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！工作流引擎运行正常")
            return True
            
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def start_server_for_manual_testing(self):
        """启动服务器进行手动测试"""
        print("🚀 启动工作流引擎服务器进行手动测试...")
        print("=" * 60)
        
        try:
            import uvicorn
            
            # 设置测试环境
            self.setup_test_environment()
            
            print(f"🌐 服务器将在 http://localhost:{self.server_port} 启动")
            print("📖 API文档: http://localhost:{}/docs".format(self.server_port))
            print("🖥️ 控制台: http://localhost:{}/console".format(self.server_port))
            print("\n按 Ctrl+C 停止服务器")
            print("-" * 60)
            
            # 启动服务器
            uvicorn.run(
                self.app,
                host="0.0.0.0",
                port=self.server_port,
                log_level="info"
            )
            
        except KeyboardInterrupt:
            print("\n👋 服务器已停止")
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="工作流引擎集成测试")
    parser.add_argument("--mode", choices=["test", "server"], default="test",
                       help="运行模式: test=运行测试, server=启动服务器")
    
    args = parser.parse_args()
    
    test_suite = WorkflowEngineTestSuite()
    
    if args.mode == "test":
        success = test_suite.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.mode == "server":
        test_suite.start_server_for_manual_testing()


if __name__ == "__main__":
    main()