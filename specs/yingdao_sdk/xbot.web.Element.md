# 影刀RPA - xbot.web.Element API 文档

## 概述
对网页元素进行处理，如获取相似网页元素、查找目标元素父/子元素、点击元素

## 方法

### 元素关系方法

#### parent()
获取当前元素的父元素

**语法：**
```python
parent(self)
```

**返回值：**
WebElement：返回当前元素的父元素

#### children()
获取当前元素的所有子元素

**语法：**
```python
children(self)
```

**返回值：**
List[WebElement]：返回当前元素的所有子元素

#### child_at()
获取指定位置的子元素

**语法：**
```python
child_at(self, index)
```

**参数：**
- `index`：子元素的位置索引，从0开始计数

**返回值：**
WebElement：返回指定位置的子元素

#### previous_sibling()
获取上一个并列的兄弟元素

**语法：**
```python
previous_sibling(self)
```

**返回值：**
WebElement：返回上一个并列的兄弟元素

#### next_sibling()
获取下一个并列的兄弟元素

**语法：**
```python
next_sibling(self)
```

**返回值：**
WebElement：返回下一个并列的兄弟元素

### 交互方法

#### click()
单击当前网页元素

**语法：**
```python
click(self, button='left', simulative=True, keys='none', delay_after=1, move_mouse=False, anchor=None)
```

**参数：**
- `button`：要点击的鼠标按键，可传入'left' 或 'right'，默认为 'left'
- `simulative`：是否模拟人工点击, 默认为True
- `move_mouse`：是否显示鼠标移动轨迹, 默认为 True
- `keys`：点击鼠标时的键盘辅助按钮，可用辅助按键有——none、alt、ctrl、shift 和 win
- `delay_after`：执行成功后延迟时间，默认延迟 1s
- `anchor`：锚点，鼠标点击元素的位置以及偏移量元组

#### dblclick()
双击当前网页元素

**语法：**
```python
dblclick(self, simulative=True, delay_after=1, move_mouse=False, anchor=None)
```

#### input()
填写网页输入框

**语法：**
```python
input(self, text: str, simulative=True, append=False, contains_hotkey=False, force_img_ENG=False, send_key_delay=50, focus_timeout=1000, delay_after=1, anchor=None)
```

**参数：**
- `text`：需要填写到输入框中的文本内容
- `simulative`：是否模拟人工点击, 默认为True
- `append`：是否追加输入，追加输入会保留输入框中原有内容
- `contains_hotkey`：输入内容是否包含快捷键
- `send_key_delay`：两次按键之间的时间间隔
- `delay_after`：执行成功后延迟时间，默认延迟 1s
- `anchor`：锚点，鼠标点击元素的位置以及偏移量元组
- `focus_timeout`：焦点超时时间，默认1000毫秒

#### clipboard_input()
通过剪切板填写网页输入框(可有效避免输入法问题)

**语法：**
```python
clipboard_input(self, text: str, append=False, delay_after=1, anchor=None, focus_timeout=1000)
```

#### focus()
选中(激活)当前元素

**语法：**
```python
focus(self)
```

#### hover()
鼠标悬停在当前元素

**语法：**
```python
hover(self, simulative=True, delay_after=1)
```

### 获取内容方法

#### get_text()
获取当前网页元素的文本内容

**语法：**
```python
get_text(self)
```

**返回值：**
str：返回当前网页元素的文本内容

#### get_html()
获取当前网页元素的html内容

**语法：**
```python
get_html(self)
```

**返回值：**
str：返回当前网页元素的html内容

#### get_value()
获取当前网页元素的值

**语法：**
```python
get_value(self)
```

**返回值：**
str：返回当前网页元素的值

#### set_value()
设置当前网页元素的值

**语法：**
```python
set_value(self, value: str)
```

**参数：**
- `value`：需要设置到网页元素上的文本值

### 表单控件方法

#### check()
设置网页复选框

**语法：**
```python
check(self, mode='check', delay_after=1)
```

**参数：**
- `mode`：设置网页复选框的结果，可传入 'check'（选中）、'uncheck'（取消选中）或'toggle'（反选）

#### select()
按选项内容设置单选网页下拉框元素

**语法：**
```python
select(self, item: str, mode='fuzzy', delay_after=1)
```

**参数：**
- `item`：要设置的网页下拉框元素的某一项的文本内容
- `mode`：查找项的匹配模式，可以选择 'fuzzy'（模糊匹配） 'exact'（精准匹配）或'regex'（正则匹配）

#### select_multiple()
按选项内容设置多选网页下拉框元素

**语法：**
```python
select_multiple(self, items: typing.List[str], mode='fuzzy', append=False, delay_after=1)
```

#### select_by_index()
按下标设置单选网页下拉框元素

**语法：**
```python
select_by_index(self, index: int, delay_after=1)
```

#### select_multiple_by_index()
按下标设置多选网页下拉框元素

**语法：**
```python
select_multiple_by_index(self, indexes: typing.List[int], append=False, delay_after=1)
```

#### get_select_options()
获取网页下拉框的值

**语法：**
```python
get_select_options(self)
```

**返回值：**
List[Tuple]：返回下拉框值（选项，选项值，被选中状态）的列表

### 属性操作方法

#### set_attribute()
设置网页元素属性值

**语法：**
```python
set_attribute(self, name: str, value: str)
```

**参数：**
- `name`：元素属性名称
- `value`：要设置的元素属性值

#### get_attribute()
获取网页元素属性值

**语法：**
```python
get_attribute(self, name: str)
```

**参数：**
- `name`：元素属性名称

**返回值：**
str：返回网页元素目标属性的属性值

#### get_all_attributes()
获取网页元素全部属性值

**语法：**
```python
get_all_attributes(self)
```

**返回值：**
List[Tuple]：返回目标网页元素的全部属性名与属性值的组合列表

### 位置和状态方法

#### get_bounding()
获取网页元素的边框属性组合

**语法：**
```python
get_bounding(self, to96dpi=True)
```

**参数：**
- `to96dpi`：是否需要将边框属性转换成dpi为96的对应属性值

**返回值：**
Tuple：返回网页元素的边框属性组合，如('x', 'y', 'width', 'height')

#### is_checked()
判断网页复选框元素是否被选中

**语法：**
```python
is_checked(self)
```

**返回值：**
bool：返回元素的选中状态

#### is_enabled()
判断网页元素是否可用

**语法：**
```python
is_enabled(self)
```

**返回值：**
bool：返回元素的可用状态

#### is_displayed()
判断网页元素是否可见

**语法：**
```python
is_displayed(self)
```

**返回值：**
bool：返回元素的可见状态

### 高级操作方法

#### drag_to()
拖拽网页元素到指定位置

**语法：**
```python
drag_to(self, simulative=True, behavior='smooth', top=0, left=0, delay_after=1)
```

#### get_all_select_items()
获取网页下拉框元素的全部下拉选项

**语法：**
```python
get_all_select_items(self)
```

**返回值：**
List[str]：返回网页下拉框全部下拉选项列表

#### get_selected_item()
获取网页下拉框当前选中的项

**语法：**
```python
get_selected_item(self)
```

**返回值：**
List[str]：返回网页下拉框当前全部选中项列表

#### upload()
自动完成点击上传按钮、在文件选择对话框中输入待上传文件等系列操作

**语法：**
```python
upload(self, file_names, clipboard_input=True, focus_timeout=1000, dialog_timeout=20)
```

**参数：**
- `file_names`：上传文件列表，比如[r"C:\test.txt",r"C:\text1.txt"]
- `clipboard_input`：文件选择是否用剪切板输入，默认为True
- `focus_timeout`：焦点超时时间，默认1000毫秒
- `dialog_timeout`：点击上传按钮后，等待文件选择框的最大时间,单位（秒）

#### download()
自动完成点击下载按钮、在文件保存对话框中输入保存文件信息等系列操作

**语法：**
```python
download(self, file_folder, file_name, wait_complete=True, wait_complete_timeout=300, clipboard_input=True, focus_timeout=1000, dialog_timeout=20)
```

**参数：**
- `file_folder`：保存下载文件的文件夹
- `file_name`：自定义保存的文件名，若为空，用下载资源默认文件名
- `wait_complete`：是否等待下载完成，默认为True
- `wait_complete_timeout`：等待下载超时时间，单位(秒)，默认为300秒

**返回值：**
str：返回下载文件所在的位置

#### extract_table()
获取当前元素所属表格的内容列表

**语法：**
```python
extract_table(self)
```

**返回值：**
List[Tuple]: 返回数据表格内容

#### screenshot()
对目标元素进行截图, 并将图片进行保存

**语法：**
```python
screenshot(self, folder_path, filename=None)
```

**参数：**
- `folder_path`：元素截图后图片需要保存的路径
- `filename`：截图后图片保存后的名称，可为空，为空时会根据当前时间自动生成文件名称

#### screenshot_to_clipboard()
对目标元素进行截图, 并将图片保存至剪切板

**语法：**
```python
screenshot_to_clipboard(self)
```
