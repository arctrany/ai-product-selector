# xbot.web.Element

## 描述
网页元素对象，用于对网页中的各种元素进行操作

## 方法

### click()
点击网页元素

```python
click(self, simulative=True, delay_after=1, anchor=None)
```

**输入参数**
- simulative：是否模拟人工点击，默认为True
- delay_after：执行成功后延迟时间，默认延迟1s
- anchor：锚点位置

### input()
在网页元素中输入文本

```python
input(self, text, simulative=True, delay_after=1, contains_hotkey=False, anchor=None, append=False)
```

**输入参数**
- text：要输入的文本内容
- simulative：是否模拟人工输入，默认为True
- delay_after：执行成功后延迟时间，默认延迟1s
- contains_hotkey：是否包含热键，默认为False
- anchor：锚点位置
- append：是否追加输入，默认为False

### clipboard_input()
通过剪切板输入文本

```python
clipboard_input(self, text, append=False, anchor=None)
```

### focus()
选中(激活)当前元素

```python
focus(self)
```

### hover()
鼠标悬停在当前元素

```python
hover(self, simulative=True, delay_after=1)
```

### get_text()
获取当前网页元素的文本内容

```python
get_text(self)
```

**返回值**
- str：返回当前网页元素的文本内容

### get_html()
获取当前网页元素的html内容

```python
get_html(self)
```

**返回值**
- str：返回当前网页元素的html内容

### get_value()
获取当前网页元素的值

```python
get_value(self)
```

**返回值**
- str：返回当前网页元素的值

### set_value()
设置当前网页元素的值

```python
set_value(self, value: str)
```

### check()
设置网页复选框

```python
check(self, mode='check', delay_after=1)
```

**输入参数**
- mode：设置网页复选框的结果，可传入 'check'（选中）、'uncheck'（取消选中）或'toggle'（反选），默认为 check（选中）

### select()
按选项内容设置单选网页下拉框元素

```python
select(self, item: str, mode='fuzzy', delay_after=1)
```

### select_multiple()
按选项内容设置多选网页下拉框元素

```python
select_multiple(self, items: typing.List[str], mode='fuzzy', append=False, delay_after=1)
```

### select_by_index()
按下标设置单选网页下拉框元素

```python
select_by_index(self, index: int, delay_after=1)
```

### select_multiple_by_index()
按下标设置多选网页下拉框元素

```python
select_multiple_by_index(self, indexes: typing.List[int], append=False, delay_after=1)
```

### get_select_options()
获取网页下拉框的值

```python
get_select_options(self)
```

**返回值**
- List[Tuple]：返回下拉框值（选项，选项值，被选中状态）的列表

### set_attribute()
设置网页元素属性值

```python
set_attribute(self, name: str, value: str)
```

### get_attribute()
获取网页元素属性值

```python
get_attribute(self, name: str)
```

**返回值**
- str：返回网页元素目标属性的属性值

### get_all_attributes()
获取网页元素全部属性值

```python
get_all_attributes(self)
```

**返回值**
- List[Tuple]：返回目标网页元素的全部属性名与属性值的组合列表

### get_bounding()
获取网页元素的边框属性组合

```python
get_bounding(self, to96dpi=True)
```

**返回值**
- Tuple：返回网页元素的边框属性组合，如('x', 'y', 'width', 'height')

### extract_table()
获取当前元素所属表格的内容列表

```python
extract_table(self)
```

**返回值**
- List[Tuple]: 返回数据表格内容

### screenshot()
对目标元素进行截图, 并将图片进行保存

```python
screenshot(self, folder_path, filename=None)
```

### screenshot_to_clipboard()
对目标元素进行截图, 并将图片保存至剪切板

```python
screenshot_to_clipboard(self)
```

### is_checked()
判断网页复选框元素是否被选中

```python
is_checked(self)
```

**返回值**
- bool：返回元素的选中状态, 选中返回True， 否则返回False

### is_enabled()
判断网页元素是否可用

```python
is_enabled(self)
```

**返回值**
- bool：返回元素的可用状态, 可用返回True，否则返回False

### is_displayed()
判断网页元素是否可见

```python
is_displayed(self)
```

**返回值**
- bool：返回元素的可见状态, 可见返回True，否则返回False

### drag_to()
拖拽网页元素到指定位置

```python
drag_to(self, simulative=True, behavior='smooth', top=0, left=0, delay_after=1)
```

### get_all_select_items()
获取网页下拉框元素的全部下拉选项

```python
get_all_select_items(self)
```

**返回值**
- List[str]：返回网页下拉框全部下拉选项列表

### get_selected_item()
获取网页下拉框当前选中的项

```python
get_selected_item(self)
```

**返回值**
- List[str]：返回网页下拉框当前全部选中项列表

### upload()
自动完成点击上传按钮、在文件选择对话框中输入待上传文件等系列操作

```python
upload(self, file_names, clipboard_input=True, focus_timeout=1000, dialog_timeout=20)
```

### download()
自动完成点击下载按钮、在文件保存对话框中输入保存文件信息等系列操作

```python
download(self, file_folder, file_name, wait_complete=True, wait_complete_timeout=300, clipboard_input=True, focus_timeout=1000, dialog_timeout=20)
```

**返回值**
- str：返回下载文件所在的位置