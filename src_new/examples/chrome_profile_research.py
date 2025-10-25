#!/usr/bin/env python3
"""
Chrome Profile 默认工作目录调研
深入分析 Chrome 的 Profile 选择机制和"默认"概念
"""

import os
import json
import subprocess
from datetime import datetime

def research_chrome_profile_mechanism():
    """调研 Chrome Profile 机制"""
    print("🔬 Chrome Profile 默认工作目录调研")
    print("=" * 80)
    
    user_data_dir = "/Users/haowu/Library/Application Support/Google/Chrome"
    
    # 1. 检查 Chrome 的 Local State 文件
    print("📋 1. 检查 Chrome Local State 配置...")
    print("-" * 50)
    
    local_state_path = os.path.join(user_data_dir, "Local State")
    if os.path.exists(local_state_path):
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # 检查 Profile 信息
            if 'profile' in local_state:
                profile_info = local_state['profile']
                print("✅ 发现 Profile 配置信息:")
                
                # 最后使用的 Profile
                if 'last_used' in profile_info:
                    print(f"   📌 最后使用的 Profile: {profile_info['last_used']}")
                
                # Profile 信息缓存
                if 'info_cache' in profile_info:
                    print("   📁 Profile 信息缓存:")
                    for profile_name, info in profile_info['info_cache'].items():
                        print(f"      - {profile_name}:")
                        if 'name' in info:
                            print(f"        名称: {info['name']}")
                        if 'user_name' in info:
                            print(f"        用户名: {info['user_name']}")
                        if 'is_using_default_name' in info:
                            print(f"        使用默认名称: {info['is_using_default_name']}")
                        if 'is_using_default_avatar' in info:
                            print(f"        使用默认头像: {info['is_using_default_avatar']}")
                        if 'active_time' in info:
                            active_time = datetime.fromtimestamp(info['active_time'])
                            print(f"        活跃时间: {active_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print()
                
                # Profile 创建顺序
                if 'profiles_created' in profile_info:
                    print(f"   📊 已创建的 Profile 数量: {profile_info['profiles_created']}")
                
                # Profile 顺序
                if 'profiles_order' in profile_info:
                    print(f"   📋 Profile 顺序: {profile_info['profiles_order']}")
                    
        except Exception as e:
            print(f"❌ 无法读取 Local State: {e}")
    else:
        print("❌ Local State 文件不存在")
    
    print("\n" + "=" * 80)
    
    # 2. 分析 Profile 启动逻辑
    print("🚀 2. 分析 Chrome Profile 启动逻辑...")
    print("-" * 50)
    
    print("📖 Chrome Profile 启动规则:")
    print("   1. 如果指定了 --profile-directory 参数，使用指定的 Profile")
    print("   2. 如果指定了 --user-data-dir 但没有 --profile-directory，使用 Default Profile")
    print("   3. 如果都没指定，使用系统默认用户数据目录的 Default Profile")
    print("   4. 如果 Default Profile 不存在，会自动创建")
    print("   5. Local State 中的 'last_used' 字段记录最后使用的 Profile")
    
    # 3. 检查当前运行的 Chrome 实例
    print("\n🔍 3. 检查当前运行的 Chrome 实例...")
    print("-" * 50)
    
    try:
        # 使用 lsof 检查 Chrome 打开的文件
        result = subprocess.run(['lsof', '-c', 'Google'], capture_output=True, text=True)
        chrome_files = result.stdout.split('\n')
        
        # 分析使用的 Profile
        profiles_in_use = set()
        for line in chrome_files:
            if 'Google/Chrome/' in line and ('Profile' in line or 'Default' in line):
                parts = line.split('/')
                for i, part in enumerate(parts):
                    if part == 'Chrome' and i + 1 < len(parts):
                        next_part = parts[i + 1]
                        if next_part == 'Default' or next_part.startswith('Profile'):
                            profiles_in_use.add(next_part)
        
        if profiles_in_use:
            print(f"✅ 当前运行的 Chrome 正在使用的 Profile: {', '.join(profiles_in_use)}")
        else:
            print("❌ 无法确定当前使用的 Profile")
            
    except Exception as e:
        print(f"❌ 检查运行实例失败: {e}")
    
    # 4. 理论分析
    print("\n📚 4. 理论分析: '默认工作目录' 的含义...")
    print("-" * 50)
    
    print("🤔 '默认工作目录' 可能的含义:")
    print("   A. 系统级默认: Chrome 安装后首次启动时创建的 Default Profile")
    print("   B. 用户级默认: Local State 中 'last_used' 记录的最后使用的 Profile")
    print("   C. 会话级默认: 当前浏览器会话正在使用的 Profile")
    print("   D. 活跃度默认: 最近修改时间最新的 Profile")
    
    print("\n💡 结论推测:")
    print("   - Chrome 的 '默认' Profile 通常指的是 'Default' 目录")
    print("   - 但用户实际使用的可能是其他 Profile (如 Profile 2)")
    print("   - Local State 的 'last_used' 字段记录了最后使用的 Profile")
    print("   - 文件系统的修改时间反映了实际的活跃度")
    
    # 5. 实际测试建议
    print("\n🧪 5. 验证建议...")
    print("-" * 50)
    
    print("🔬 验证方法:")
    print("   1. 关闭所有 Chrome 实例")
    print("   2. 直接启动 Chrome (不带任何参数)")
    print("   3. 观察启动的是哪个 Profile")
    print("   4. 检查 Local State 的 'last_used' 字段")
    print("   5. 对比文件修改时间")

def analyze_playwright_behavior():
    """分析 Playwright 的行为"""
    print("\n🎭 6. Playwright 行为分析...")
    print("-" * 50)
    
    print("🤖 Playwright 的 Profile 选择逻辑:")
    print("   1. 如果指定 user_data_dir 但不指定 profile，使用 Default Profile")
    print("   2. 如果同时指定 user_data_dir 和 profile，使用指定的 Profile")
    print("   3. 如果都不指定，创建临时的用户数据目录")
    
    print("\n⚠️  关键发现:")
    print("   - Playwright 默认使用 'Default' Profile，不会自动使用 'last_used'")
    print("   - 要使用用户实际的 Profile，必须明确指定 profile 参数")
    print("   - 用户手动打开的 Chrome 可能使用任何 Profile，不一定是 Default")

def main():
    research_chrome_profile_mechanism()
    analyze_playwright_behavior()
    
    print("\n" + "=" * 80)
    print("🎯 **最终结论**")
    print("=" * 80)
    
    print("❓ '默认工作目录' 的真实含义:")
    print("   ✅ 对于 Chrome: 通常是 'Default' Profile，但用户可能实际使用其他 Profile")
    print("   ✅ 对于 Playwright: 总是 'Default' Profile，除非明确指定")
    print("   ✅ 对于用户体验: 是最后使用的 Profile (Local State 'last_used')")
    print("   ✅ 对于活跃度: 是最近修改的 Profile (文件系统时间戳)")
    
    print("\n💡 **实用建议**:")
    print("   1. 不要假设 'Default' Profile 就是用户实际使用的")
    print("   2. 检查 Local State 的 'last_used' 字段获取真实的默认 Profile")
    print("   3. 结合文件修改时间验证活跃度")
    print("   4. Playwright 需要明确指定 profile 参数才能使用正确的 Profile")

if __name__ == "__main__":
    main()