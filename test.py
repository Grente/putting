# -*- coding: utf-8 -*-


def test_func(arg):
    while arg > 0:
        arg -= 1
    b = arg + 2
    return b


class TestClass(object):
    def __init__(self):
        pass

    def name(self):
        return "Dog"

    def age(self):
        return 50
