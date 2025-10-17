# 影刀RPA - xbot.web API 文档

## 概述
对web网页进行各式操作，如打开网页、关闭网页

## 方法

### create()
打开网页

**语法：**
```python
create(url, mode='cef', load_timeout=20, stop_if_timeout=False, silent_running=False, executable_path=None, arguments=None)
```

**参数：**
- `url`：目标网址
- `mode`：浏览器类型
  - `'cef'`：影刀浏览器（默认值）
  - `'chrome'`：Google Chrome浏览器
  - `'ie'`：Internet Explorer浏览器
  - `'edge'`：Microsoft Edge浏览器
  - `'360se'`：360安全浏览器
  - 自定义浏览器：`%localappdata%\shadowbot\ChromiumBrowser.config` 文件中的ProductName
- `load_timeout`：等待加载超时时间，默认超时时间20s
- `stop_if_timeout`：网页加载超时是否停止加载网页，默认为 False
- `silent_running`：是否开启运行时不抢占鼠标键盘，默认为 False
- `executable_path`：浏览器执行文件路径，默认为None
- `arguments`：命令行参数，必须是目标浏览器支持的命令行，默认为None

**返回值：**
WebBrowser：返回打开的网页对象

**示例：**
```python
from xbot import web
def main(args):
    web_object = web.create('www.baidu.com', 'chrome', load_timeout=20)
```

### get()
根据网址或标题获取网页

**语法：**
```python
get(title=None, url=None, mode='cef', load_timeout=20, use_wildcard=False, stop_if_timeout=False, open_page=False, page_url=None, silent_running=False)
```

**参数：**
- `title`：网页标题
- `url`：网址
- `mode`：浏览器类型（同create方法）
- `load_timeout`：等待加载超时时间，默认超时时间20s
- `use_wildcard`：是否使用通配符方式匹配，默认为False
- `stop_if_timeout`：等待加载超时时间，默认超时时间20s
- `open_page`：根据url或title匹配失败时，是否打开新的网页，默认为False
- `page_url`：open_page=True时，指定打开的网页地址
- `silent_running`：是否开启运行时不抢占鼠标键盘，默认为 False

**返回值：**
WebBrowser：返回获取到的网页对象

**示例：**
```python
from xbot import web
def main(args):
    web_object = web.get('百度', None, 'chrome', load_timeout=20, use_wildcard=False)
```

### get_active()
获取当前选中或激活的网页

**语法：**
```python
get_active(mode='cef', load_timeout=20, stop_if_timeout=False, silent_running=False)
```

**返回值：**
WebBrowser：返回获取到的网页对象

### get_all()
获取所有网页

**语法：**
```python
get_all(mode='cef', title=None, url=None, use_wildcard=False, silent_running=False)
```

**返回值：**
List[WebBrowser]：返回网页对象列表

### get_cookies()
获取浏览器Cookie信息

**语法：**
```python
get_cookies(mode='cef', url=None, name=None, domain=None, path=None)
```

**返回值：**
List[dict]：返回筛选到的cookie列表

### set_cookie()
设置浏览器Cookie信息

**语法：**
```python
set_cookie(url, mode='cef', name=None, value=None, sessionCookie=True, expires=100, domain=None, path=None, httpOnly=False, secure=False)
```

### remove_cookie()
移除指定的cookie

**语法：**
```python
remove_cookie(url, name, mode='cef')
```

### close_all()
关闭所有网页

**语法：**
```python
close_all(mode='cef', task_kill=False)
```

**参数：**
- `task_kill`：是否终止浏览器进程，默认为 False

### handle_save_dialog()
处理网页下载对话框

**语法：**
```python
handle_save_dialog(file_folder, dialog_result='ok', mode='cef', *, file_name=None, wait_appear_timeout=20, focus_timeout=600)
```

### handle_upload_dialog()
处理网页上传对话框

**语法：**
```python
handle_upload_dialog(filename, dialog_result='ok', mode='cef', *, wait_appear_timeout=20)
```
