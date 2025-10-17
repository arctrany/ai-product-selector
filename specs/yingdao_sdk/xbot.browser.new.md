# xbot.web.Browser

## 描述
对网页元素、网页进行的各种处理，如网页激活、获取网页标题、网页重新加载、取消网页加载

## 方法

### get_url()
获取网址

```python
get_url(self)
```

**输入参数**
- 无

**返回值**
- str：返回网页地址

**示例1**
```python
from xbot import web

def main(args):
    browser = web.get_active()
    url = browser.get_url()
```

该示例执行逻辑： 获取已打开的网页对象 --> 获取url地址

### get_title()
获取标题

```python
get_title(self)
```

**输入参数**
- 无

**返回值**
- str：返回网页标题

### get_text()
获取网页的文本内容

```python
get_text(self)
```

**返回值**
- str：返回网页文本内容

### get_html()
获取网页的html

```python
get_html(self)
```

**返回值**
- str：返回网页的html

### activate()
激活目标网页

```python
activate(self)
```

### navigate()
跳转到新网页

```python
navigate(self, url, load_timeout=20)
```

**输入参数**
- url：新网页地址
- load_timeout：等待加载超时时间，默认超时时间20s

### go_back()
网页后退

```python
go_back(self, load_timeout=20)
```

### go_forward()
网页前进

```python
go_forward(self, load_timeout=20)
```

### reload()
网页重新加载

```python
reload(self, ignore_cache=False, load_timeout=20)
```

**输入参数**
- ignore_cache：是否忽略缓存，默认为 False（不忽略）
- load_timeout：等待加载超时时间，默认超时时间20s

### stop_load()
网页停止加载

```python
stop_load(self)
```

### is_load_completed()
判断网页是否加载完成

```python
is_load_completed(self)
```

**返回值**
- bool：返回网页是否加载完成，完成返回 True，否则返回 False

### wait_load_completed()
等待网页加载完成

```python
wait_load_completed(self, timeout=20)
```

### close()
关闭网页

```python
close(self)
```

### execute_javascript()
在网页元素上执行JS脚本

```python
execute_javascript(self, code, argument=None)
```

**输入参数**
- code：要执行的JS脚本，必须为javascript函数形式
- argument：要传入到JS函数中的参数，必须为字符串

**返回值**
- Any：返回JS脚本执行结果

### scroll_to()
鼠标滚动网页

```python
scroll_to(self, location='bottom', behavior='instant', top=0, left=0)
```

**输入参数**
- location：网页要滚动到的位置, 可以选择 'bottom'（滚动到底部）、'top'（滚动到顶部） 或 'point'（滚动到指定位置）
- behavior：网页滚动效果，可以设置 'instant'（瞬间滚动） 或 'smooth'（平滑滚动）
- top：滚动到指定位置的纵坐标
- left：滚动到指定位置的横坐标

### handle_javascript_dialog()
处理网页对话框

```python
handle_javascript_dialog(self, dialog_result='ok', text=None, wait_appear_timeout=20)
```

### wait_appear()
等待网页元素出现

```python
wait_appear(self, selector_or_element, timeout=20)
```

**返回值**
- bool：返回网页元素是否出现，出现返回True，否则返回False

### wait_disappear()
等待网页元素消失

```python
wait_disappear(self, selector_or_element, timeout=20)
```

**返回值**
- bool：返回网页元素是否消失结果，消失返回True，否则返回False

### find_all()
在当前网页中获取与选择器匹配的相似网页元素列表

```python
find_all(self, selector, timeout=20)
```

**返回值**
- List[WebElement]：返回和目标元素相似网页元素列表

### find()
在当前网页中获取与选择器匹配的网页元素对象

```python
find(self, selector, timeout=20)
```

**返回值**
- WebElement：返回目标网页元素对象

### find_by_css()
在当前网页中获取符合CSS选择器的网页元素对象

```python
find_by_css(self, css_selector, timeout=20)
```

### find_by_xpath()
在当前网页中获取符合Xpath选择器的网页元素对象

```python
find_by_xpath(self, xpath_selector, timeout=20)
```

### is_element_displayed()
网页元素是否可见

```python
is_element_displayed(self, selector)
```

**返回值**
- bool：返回网页元素是否可见, 可见返回True，反之返回False

### extract_table()
获取选择器对应表格数据

```python
extract_table(self, table_selector, exclude_thead=False, timeout=20)
```

**返回值**
- List：返回网页上与目标元素相似的元素列表