from xbot import print
import sys
import os

# 添加当前脚本所在目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 影刀RPA Python片段 - 简化版
print("=== Simple Runner 启动 ===")

try:
    # 获取文件路径
    path = getattr(dialog_result, "good_shop_file")

    # 处理路径（可能是列表）
    if isinstance(path, (list, tuple)) and path:
        path = path[0]

    # 构造参数并调用seefar_test的run方法
    args = {
        "dialog_result": str(path),
        "good_shop_file": str(path)
    }

    # 调用seefar_test模块的run方法
    from seefar_test import SeefarCrawler
    crawler = SeefarCrawler()
    crawler.run(args)

    print("处理完成")

except NameError as e:
    if "dialog_result" in str(e):
        print("❌ dialog_result变量未定义！请确保在影刀流程中正确设置对话框组件")
    else:
        print(f"❌ 变量未定义错误：{str(e)}")
except Exception as e:
    print(f"❌ 程序执行失败：{str(e)}")

print("=== Simple Runner 结束 ===")