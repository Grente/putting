# -*- coding: utf-8 -*-

import putting
import test

if __name__ == "__main__":
    putting.Open("test")
    test.test_func(5)
    print putting.g_manager.m_ObModuleDic
    putting.Close("test")
    test.test_func(3)
