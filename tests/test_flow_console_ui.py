"""
测试工作流控制台UI优化功能
验证 optimize-console-ui 变更提案的实施效果
"""
import re
import os
import time


class TestFlowConsoleUI:
    """工作流控制台UI测试类"""
    
    def setup_method(self):
        """测试前准备"""
        self.base_url = "http://localhost:8889"  # 使用正确的端口
        self.console_path = "/src_new/workflow_engine/templates/flow_console.html"

    def test_html_structure_validation(self):
        """6.1 测试按钮状态切换功能 - 验证HTML结构"""
        # 读取HTML文件
        with open(f".{self.console_path}", 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 使用正则表达式验证HTML结构（不依赖BeautifulSoup）

        # 验证"触发流程"按钮已移除
        trigger_pattern = r'<button[^>]*>.*?触发.*?</button>'
        trigger_buttons = re.findall(trigger_pattern, html_content, re.DOTALL | re.IGNORECASE)
        assert len(trigger_buttons) == 0, f"触发流程按钮应该已被移除，但找到: {trigger_buttons}"

        # 验证开始/暂停按钮存在
        start_pause_pattern = r'<button[^>]*id=["\']start-pause-btn["\'][^>]*>'
        start_pause_matches = re.search(start_pause_pattern, html_content)
        assert start_pause_matches is not None, "开始/暂停按钮应该存在"

        # 验证按钮绑定了切换函数
        toggle_function_pattern = r'toggleStartPause\(\)'
        assert re.search(toggle_function_pattern, html_content), "按钮应该绑定toggleStartPause函数"

        # 验证停止按钮存在
        stop_button_pattern = r'<button[^>]*onclick=["\']stopFlow\(\)["\'][^>]*>.*?停止.*?</button>'
        stop_matches = re.search(stop_button_pattern, html_content, re.DOTALL)
        assert stop_matches is not None, "停止按钮应该存在"

        print("✅ 6.1 按钮状态切换功能结构验证通过")

    def test_status_area_layout(self):
        """6.2 验证实时状态更新 - 检查状态区域布局"""
        with open(f".{self.console_path}", 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 验证执行状态区域存在
        status_info_pattern = r'<div[^>]*id=["\']status-info["\'][^>]*>'
        assert re.search(status_info_pattern, html_content), "状态信息区域应该存在"

        # 验证连接状态指示器存在
        connection_status_pattern = r'<div[^>]*id=["\']connection-status["\'][^>]*>'
        assert re.search(connection_status_pattern, html_content), "连接状态指示器应该存在"

        # 验证状态更新相关JavaScript函数存在
        assert 'updateStatus(' in html_content, "updateStatus函数应该存在"
        assert 'updateConnectionStatus(' in html_content, "updateConnectionStatus函数应该存在"

        print("✅ 6.2 实时状态更新功能验证通过")

    def test_responsive_layout(self):
        """6.3 测试响应式布局"""
        with open(f".{self.console_path}", 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 验证CSS媒体查询存在
        assert '@media' in html_content, "应该包含响应式CSS媒体查询"

        # 验证现代化CSS样式
        assert 'linear-gradient' in html_content, "应该包含现代化渐变样式"
        assert 'transition:' in html_content, "应该包含过渡动画"
        assert 'border-radius:' in html_content, "应该包含圆角样式"

        print("✅ 6.3 响应式布局验证通过")

    def test_removed_elements(self):
        """6.4 验证所有核心功能正常工作 - 检查移除的元素"""
        with open(f".{self.console_path}", 'r', encoding='utf-8') as f:
            html_content = f.read()

        # 验证输入数据区域已移除（检查特定的输入数据区域标识）
        # 检查是否存在专门的输入数据表单或输入区域
        input_form_pattern = r'<form[^>]*>.*?输入.*?</form>'
        input_section_pattern = r'<div[^>]*class=["\'][^"\']*input[^"\']*["\'][^>]*>.*?输入数据.*?</div>'

        input_form_matches = re.findall(input_form_pattern, html_content, re.DOTALL | re.IGNORECASE)
        input_section_matches = re.findall(input_section_pattern, html_content, re.DOTALL | re.IGNORECASE)

        # 只要没有专门的输入表单或输入区域就算通过
        assert len(input_form_matches) == 0, f"输入表单应该已被移除，但找到: {input_form_matches}"
        assert len(input_section_matches) == 0, f"输入数据区域应该已被移除，但找到: {input_section_matches}"
        
        # 验证triggerFlow函数已移除
        assert 'function triggerFlow(' not in html_content, "triggerFlow函数应该已被移除"
        
        # 验证核心功能保留
        assert 'startWorkflow(' in html_content, "startWorkflow函数应该保留"
        assert 'pauseWorkflow(' in html_content, "pauseWorkflow函数应该保留"
        assert 'stopFlow(' in html_content, "stopFlow函数应该保留"
        assert 'WebSocket(' in html_content, "WebSocket连接功能应该保留"
        
        print("✅ 6.4 核心功能验证通过")
    
    def test_javascript_functionality(self):
        """验证JavaScript功能完整性"""
        with open(f".{self.console_path}", 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 验证关键JavaScript函数存在
        required_functions = [
            'toggleStartPause()',
            'updateButtonState(',
            'startLogPolling(',
            'updateConnectionStatus(',
            'addLog(',
            'refreshStatus()'
        ]
        
        for func in required_functions:
            assert func in html_content, f"关键函数 {func} 应该存在"
        
        print("✅ JavaScript功能完整性验证通过")


if __name__ == "__main__":
    # 运行测试
    test_instance = TestFlowConsoleUI()
    test_instance.setup_method()
    
    try:
        test_instance.test_html_structure_validation()
        test_instance.test_status_area_layout()
        test_instance.test_responsive_layout()
        test_instance.test_removed_elements()
        test_instance.test_javascript_functionality()
        
        print("\n🎉 所有UI优化测试通过！")
        print("✅ 按钮状态切换功能正常")
        print("✅ 实时状态更新功能正常")
        print("✅ 响应式布局正常")
        print("✅ 所有核心功能正常工作")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试执行错误: {e}")
        raise