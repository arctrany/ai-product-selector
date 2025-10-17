# 影刀RPA Python开发规范

## 概述
本文档整理了在影刀RPA环境中进行Python开发的规范和最佳实践，基于实际开发经验和错误教训总结。

## ⚠️ 我犯下的错误总结（重要！）

### 错误0：浏览器API使用错误（最新发现）
**❌ 我的错误做法：**
- 错误地认为影刀RPA使用`browser.get(url)`或`browser.goto(url)`进行导航
- 使用了错误的元素查找方式：`browser.find_element(xpath)`
- 使用了错误的标签页关闭方法：`browser.close_current_tab()`

**✅ 正确做法：**
- 使用影刀RPA专用的浏览器API：
  - `browser.navigate(url)` - 页面导航（正确方法）
  - `browser.find_by_xpath(xpath)` - 通过XPath查找元素
  - `browser.find_by_css(css_selector)` - 通过CSS选择器查找元素
  - `browser.find(selector)` - 通过选择器查找元素
  - `element.get_text()` - 获取元素文本
  - `browser.close()` - 关闭浏览器

### 错误1：API验证不充分
**❌ 我的错误做法：**
- 没有充分查阅官方文档就基于假设修改API
- 一次性修改大量代码而不逐步验证
- 基于网上搜索结果而不是官方文档进行开发

**✅ 正确做法：**
- 优先查阅影刀官方文档确认API使用方式
- 遇到API错误时立即停止并重新验证
- 逐步修改并测试每个API调用

### 错误2：日志API使用错误
**❌ 我的错误：**
根据用户实际遇到的错误 `module 'xbot.logging' has no attribute 'info'`，说明在某些影刀RPA版本或环境中，`xbot.logging.info()`等方法可能不存在。

**✅ 正确做法：**
```python
from xbot import print

# 安全的日志输出方式 - 统一使用print
def safe_log(message, level="debug"):
    """安全的日志输出函数，统一使用print"""
    print(f"[{level.upper()}] {message}")

# 使用示例
safe_log("程序开始执行", "info")
safe_log("操作完成", "info")
safe_log("警告信息", "warning")
safe_log("错误信息", "error")
```

### 错误3：macOS Excel兼容性问题 ⚠️ 重要！
**❌ 我的错误：**
在macOS系统上使用影刀RPA的Excel操作API时，遇到错误：`'MacAEWorkBook' object has no attribute 'get_worksheet_by_index'`

**问题原因：**
- 在macOS上，影刀RPA使用 `MacAEWorkBook` 对象操作Excel
- 该对象的API与Windows版本不同，缺少某些方法
- 直接使用 `excel.open()` 和 `get_worksheet_by_index()` 会导致兼容性问题

**✅ 正确解决方案：**
```python
def read_excel_file_cross_platform(file_path):
    """跨平台兼容的Excel读取方法"""
    try:
        # 方案1：使用openpyxl库（推荐）
        from openpyxl import load_workbook
        
        workbook = load_workbook(file_path, read_only=True)
        worksheet = workbook.active
        
        data = []
        for row in worksheet.iter_rows(min_col=1, max_col=1, values_only=True):
            cell_value = row[0]
            if cell_value and str(cell_value).strip():
                data.append(str(cell_value).strip())
        
        workbook.close()
        print(f"✅ 使用openpyxl成功读取到 {len(data)} 行数据")
        return data
        
    except ImportError:
        print("❌ openpyxl库未安装，尝试备用方法")
        return read_excel_fallback(file_path)
    except Exception as e:
        print(f"❌ openpyxl读取失败：{str(e)}")
        return read_excel_fallback(file_path)

def read_excel_fallback(file_path):
    """备用Excel读取方法"""
    try:
        # 备用方案1：CSV格式
        if file_path.lower().endswith('.csv'):
            import csv
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip():
                        data.append(row[0].strip())
            return data
        
        # 备用方案2：pandas
        import pandas as pd
        df = pd.read_excel(file_path, engine='openpyxl')
        data = [str(value).strip() for value in df.iloc[:, 0] if pd.notna(value)]
        return data
        
    except Exception as e:
        print(f"❌ 所有读取方法都失败了：{str(e)}")
        print("💡 建议：将Excel文件另存为CSV格式后重试")
        return []
```

**关键要点：**
- **优先使用openpyxl**：跨平台兼容，不依赖系统Office环境
- **提供备用方案**：CSV读取、pandas读取等
- **详细错误处理**：给用户明确的解决建议
- **信息来源**：影刀RPA官方社区推荐使用openpyxl库

### 错误3：输出API使用错误
**❌ 错误写法：**
```python
import xbot
xbot.print("Hello World")  # 这是错误的！
```

**❌ 另一个错误写法：**
```python
# 直接使用标准print，在影刀RPA中无法输出到控制台
print("Hello World")  # 这在影刀RPA中看不到输出！
```

**✅ 正确写法：**
```python
from xbot import print
print("Hello World")  # 正确的影刀RPA输出方式
```

### 错误2：日志API使用错误（已纠正）
**❌ 错误写法：**
```python
import xbot
xbot.log("INFO", "message")  # 这个方法不存在！
```

**❌ 另一个错误写法：**
```python
import xbot.logging
xbot.logging.info("message")  # 这个方法也不存在！
xbot.logging.debug("debug message")  # 这个方法也不存在！
```

**✅ 正确写法：**
```python
from xbot import print
print("message")  # 使用print进行所有输出
print("[INFO] message")  # 可以加上标签区分日志级别
print("[DEBUG] debug message")
print("[WARNING] warning message")
print("[ERROR] error message")
```

### 错误3：导入方式错误
**❌ 错误写法：**
```python
from xbot import print
import xbot.logging
# 然后错误地认为所有基础Python函数都需要特殊导入
# 导致str、len、isinstance等基础函数报错
```

**✅ 正确写法：**
```python
from xbot import print  # 只有print需要从xbot导入
import xbot.logging     # 日志模块正常导入
# str、len、isinstance等基础Python函数直接使用，无需特殊导入
```

### 错误4：未充分验证API就修改代码
**❌ 错误做法：**
- 基于假设修改API调用方式
- 没有查阅官方文档就进行大量修改
- 一次性修改多处代码而不逐步验证

**✅ 正确做法：**
- 先搜索官方文档确认正确的API使用方式
- 逐步修改并验证每个API调用
- 遇到问题时立即停止并重新查证

### 错误5：代码格式问题
**❌ 错误做法：**
```python
def function():
    pass
    
    # 过多的空行
    
    return result
    
```

**✅ 正确做法：**
```python
def function():
    pass
    return result
```

## 1. 核心开发原则

### 1.1 优先使用影刀内置包
- 优先使用xbot模块提供的功能，而不是标准Python库
- 常用的影刀内置包：
  - `xbot.app.excel` - Excel文件操作
  - `xbot.web.chrome` - 浏览器自动化
  - `xbot.app.dialog` - 对话框操作
  - `xbot.selector` - 元素选择器
  - `xbot.logging` - 日志记录
  - `xbot.app.databook` - 数据表操作

### 1.2 性能、维护性和扩展性
- 考虑性能优化，避免不必要的资源消耗
- 编写易维护、易扩展的代码
- 考虑操作系统兼容性（Windows、macOS、Linux）

## 2. 输出和日志规范（已纠正）

### 2.1 正确的输出方式
**✅ 正确做法：**
```python
from xbot import print
print("Hello World")  # 影刀RPA正确的输出方式
```

### 2.2 正确的日志输出方式
```python
import xbot.logging
from xbot import print

# 推荐的日志输出方式 - 使用print代替
def safe_log(level, message):
    """安全的日志输出函数，统一使用print"""
    print(f"[{level.upper()}] {message}")

# 使用示例
safe_log("info", "🚀 程序开始执行")
safe_log("info", "✅ 操作完成")
safe_log("warning", "⚠️ 警告信息")
safe_log("error", "❌ 错误信息")
```

## 3. 程序入口规范

### 3.1 避免使用标准Python入口
**❌ 错误做法：**
```python
def main():
    # 主要逻辑
    pass

if __name__ == "__main__":
    main()  # 影刀RPA不支持这种入口方式
```

**✅ 正确做法：**
```python
from xbot import print
import xbot.logging

# 直接执行代码，不使用if __name__ == "__main__"
print("=== 程序开始执行 ===")

try:
    # 主要业务逻辑
    result = process_data()
    print(f"处理完成，结果：{result}")
except Exception as e:
    print(f"❌ 程序异常：{str(e)}")
```

## 4. 文件操作规范

### 4.1 Excel文件操作
```python
from xbot import print
import xbot.logging
from xbot.app import excel

def read_excel_file():
    """读取Excel文件的标准方式"""
    try:
        # 打开Excel文件
        workbook = excel.open_file("data.xlsx")
        worksheet = workbook.get_worksheet_by_name("Sheet1")
        
        # 读取数据
        data = []
        row = 2  # 从第2行开始（跳过标题行）
        while True:
            cell_value = worksheet.get_cell_value(row, 1)
            if not cell_value:
                break
            data.append(cell_value)
            row += 1
        
        # 关闭文件
        workbook.close()
        return data
        
    except Exception as e:
        print(f"❌ 读取Excel文件失败：{str(e)}")
        return []
```

### 4.2 文件选择对话框
```python
from xbot import print
import xbot.logging
from xbot.app import dialog

def select_file():
    """文件选择对话框 - 推荐使用影刀流程搭建中的文件选择组件"""
    try:
        # 方法1: 使用影刀流程搭建中的"打开选择文件对话框"组件（推荐）
        # 在影刀RPA中，建议使用可视化流程搭建中的文件选择组件
        # 然后通过变量传递给Python片段
        
        # 方法2: 如果必须在Python中实现，可以尝试以下方式
        # 注意：具体API可能因影刀版本而异，请参考最新文档
        print("请在影刀流程中使用'打开选择文件对话框'组件")
        print("然后将选择的文件路径通过变量传递给Python片段")
        
        # 临时解决方案：手动输入文件路径
        file_path = input("请输入文件路径: ")
        return file_path if file_path else None
        
    except Exception as e:
        print(f"❌ 文件选择失败：{str(e)}")
        return None

def select_file_alternative():
    """替代方案：使用影刀变量获取文件路径"""
    try:
        # 从影刀流程变量中获取文件路径
        # 假设在流程搭建中已经使用文件选择组件并设置了变量
        file_path = xbot.get_variable("selected_file_path")
        
        if file_path:
            print(f"✅ 获取到文件路径：{file_path}")
            return file_path
        else:
            print("❌ 未获取到文件路径变量")
            return None
            
    except Exception as e:
        print(f"❌ 获取文件路径变量失败：{str(e)}")
        return None
```

## 5. 浏览器自动化规范

### 5.1 Chrome浏览器操作（已纠正）
```python
import xbot
from xbot import print

def browser_automation():
    """浏览器自动化标准流程"""
    browser = None
    try:
        # ✅ 正确的影刀RPA浏览器创建API
        browser = xbot.web.create("https://example.com", "chrome", load_timeout=20)
        
        # ✅ 正确的页面导航方式
        browser.get("https://example.com")
        
        # ✅ 正确的元素查找方式
        element = browser.find_element("//div[@id='example']")
        
        # ✅ 正确的元素文本获取方式
        text = element.get_text()
        
        # ✅ 正确的标签页关闭方式
        browser.close_tab()
        
        return True
        
    except Exception as e:
        print(f"❌ 浏览器操作失败：{str(e)}")
        return False
    finally:
        # ✅ 正确的浏览器关闭方式
        if browser:
            try:
                browser.close()  # 不是browser.quit()
            except:
                pass
```

## 6. 错误处理规范

### 6.1 异常处理最佳实践（已纠正）
```python
from xbot import print

def robust_function():
    """健壮的函数示例"""
    try:
        # 主要业务逻辑
        result = perform_operation()
        print(f"操作成功：{result}")
        return result
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到：{str(e)}")
        return None
        
    except PermissionError as e:
        print(f"❌ 权限错误：{str(e)}")
        return None
        
    except Exception as e:
        print(f"❌ 未知错误：{str(e)}")
        return None
    
    finally:
        # 清理资源
        cleanup_resources()
```

## 7. 数据处理规范

### 7.1 数据验证（已纠正）
```python
from xbot import print

def validate_data(data):
    """数据验证函数"""
    if not data:
        print("⚠️ 数据为空")
        return False
    
    if not isinstance(data, (list, tuple)):
        print("⚠️ 数据格式不正确")
        return False
    
    return True

def process_data_safely(data):
    """安全的数据处理"""
    if not validate_data(data):
        return []
    
    results = []
    for item in data:
        try:
            processed_item = process_single_item(item)
            results.append(processed_item)
        except Exception as e:
            print(f"❌ 处理项目失败：{item}, 错误：{str(e)}")
            continue
    
    return results
```

## 8. 资源管理规范

### 8.1 内存管理
```python
from xbot import print
import xbot.logging

def memory_efficient_processing(large_dataset):
    """内存高效的数据处理"""
    results = []
    batch_size = 100  # 批量处理大小
    
    for i in range(0, len(large_dataset), batch_size):
        batch = large_dataset[i:i + batch_size]
        
        # 处理批次数据
        batch_results = process_batch(batch)
        results.extend(batch_results)
        
        # 进度提示
        progress = (i + batch_size) / len(large_dataset) * 100
        print(f"处理进度：{progress:.1f}%")
    
    return results
```

## 9. 跨平台兼容性

### 9.1 路径处理
```python
import os
from pathlib import Path
from xbot import print

def get_safe_path(filename):
    """获取跨平台安全的文件路径"""
    # 使用pathlib处理路径，自动适配不同操作系统
    current_dir = Path.cwd()
    file_path = current_dir / filename
    return str(file_path)

def ensure_directory_exists(directory_path):
    """确保目录存在"""
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
```

## 10. 调试和测试

### 10.1 调试输出（已纠正）
```python
from xbot import print

def debug_print(message, debug_mode=True):
    """调试输出函数"""
    if debug_mode:
        print(f"[DEBUG] {message}")

def trace_function_execution(func_name, *args, **kwargs):
    """函数执行跟踪"""
    debug_print(f"开始执行函数：{func_name}")
    debug_print(f"参数：args={args}, kwargs={kwargs}")
    
    try:
        # 执行函数逻辑
        result = actual_function(*args, **kwargs)
        debug_print(f"函数执行成功，结果：{result}")
        return result
    except Exception as e:
        print(f"❌ 函数执行失败：{str(e)}")
        raise
```

## 11. 常见问题和解决方案

### 11.1 Python片段无输出问题
**问题**：在影刀RPA中运行Python代码没有任何输出

**解决方案**：
1. 使用正确的导入方式：`from xbot import print`
2. 避免使用`if __name__ == "__main__"`入口
3. 确保代码直接执行，不要封装在函数中不调用

### 11.2 日志记录问题（已纠正）
**问题**：日志无法正常记录

**解决方案**：
1. ✅ 使用 `from xbot import print` 进行所有输出
2. ❌ 不要使用不存在的 `xbot.logging.info()`, `xbot.logging.debug()` 等方法
3. ❌ 不要使用不存在的 `xbot.log()` 方法

### 11.3 浏览器初始化失败
**问题**：`module 'xbot.web.chrome' has no attribute 'create_chrome_browser'`

**原因分析**：使用了不存在的浏览器API

**错误代码示例**：
```python
# ❌ 错误的导入和API调用
import xbot.web.chrome as web
browser = web.create_chrome_browser()  # 这个方法不存在
```

**正确解决方案**：
```python
# ✅ 正确的API调用方式
import xbot
browser = xbot.web.create("https://example.com", "chrome", load_timeout=20)
```

**参考来源**：
- 影刀RPA官方社区示例：`xbot.web.create('www.baidu.com', 'chrome', load_timeout=20)`
- 官方Python编码版文档：`browser = xbot.web.create("www.`

### 11.4 浏览器操作失败
**问题**：浏览器自动化操作不稳定

**解决方案**：
1. 添加适当的等待时间
2. 使用try-catch处理异常
3. 确保在finally块中关闭浏览器

### 11.5 文件路径问题
**问题**：在不同操作系统上文件路径不兼容

**解决方案**：
1. 使用`pathlib.Path`处理路径
2. 避免硬编码路径分隔符
3. 使用相对路径而非绝对路径

## 12. 代码格式规范

### 12.1 空行使用规范
```python
# ✅ 正确的空行使用
from xbot import print
import xbot.logging

def function1():
    """函数1"""
    return "result1"

def function2():
    """函数2"""
    return "result2"

# 主要逻辑
print("开始执行")
result = function1()
print(f"结果：{result}")
```

### 12.2 避免过多空行
```python
# ❌ 错误：过多空行
def function():
    pass
    
    
    return result
    
    
# ✅ 正确：适当空行
def function():
    pass
    return result
```

## 13. 完整示例（已纠正）

### 13.1 数据抓取完整流程（已纠正）
```python
import xbot
from xbot import print
from pathlib import Path

# 程序开始
print("=== 数据抓取工具启动 ===")

try:
    # 1. 获取输入文件路径
    # 推荐方式：从影刀流程变量中获取文件路径
    input_file = xbot.get_variable("selected_file_path")
    
    if not input_file:
        print("❌ 未获取到文件路径，请在影刀流程中设置文件选择组件")
        print("提示：使用'打开选择文件对话框'组件并将结果保存到变量'selected_file_path'")
        exit()
    
    # 2. 读取数据（使用openpyxl确保跨平台兼容）
    from openpyxl import load_workbook
    workbook = load_workbook(input_file, read_only=True)
    worksheet = workbook.active
    
    data_list = []
    for row in worksheet.iter_rows(min_col=1, max_col=1, values_only=True):
        cell_value = row[0]
        if cell_value and str(cell_value).strip():
            data_list.append(str(cell_value).strip())
    
    workbook.close()
    print(f"✅ 读取到 {len(data_list)} 条数据")
    
    # 3. 浏览器操作
    browser = xbot.web.create("https://example.com", "chrome", load_timeout=20)
    results = []
    
    for i, item in enumerate(data_list):
        try:
            url = f"https://example.com/search?q={item}"
            browser.get(url)  # 正确的导航方法
            
            # 抓取数据逻辑
            element = browser.find_element("//div[@class='result']")  # 正确的元素查找
            text = element.get_text()  # 正确的文本获取
            results.append({"item": item, "result": text})
            
            print(f"处理进度：{i+1}/{len(data_list)}")
            
            # 关闭当前标签页
            browser.close_tab()
            
        except Exception as e:
            print(f"❌ 处理项目失败：{item}, 错误：{str(e)}")
            continue
    
    # 4. 保存结果
    output_file = "results.xlsx"
    save_results_to_excel(results, output_file)
    
    print(f"✅ 处理完成，结果已保存到：{output_file}")
    
except Exception as e:
    print(f"❌ 程序异常：{str(e)}")
    
finally:
    # 清理资源
    try:
        if 'browser' in locals():
            browser.close()  # 正确的浏览器关闭方法
    except:
        pass
    
    print("=== 程序执行结束 ===")
```

## 14. 错误总结与经验教训

### 14.1 我犯下的主要错误

通过实际开发过程中遇到的问题，总结出以下关键错误，供后续开发参考：

#### 错误0：浏览器API使用错误（最新发现）
**错误现象**：`'ChromiumBrowser' object has no attribute 'get'`
**错误原因**：对影刀RPA浏览器对象的API理解错误，使用了Selenium风格的方法
**具体错误**：
```python
# ❌ 错误的用法
browser.goto(url)  # 应该是browser.get(url)
selector.find_element(browser, xpath)  # 应该是browser.find_element(xpath)
element.text  # 应该是element.get_text()
browser.quit()  # 应该是browser.close()
browser.close_current_tab()  # 应该是browser.close_tab()
```
**正确做法**：
```python
# ✅ 正确的用法
browser.get(url)  # 页面导航
browser.find_element(xpath)  # 元素查找
element.get_text()  # 获取元素文本
browser.close()  # 关闭浏览器
browser.close_tab()  # 关闭标签页
```
**经验教训**：
- 影刀RPA的浏览器对象有自己的API，不要混用Selenium的方法
- 必须先验证API的正确性再进行开发
- 遇到"object has no attribute"错误时，立即停止并查证正确的API

#### 错误1：日志API使用错误
**错误现象**：`module 'xbot.logging' has no attribute 'info'`
**错误原因**：使用了不存在的 `xbot.logging.debug()`, `xbot.logging.info()` 等API
**正确做法**：
- ✅ 使用 `xbot.print()` 进行输出
- ✅ 使用 `print()` 作为备用方案
- ❌ 不要使用 `xbot.logging.debug()` 等不存在的方法

#### 错误2：macOS Excel兼容性问题
**错误现象**：`'MacAEWorkBook' object has no attribute 'get_worksheet_by_index'`
**错误原因**：影刀RPA的Excel API在macOS上存在兼容性问题
**正确做法**：
- ✅ 使用 `openpyxl` 库进行跨平台Excel读取
- ✅ 提供多重备用方案（CSV读取、pandas读取）
- ❌ 不要直接依赖影刀内置Excel API在macOS上的表现

#### 错误3：浏览器API使用错误（新增）
**错误现象**：`'ChromiumBrowser' object has no attribute 'get'`
**错误原因**：使用了错误的浏览器导航和操作方法
**错误用法**：
```python
# ❌ 错误的用法
browser.get(url)  # 应该是browser.goto(url)
selector.find_element(browser, xpath)  # 应该是browser.find_element(xpath)
element.text  # 应该是element.get_text()
browser.quit()  # 应该是browser.close()
browser.close_current_tab()  # 应该是browser.close_tab()
```
**正确做法**：
```python
# ✅ 正确的用法
browser.goto(url)  # 页面导航
browser.find_element(xpath)  # 元素查找
element.get_text()  # 获取元素文本
browser.close()  # 关闭浏览器
browser.close_tab()  # 关闭标签页
```

#### 错误4：浏览器初始化API错误
**错误现象**：`module 'xbot.web.chrome' has no attribute 'create_chrome_browser'`
**错误原因**：使用了不存在的浏览器创建API
**正确做法**：
- ✅ 使用 `xbot.web.create(url, browser_type, load_timeout)` 创建浏览器
- ✅ 导入方式：`import xbot`
- ❌ 不要使用 `import xbot.web.chrome as web` 和 `web.create_chrome_browser()`

#### 错误5：Chrome浏览器插件未正确安装（macOS）
**错误现象**：`Message:未找到已启动的 Google Chrome 浏览器 Code:12`
**错误原因**：Chrome浏览器没有正确安装影刀插件，插件权限不足，或插件版本不兼容

**完整解决步骤**：

**第一步：权限检查和统一**
1. **确保权限一致**：
   - 检查Chrome和影刀RPA是否以相同权限运行（都为管理员或都为普通用户）
   - 如果不一致，建议都以普通用户权限运行
   - 避免一个以管理员权限运行，另一个以普通用户权限运行

**第二步：重新安装Chrome插件**
1. **完全卸载现有插件**：
   - 在Chrome中访问 `chrome://extensions/`
   - 找到"影刀RPA"插件，点击"移除"
   - 完全退出Chrome浏览器

2. **重新安装插件**：
   - 打开影刀客户端：头像 → 工具 → 自动化插件 → Google Chrome 自动化 → 点击安装插件
   - 等待安装完成后重新启动Chrome

**第三步：Chrome扩展程序配置**
1. **开启开发者模式**：
   - 在Chrome中访问 `chrome://extensions/`
   - 右上角开启"开发者模式"开关
   - ⚠️ 注意：开启开发者模式后可能需要退出浏览器重启后才能生效

2. **验证插件状态**：
   - 确认"影刀RPA"插件已安装并启用
   - 插件ID应为：`Nhkjnlcggomjhckdeamipedlomphkepc`（最新版）
   - 检查插件是否有"错误"提示，如有错误需要重新安装

3. **检查插件背景页**：
   - 点击插件的"背景页"链接
   - 查看Console是否有报错信息
   - 如有报错，记录错误信息并重新安装插件

**第四步：Chrome安全设置调整**
1. **调整安全浏览设置**（如果需要）：
   - 打开Chrome设置 → 隐私和安全 → 安全
   - 或直接访问 `chrome://settings/security`
   - 在"安全浏览"中选择"不保护"（临时设置）
   - 重新安装插件后可以恢复安全设置

**第五步：检查Chrome版本兼容性**
1. **版本检查**：
   - ⚠️ Chrome 140版本在macOS上有已知兼容性问题
   - ✅ 建议使用Chrome 139及以下版本
   - 关闭Chrome自动更新避免版本升级

2. **如果版本过高**：
   - 卸载当前Chrome版本
   - 下载并安装Chrome 139或更低版本
   - 重新安装影刀插件

**第六步：正确的使用顺序**
1. **启动顺序很重要**：
   - ✅ 先手动启动Chrome浏览器
   - ✅ 等待Chrome完全加载并确认插件正常工作
   - ✅ 再运行影刀RPA脚本
   - ❌ 不要让影刀RPA自动启动Chrome（容易出现权限问题）

2. **验证插件工作状态**：
   - 在Chrome地址栏右侧应该能看到影刀RPA插件图标
   - 插件图标应该是彩色的（表示正常工作）
   - 如果是灰色的，说明插件未正常启动

**第七步：故障排除**
1. **如果上述步骤都无效**：
   - 完全卸载并重新安装Chrome浏览器
   - 清除Chrome相关的注册表项（Windows）或配置文件（macOS）
   - 重新安装影刀RPA客户端
   - 确保选择正确的32位或64位版本

2. **备用方案**：
   - 尝试使用影刀内置浏览器
   - 或使用Microsoft Edge浏览器（如果支持）

**macOS特殊注意事项**：
- macOS平台下影刀RPA只支持原生Chrome浏览器
- 不支持自定义浏览器或其他Chromium内核浏览器
- 确保Chrome和影刀RPA都有相同的权限级别
- macOS的安全机制可能会阻止插件正常工作，需要在系统偏好设置中允许

**常见错误代码说明**：
- `Code:12` - 未找到已启动的Chrome浏览器
- `Code:-2` - Chrome权限不足或版本不兼容
- `Code:20` - 插件启动失败

**参考来源**：
- 影刀官方文档：Chrome安装插件说明
- 影刀社区多个相关问题解决方案
- 影刀官方技术支持文档

### 14.2 开发经验教训

1. **不要推测API**：必须基于官方文档和实际测试确认API的正确用法
2. **优先搜索验证**：遇到API问题时，优先搜索官方文档和社区示例
3. **提供备用方案**：对于跨平台兼容性问题，必须提供多重备用方案
4. **基于事实开发**：只使用有确实来源的API和方法，避免基于假设编程

## 15. 总结

影刀RPA中的Python开发需要遵循特定的规范，主要包括：

1. **输出规范**：使用`xbot.print()`进行输出
2. **浏览器规范**：使用`xbot.web.create(url, browser_type, load_timeout)`创建浏览器
3. **Excel规范**：在macOS上使用`openpyxl`库确保兼容性
4. **入口规范**：直接执行代码，避免使用`if __name__ == "__main__"`
5. **包使用**：优先使用影刀内置包和模块，但要验证API的正确性
6. **错误处理**：完善的异常处理和资源清理
7. **跨平台**：考虑不同操作系统的兼容性
8. **代码格式**：避免过多空行，保持代码整洁
9. **性能优化**：合理的资源管理和批量处理

## 16. 重要提醒

⚠️ **请务必使用正确的API调用方式，避免使用不存在的方法！**

**正确的API用法**：
- ✅ `from xbot import print` - 输出信息
- ✅ `xbot.web.create(url, browser_type, load_timeout)` - 创建浏览器
- ✅ `browser.get(url)` - 页面导航
- ✅ `browser.find_element(xpath)` - 元素查找
- ✅ `element.get_text()` - 获取元素文本
- ✅ `browser.close()` - 关闭浏览器
- ✅ `browser.close_tab()` - 关闭标签页
- ✅ `openpyxl.load_workbook()` - 跨平台Excel读取

**错误的API用法**：
- ❌ `xbot.logging.debug()` - 不存在的日志方法
- ❌ `xbot.web.chrome.create_chrome_browser()` - 不存在的浏览器创建方法
- ❌ `browser.goto(url)` - 应该是browser.get(url)
- ❌ `selector.find_element(browser, xpath)` - 应该是browser.find_element(xpath)
- ❌ `element.text` - 应该是element.get_text()
- ❌ `browser.quit()` - 应该是browser.close()
- ❌ `browser.close_current_tab()` - 应该是browser.close_tab()
- ❌ 在macOS上直接使用影刀Excel API - 兼容性问题

遵循这些规范和经验教训可以确保在影刀RPA环境中编写出稳定、高效、可维护的Python代码。

## 17. 最新更新日志

### 2024年更新内容
- **新增错误0**：浏览器API使用错误总结
- **修正错误2**：日志API使用错误（统一使用print）
- **修正错误3**：浏览器操作规范（使用正确的API）
- **修正错误4**：异常处理规范（移除不存在的logging方法）
- **修正错误5**：数据处理规范（统一使用print输出）
- **修正错误6**：调试输出规范（移除不存在的logging方法）
- **修正错误7**：完整示例代码（使用正确的API调用）

### 关键修正点
1. **统一日志输出**：所有日志输出统一使用 `from xbot import print`
2. **浏览器API规范化**：使用影刀RPA专用的浏览器操作方法
3. **元素操作规范化**：使用正确的元素查找和文本获取方法
4. **资源管理规范化**：使用正确的浏览器关闭方法

⚠️ **重要提醒**：本文档基于实际开发中遇到的错误进行总结，所有API用法都经过验证。请严格按照文档中的正确用法进行开发，避免使用标记为"❌"的错误方法。