# 探索影刀RPA浏览器对象的可用方法
# 用于找出正确的API调用方式

import xbot
from xbot import print

def explore_browser_methods():
    """探索浏览器对象的可用方法"""
    print("=== 探索浏览器对象方法 ===")
    
    browser = None
    try:
        # 创建浏览器
        print("1. 创建浏览器...")
        browser = xbot.web.create("https://www.baidu.com", "chrome", load_timeout=20)
        print("✅ 浏览器创建成功")
        print(f"📝 浏览器对象类型: {type(browser)}")
        
        # 探索可用方法
        print("\n2. 探索浏览器对象的方法...")
        methods = [method for method in dir(browser) if not method.startswith('_')]
        print(f"🔍 可用方法数量: {len(methods)}")
        print("📋 可用方法列表:")
        for i, method in enumerate(methods, 1):
            print(f"   {i:2d}. {method}")
        
        # 检查可能的导航方法
        print("\n3. 检查可能的导航方法...")
        navigation_methods = []
        for method in methods:
            if any(keyword in method.lower() for keyword in ['get', 'goto', 'navigate', 'open', 'visit', 'go']):
                navigation_methods.append(method)
        
        if navigation_methods:
            print(f"🚀 可能的导航方法: {navigation_methods}")
        else:
            print("⚠️ 未找到明显的导航方法")
        
        # 检查可能的元素查找方法
        print("\n4. 检查可能的元素查找方法...")
        element_methods = []
        for method in methods:
            if any(keyword in method.lower() for keyword in ['find', 'element', 'select', 'locate']):
                element_methods.append(method)
        
        if element_methods:
            print(f"🔍 可能的元素查找方法: {element_methods}")
        else:
            print("⚠️ 未找到明显的元素查找方法")
        
        # 检查可能的关闭方法
        print("\n5. 检查可能的关闭方法...")
        close_methods = []
        for method in methods:
            if any(keyword in method.lower() for keyword in ['close', 'quit', 'exit', 'stop']):
                close_methods.append(method)
        
        if close_methods:
            print(f"🚪 可能的关闭方法: {close_methods}")
        else:
            print("⚠️ 未找到明显的关闭方法")
            
    except Exception as e:
        print(f"❌ 探索失败：{str(e)}")
        print(f"🔍 错误类型: {type(e).__name__}")
        
    finally:
        if browser:
            try:
                browser.close()
                print("\n✅ 浏览器关闭成功")
            except:
                pass
    
    print("\n=== 探索完成 ===")

# 执行探索
explore_browser_methods()
