# -*- coding: utf-8 -*-

from define import *


def test_func(n):
    for i in xrange(n):
        print(i)
    return 8 + 3


class TestClass(object):
    def __init__(self):
        pass

    def name(self, b):
        return "Dog"

    @staticmethod
    def age(b):
        return "Dog", b

    @classmethod
    def tall(cls):
        return "180cm"
