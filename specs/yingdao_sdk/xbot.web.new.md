# xbot.web

## 描述
对web网页进行各式操作，如打开网页、关闭网页

## 方法

### create()
打开网页

```python
create(url, mode='cef', load_timeout=20, stop_if_timeout=False, silent_running=False, executable_path=None, arguments=None)
```

**输入参数**
- url：目标网址
- mode：浏览器类型。目前支持的浏览器有：
  - 'cef'：影刀浏览器（默认值）
  - 'chrome'：Google Chrome浏览器
  - 'ie'：Internet Explorer浏览器
  - 'edge'：Microsoft Edge浏览器
  - '360se'：360安全浏览器
  - %localappdata%\shadowbot\ChromiumBrowser.config 文件中的ProductName：自定义浏览器 / 指纹浏览器
- load_timeout：等待加载超时时间，默认超时时间20s，若超时未加载完毕则抛出UIAError异常
- stop_if_timeout：网页加载超时是否停止加载网页，默认为 False（不停止加载）
- silent_running：是否开启运行时不抢占鼠标键盘，默认为 False
- executable_path：浏览器执行文件路径，默认为None使用默认值
- arguments：命令行参数，必须是目标浏览器支持的命令行，默认为None

**返回值**
- WebBrowser：返回打开的网页对象

**示例1**
```python
from xbot import web
def main(args):
    web_object = web.create('www.baidu.com', 'chrome', load_timeout=20)
```

该示例执行逻辑： 使用Chrome浏览器打开 百度官网

### get()
根据网址或标题获取网页

```python
get(title=None, url=None, mode='cef', load_timeout=20, use_wildcard=False, stop_if_timeout=False, open_page=False, page_url=None, silent_running=False)
```

**输入参数**
- title：网页标题
- url：网址
- mode：浏览器类型（同create方法）
- load_timeout：等待加载超时时间，默认超时时间20s
- use_wildcard：是否使用通配符方式匹配，默认为False（不使用）
- stop_if_timeout：等待加载超时时间，默认超时时间20s
- open_page：根据url或title匹配失败时，是否打开新的网页，默认为False（不打开）
- page_url：open_page=True时，指定打开的网页地址
- silent_running：是否开启运行时不抢占鼠标键盘，默认为 False

**返回值**
- WebBrowser：返回获取到的网页对象

### get_active()
获取当前选中或激活的网页

```python
get_active(mode='cef', load_timeout=20, stop_if_timeout=False, silent_running=False)
```

### get_all()
获取所有网页

```python
get_all(mode='cef', title=None, url=None, use_wildcard=False, silent_running=False)
```

### get_cookies()
获取浏览器Cookie信息

```python
get_cookies(mode='cef', url=None, name=None, domain=None, path=None)
```

### get_cookies_v2()
获取浏览器Cookie信息，支持 PartitionKey

```python
get_cookies_v2(mode='cef', name=None, url=None, domain=None, path=None, partition_key=None, secure=None, session=None)
```

### set_cookie()
设置浏览器Cookie信息

```python
set_cookie(url, mode='cef', name=None, value=None, sessionCookie=True, expires=100, domain=None, path=None, httpOnly=False, secure=False)
```

### remove_cookie()
移除指定的cookie

```python
remove_cookie(url, name, mode='cef')
```

### close_all()
关闭所有网页

```python
close_all(mode='cef', task_kill=False)
```

### handle_save_dialog()
处理网页下载对话框

```python
handle_save_dialog(file_folder, dialog_result='ok', mode='cef', file_name=None, wait_appear_timeout=20, focus_timeout=600)
```

### handle_upload_dialog()
处理网页上传对话框

```python
handle_upload_dialog(filename, dialog_result='ok', mode='cef', wait_appear_timeout=20)
```