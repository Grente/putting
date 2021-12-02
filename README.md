# putting
Python动态增加堆栈打印、函数调用打印，类似PySnooper打印
可以不关闭进程，增加\关闭 打印



## 版本：python2.7

## 例子：

```python
def test_func(arg):
    while arg > 0:
        arg -= 1
    b = arg + 2
    print arg
    return b
```

```python
putting.open("test.test_func")
```

效果：

```python
open debug: test.test_func
====================(Star(ID:46903704))===================
traceback(
  File "main.py", line 14, in <module>
    test.test_func(4)
)
def test_func(arg(4)):

7 *    while arg(4) > 0:

8 *        arg(3) -= 1

9 *    b(2) = arg(0) + 2

0
10 *    print arg(0)

11     return b(2)

==================(END:Info(ID:46903704))=================
```
