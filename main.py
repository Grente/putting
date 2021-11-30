# -*- coding: utf-8 -*-


import putting
import test

def message_out(msg):
    print msg


if __name__ == "__main__":
    putting.set_out_trace(message_out)
    putting.open("test.test_func")
    test.test_func(4)
    putting.close("test.test_func")
