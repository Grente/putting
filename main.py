# -*- coding: utf-8 -*-


import putting
import test


if __name__ == "__main__":
    putting.open("test.test_func")
    test.test_func(4)
    putting.close("test.test_func")
