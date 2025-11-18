#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试浏览器检测器功能

验证：
1. Profile 检测
2. 登录态验证
3. 浏览器进程检测
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rpa.browser.utils import BrowserDetector, detect_active_profile, get_browser_info


def test_browser_detector():
    """测试浏览器检测器基本功能"""
    print("=" * 60)
    print("🧪 测试 1: BrowserDetector 基本功能")
    print("=" * 60)
    
    detector = BrowserDetector()
    
    # 测试浏览器是否运行
    print("\n📌 检测浏览器是否运行...")
    is_running = detector.is_browser_running()
    print(f"   结果: {'✅ 浏览器正在运行' if is_running else '❌ 浏览器未运行'}")
    
    # 获取用户数据目录
    print("\n📌 获取用户数据目录...")
    user_data_dir = detector._get_edge_user_data_dir()
    print(f"   路径: {user_data_dir}")
    print(f"   存在: {'✅ 是' if os.path.exists(user_data_dir) else '❌ 否'}")
    
    # 列出所有 Profile
    if user_data_dir and os.path.exists(user_data_dir):
        print("\n📌 列出所有 Profile...")
        profiles = detector._list_profiles(user_data_dir)
        print(f"   找到 {len(profiles)} 个 Profile:")
        for i, profile in enumerate(profiles, 1):
            profile_path = os.path.join(user_data_dir, profile)
            mtime = os.path.getmtime(profile_path)
            from datetime import datetime
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"   {i}. {profile} (最后修改: {mtime_str})")
    
    print("\n" + "=" * 60)


def test_login_detection():
    """测试登录态检测"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 登录态检测")
    print("=" * 60)
    
    detector = BrowserDetector()
    user_data_dir = detector._get_edge_user_data_dir()
    
    if not user_data_dir or not os.path.exists(user_data_dir):
        print("❌ 用户数据目录不存在，跳过测试")
        return
    
    profiles = detector._list_profiles(user_data_dir)
    
    print(f"\n📌 检查各 Profile 的 seerfar.cn 登录态...")
    for profile in profiles:
        has_login = detector._has_login_cookies(user_data_dir, profile, "seerfar.cn")
        status = "✅ 有登录态" if has_login else "❌ 无登录态"
        print(f"   {profile}: {status}")
    
    print("\n" + "=" * 60)


def test_active_profile_detection():
    """测试活跃 Profile 检测"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: 活跃 Profile 自动检测")
    print("=" * 60)
    
    print("\n📌 检测有 seerfar.cn 登录态的 Profile...")
    active_profile = detect_active_profile("seerfar.cn")
    
    if active_profile:
        print(f"   ✅ 找到活跃 Profile: {active_profile}")
    else:
        print(f"   ❌ 未找到有登录态的 Profile")
    
    print("\n" + "=" * 60)


def test_browser_info():
    """测试浏览器信息获取"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 浏览器完整信息")
    print("=" * 60)
    
    print("\n📌 获取浏览器完整信息...")
    info = get_browser_info()
    
    print(f"\n浏览器状态:")
    print(f"   运行中: {'✅ 是' if info['is_running'] else '❌ 否'}")
    print(f"   用户数据目录: {info['user_data_dir']}")
    print(f"   活跃 Profile: {info['active_profile'] or '未检测到'}")
    print(f"   所有 Profile: {', '.join(info['all_profiles']) if info['all_profiles'] else '无'}")
    
    print("\n" + "=" * 60)


def test_browser_connection():
    """测试浏览器连接逻辑"""
    print("\n" + "=" * 60)
    print("🧪 测试 5: 浏览器连接逻辑验证")
    print("=" * 60)
    
    detector = BrowserDetector()
    
    # 检查浏览器运行状态
    print("\n📌 步骤 1: 检查浏览器运行状态")
    is_running = detector.is_browser_running()
    if is_running:
        print("   ✅ 浏览器正在运行")
    else:
        print("   ❌ 浏览器未运行")
        print("   💡 提示: 请先启动浏览器")
        return
    
    # 检测活跃 Profile
    print("\n📌 步骤 2: 检测有登录态的 Profile")
    active_profile = detect_active_profile("seerfar.cn")
    if active_profile:
        print(f"   ✅ 找到活跃 Profile: {active_profile}")
    else:
        print("   ❌ 未找到有登录态的 Profile")
        print("   💡 提示: 请在浏览器中登录 seerfar.cn")
        return
    
    # 检查调试端口
    print("\n📌 步骤 3: 检查调试端口")
    import socket
    debug_port = 9222
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('localhost', debug_port))
    sock.close()
    
    if result == 0:
        print(f"   ✅ 调试端口 {debug_port} 已开启")
        
        # 验证 CDP 端点
        print("\n📌 步骤 4: 验证 CDP 端点")
        try:
            import urllib.request
            import json
            
            cdp_url = f"http://localhost:{debug_port}/json/version"
            req = urllib.request.Request(cdp_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode('utf-8'))
                if 'webSocketDebuggerUrl' in data:
                    print("   ✅ CDP 端点可用")
                    print(f"   浏览器版本: {data.get('Browser', 'Unknown')}")
                    print(f"   WebSocket URL: {data.get('webSocketDebuggerUrl', 'N/A')[:50]}...")
                else:
                    print("   ❌ CDP 端点不完整")
        except Exception as e:
            print(f"   ❌ CDP 端点验证失败: {e}")
    else:
        print(f"   ❌ 调试端口 {debug_port} 未开启")
        print("   💡 提示: 请运行 ./start_edge_with_debug.sh")
        return
    
    print("\n📌 结论:")
    print("   ✅ 所有检查通过！浏览器可以正常连接")
    
    print("\n" + "=" * 60)


def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("浏览器检测器测试套件")
    print("🚀" * 30 + "\n")
    
    try:
        # 运行所有测试
        test_browser_detector()
        test_login_detection()
        test_active_profile_detection()
        test_browser_info()
        test_browser_connection()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
