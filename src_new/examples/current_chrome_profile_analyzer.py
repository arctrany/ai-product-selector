#!/usr/bin/env python3
"""
当前 Chrome Profile 分析器
分析用户手动打开的 Chrome 浏览器实际使用的 Profile
"""

import os
import sqlite3
import json
import subprocess
from datetime import datetime

def get_chrome_user_data_dir():
    """获取 Chrome 用户数据目录"""
    return "/Users/haowu/Library/Application Support/Google/Chrome"

def analyze_profile_activity():
    """分析各个 Profile 的活动情况"""
    user_data_dir = get_chrome_user_data_dir()
    profiles = []
    
    print("🔍 分析 Chrome Profile 活动情况...")
    print("=" * 60)
    
    for item in os.listdir(user_data_dir):
        profile_path = os.path.join(user_data_dir, item)
        if os.path.isdir(profile_path) and (item == "Default" or item.startswith("Profile")):
            try:
                # 获取最后修改时间
                stat = os.stat(profile_path)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                
                # 检查是否有 Cookies 文件
                cookies_path = os.path.join(profile_path, "Cookies")
                has_cookies = os.path.exists(cookies_path)
                
                # 检查是否有 Preferences 文件
                prefs_path = os.path.join(profile_path, "Preferences")
                has_prefs = os.path.exists(prefs_path)
                
                profiles.append({
                    'name': item,
                    'path': profile_path,
                    'last_modified': last_modified,
                    'has_cookies': has_cookies,
                    'has_prefs': has_prefs
                })
                
                print(f"📁 {item}")
                print(f"   最后修改: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Cookies: {'✅' if has_cookies else '❌'}")
                print(f"   Preferences: {'✅' if has_prefs else '❌'}")
                print()
                
            except Exception as e:
                print(f"❌ 无法分析 {item}: {e}")
    
    # 按最后修改时间排序
    profiles.sort(key=lambda x: x['last_modified'], reverse=True)
    
    print("🎯 **最活跃的 Profile (按最后修改时间排序):**")
    print("=" * 60)
    for i, profile in enumerate(profiles[:3], 1):
        print(f"{i}. {profile['name']} - {profile['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    
    return profiles

def check_running_chrome_processes():
    """检查正在运行的 Chrome 进程"""
    print("\n🔍 检查正在运行的 Chrome 进程...")
    print("=" * 60)
    
    try:
        # 获取 Chrome 进程信息
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        chrome_processes = [line for line in result.stdout.split('\n') if 'Google Chrome' in line and 'Helper' not in line]
        
        if chrome_processes:
            print("✅ 发现正在运行的 Chrome 进程:")
            for process in chrome_processes:
                print(f"   {process}")
        else:
            print("❌ 没有发现正在运行的 Chrome 进程")
            
        # 检查 Chrome 打开的文件
        print("\n🔍 检查 Chrome 打开的用户数据文件...")
        try:
            lsof_result = subprocess.run(['lsof', '-c', 'Google'], capture_output=True, text=True)
            chrome_files = [line for line in lsof_result.stdout.split('\n') if 'Google/Chrome' in line]
            
            if chrome_files:
                print("✅ Chrome 正在使用的文件:")
                # 提取 Profile 信息
                profiles_in_use = set()
                for file_line in chrome_files[:10]:  # 只显示前10个
                    if 'Profile' in file_line or 'Default' in file_line:
                        parts = file_line.split('/')
                        for i, part in enumerate(parts):
                            if part == 'Chrome' and i + 1 < len(parts):
                                profile_name = parts[i + 1]
                                if profile_name in ['Default'] or profile_name.startswith('Profile'):
                                    profiles_in_use.add(profile_name)
                
                print(f"\n🎯 **当前正在使用的 Profile:** {', '.join(profiles_in_use)}")
                return list(profiles_in_use)
            else:
                print("❌ 没有发现 Chrome 打开的用户数据文件")
                
        except Exception as e:
            print(f"❌ 无法检查 lsof: {e}")
            
    except Exception as e:
        print(f"❌ 无法检查进程: {e}")
    
    return []

def analyze_profile_preferences(profile_name):
    """分析指定 Profile 的偏好设置"""
    user_data_dir = get_chrome_user_data_dir()
    prefs_path = os.path.join(user_data_dir, profile_name, "Preferences")
    
    print(f"\n🔍 分析 {profile_name} 的偏好设置...")
    print("=" * 60)
    
    if not os.path.exists(prefs_path):
        print(f"❌ {profile_name} 的 Preferences 文件不存在")
        return
    
    try:
        # 尝试读取 Preferences 文件
        with open(prefs_path, 'r', encoding='utf-8') as f:
            prefs = json.load(f)
        
        # 检查账户信息
        if 'account_info' in prefs:
            print("✅ 发现账户信息:")
            for account in prefs['account_info']:
                print(f"   账户: {account}")
        
        # 检查 Google 服务
        if 'google' in prefs:
            print("✅ 发现 Google 服务配置")
        
        # 检查同步设置
        if 'sync' in prefs:
            print("✅ 发现同步设置")
            
        # 检查登录信息
        signin_info = prefs.get('signin', {})
        if signin_info:
            print("✅ 发现登录信息:")
            print(f"   登录状态: {signin_info}")
            
    except json.JSONDecodeError:
        print(f"❌ 无法解析 {profile_name} 的 Preferences 文件 (JSON 格式错误)")
    except PermissionError:
        print(f"❌ 无法读取 {profile_name} 的 Preferences 文件 (权限不足)")
    except Exception as e:
        print(f"❌ 分析 {profile_name} 时出错: {e}")

def main():
    print("🚀 Chrome Profile 分析器")
    print("=" * 60)
    print("正在分析您手动打开的 Chrome 浏览器使用的 Profile...")
    print()
    
    # 1. 分析 Profile 活动情况
    profiles = analyze_profile_activity()
    
    # 2. 检查正在运行的 Chrome 进程
    active_profiles = check_running_chrome_processes()
    
    # 3. 分析最活跃的 Profile
    if profiles:
        most_active = profiles[0]
        print(f"\n🎯 **结论: 您当前使用的 Profile 很可能是 '{most_active['name']}'**")
        print(f"   路径: {most_active['path']}")
        print(f"   最后活动: {most_active['last_modified'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 分析这个 Profile 的详细信息
        analyze_profile_preferences(most_active['name'])
    
    print("\n" + "=" * 60)
    print("✅ 分析完成!")

if __name__ == "__main__":
    main()