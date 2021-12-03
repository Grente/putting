# putting
Python动态增加堆栈打印、函数调用打印，类似PySnooper打印 
解决PySnooper需要关闭进程通过装饰器增加打印的繁琐 
putting对 from module import * 导入的函数同样会生效 



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
