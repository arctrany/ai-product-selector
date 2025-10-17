# xbot.logging

## 描述
用来记录程序运行中的日志信息，如：错误信息，调试信息，警告信息，普通信息

## 方法

### debug()
记录Debug(调试)日志信息

```python
debug(text)
```

**输入参数**
- text：要记录的日志信息

**返回值**
- 无

**示例1**
```python
import xbot
def main(args):
    xbot.logging.debug('hello world')
```

该示例执行逻辑： 将调试信息" hello world " 打印在⌈ 运行日志 ⌋中

### info()
记录普通日志信息

```python
info(text)
```

**输入参数**
- text：需要记录的日志信息

**返回值**
- 无

**示例1**
```python
import xbot
def main(args):
    xbot.logging.info('hello world')
```

该示例执行逻辑： 将普通信息" hello world " 打印在⌈ 运行日志 ⌋中

### warning()
记录警告日志信息

```python
warning(text)
```

**输入参数**
- text：需要记录的日志信息

**返回值**
- 无

**示例1**
```python
import xbot
def main(args):
    xbot.logging.warning('hello world')
```

该示例执行逻辑： 将警告信息" hello world " 打印在⌈ 运行日志 ⌋中

### error()
记录错误日志信息

```python
error(text)
```

**输入参数**
- text：需要记录的日志信息

**返回值**
- 无

**示例1**
```python
import xbot
def main(args):
    xbot.logging.error('hello world')
```

该示例执行逻辑： 将错误信息" hello world " 打印在⌈ 运行日志 ⌋中