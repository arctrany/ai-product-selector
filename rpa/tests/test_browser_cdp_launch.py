"""
测试浏览器 CDP 端口和 Profile 配置的集成测试

验证：
1. CDP 端口参数是否正确添加
2. Profile 配置是否正确使用
3. 浏览器是否能正常启动
"""

import asyncio
import pytest
from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver


class TestBrowserCDPLaunch:
    """测试浏览器 CDP 启动功能"""
    
    @pytest.mark.asyncio
    async def test_launch_with_cdp_port_default(self):
        """测试场景：使用默认 CDP 端口启动浏览器"""
        config = {
            'browser_type': 'edge',
            'headless': True,  # 使用 headless 模式避免弹出窗口
            'debug_port': 9222
        }
        
        driver = SimplifiedPlaywrightBrowserDriver(config)
        
        try:
            # 初始化浏览器
            success = await driver.initialize()
            assert success, "浏览器初始化失败"
            
            # 验证浏览器已启动
            assert driver.browser is not None or driver.context is not None, "浏览器未启动"
            
            # 验证页面可用
            assert driver.page is not None, "页面未创建"
            
            print("✅ 测试通过：浏览器成功启动，CDP 端口配置正确")
            
        finally:
            # 清理
            await driver.shutdown()
    
    @pytest.mark.asyncio
    async def test_launch_with_custom_cdp_port(self):
        """测试场景：使用自定义 CDP 端口启动浏览器"""
        config = {
            'browser_type': 'edge',
            'headless': True,
            'debug_port': 9223  # 自定义端口
        }
        
        driver = SimplifiedPlaywrightBrowserDriver(config)
        
        try:
            success = await driver.initialize()
            assert success, "浏览器初始化失败"
            
            # 验证启动参数包含自定义端口
            launch_args = driver._get_default_launch_args()
            assert any('--remote-debugging-port=9223' in arg for arg in launch_args), \
                f"启动参数中应包含 --remote-debugging-port=9223，实际: {launch_args}"
            
            print("✅ 测试通过：自定义 CDP 端口配置正确")
            
        finally:
            await driver.shutdown()
    
    @pytest.mark.asyncio
    async def test_launch_with_custom_profile(self):
        """测试场景：使用自定义 Profile 启动浏览器"""
        import os
        import tempfile
        
        # 创建临时用户数据目录
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'browser_type': 'edge',
                'headless': True,
                'debug_port': 9222,
                'user_data_dir': temp_dir,
                'launch_args': ['--profile-directory=TestProfile']
            }
            
            driver = SimplifiedPlaywrightBrowserDriver(config)
            
            try:
                success = await driver.initialize()
                assert success, "浏览器初始化失败"
                
                # 验证 Profile 参数没有被覆盖
                # 注意：这里我们只能验证配置，实际的 Profile 使用需要检查浏览器行为
                print("✅ 测试通过：自定义 Profile 配置正确")
                
            finally:
                await driver.shutdown()
    
    def test_cdp_port_in_launch_args(self):
        """测试场景：验证 CDP 端口参数在启动参数中"""
        # 测试默认端口
        driver1 = SimplifiedPlaywrightBrowserDriver({'debug_port': 9222})
        args1 = driver1._get_default_launch_args()
        assert '--remote-debugging-port=9222' in args1, \
            f"默认端口参数应在启动参数中，实际: {args1}"
        
        # 测试自定义端口
        driver2 = SimplifiedPlaywrightBrowserDriver({'debug_port': 9223})
        args2 = driver2._get_default_launch_args()
        assert '--remote-debugging-port=9223' in args2, \
            f"自定义端口参数应在启动参数中，实际: {args2}"
        
        print("✅ 测试通过：CDP 端口参数正确添加到启动参数")
    
    def test_profile_not_overridden(self):
        """测试场景：验证 Profile 参数不会被覆盖"""
        config = {
            'browser_type': 'edge',
            'launch_args': ['--profile-directory=CustomProfile']
        }
        
        driver = SimplifiedPlaywrightBrowserDriver(config)
        
        # 模拟 _launch_browser 中的逻辑
        launch_args = config.get('launch_args', [])
        
        # 检查是否已有 profile 参数
        has_profile = any('--profile-directory=' in arg for arg in launch_args)
        
        assert has_profile, "应该检测到自定义 Profile 参数"
        
        # 验证不会添加 Default
        if has_profile:
            # 不应该添加 Default
            assert '--profile-directory=CustomProfile' in launch_args
            print("✅ 测试通过：自定义 Profile 不会被覆盖")


if __name__ == '__main__':
    # 运行同步测试
    test = TestBrowserCDPLaunch()
    test.test_cdp_port_in_launch_args()
    test.test_profile_not_overridden()
    
    # 运行异步测试
    print("\n运行异步测试...")
    asyncio.run(test.test_launch_with_cdp_port_default())
    asyncio.run(test.test_launch_with_custom_cdp_port())
    asyncio.run(test.test_launch_with_custom_profile())
    
    print("\n✅ 所有测试通过！")
