# -*- coding: utf-8 -*-

from define import TRACE
import traceback
import sys
import types
import inspect


if hasattr(types, 'ClassType'):
    classtype = (types.ClassType, type)
else:
    classtype = type


class CPuttingManager(object):
    def __init__(self):
        self.m_ObModuleDic = {}  # {module_name: {func_name: ob}}
        self.m_ObClassDic = {}  # {module_name.class: {func_name: ob}}

    def CreateInfo(self, mod_ob, obj, cls_ob=None):
        if inspect.isfunction(obj):
            if cls_ob and inspect.isclass(cls_ob):
                # 类方法
                pass
            else:
                # 函数
                new_ob = ReplaceFunc(obj)
                setattr(mod_ob, obj.__name__, new_ob)
                self.m_ObModuleDic.setdefault(mod_ob.__name__, {})
                self.m_ObModuleDic[mod_ob.__name__][obj.__name__] = obj
        else:
            for name, v_ob in obj.__dict__.items():
                if not inspect.isfunction(v_ob):
                    continue
                if v_ob.__module__ != mod_ob.__name__:
                    continue
                if isinstance(v_ob, ReplaceFunc):
                    continue

                new_ob = ReplaceFunc(v_ob)
                setattr(mod_ob, name, new_ob)
                self.m_ObModuleDic.setdefault(mod_ob.__name__, {})
                self.m_ObModuleDic[mod_ob.__name__][v_ob.__name__] = v_ob

    def RemoveInfo(self, mod_ob, obj, cls_ob=None):
        if isinstance(obj, ReplaceFunc):
            if cls_ob and inspect.isclass(cls_ob):
                # 方法
                pass
            else:
                old_obj = self.m_ObModuleDic.setdefault(mod_ob.__name__, {}).pop(obj.__name__)
                if old_obj:
                    setattr(mod_ob, old_obj.__name__, old_obj)

        elif inspect.ismodule(obj):
            for name, v_ob in obj.__dict__.items():
                if not isinstance(v_ob, ReplaceFunc):
                    continue
                old_obj = self.m_ObModuleDic.setdefault(mod_ob.__name__, {}).pop(v_ob.__name__)
                if not old_obj:
                    continue

                setattr(mod_ob, old_obj.__name__, old_obj)


class ReplaceFunc(object):
    def __init__(self, func, is_traceback=False):
        self.func = func
        self.is_traceback = is_traceback
        self.__name__ = func.__name__

    def __call__(self, *args, **kwargs):
        TRACE("================(Calling:{0}.{1})================".format(self.func.__module__, self.func.__name__))
        TRACE(self.call_func_info(*args, **kwargs))
        if self.is_traceback:
            lst = traceback.format_stack()
            str_msg = "".join(lst[:len(lst) - 3])
            traceback_info = "traceback(\n" + str_msg + ")"
            TRACE(traceback_info)
        TRACE("==================(End:{0}.{1})==================".format(self.func.__module__, self.func.__name__))
        return self.func(*args, **kwargs)

    def call_func_info(self, *args, **kwargs):
        func_info = "{0}.{1}".format(self.func.__module__, self.func.__name__)
        arg_names = self.func.__code__.co_varnames[:self.func.__code__.co_argcount]
        func_default_dic = {}

        if self.func.func_defaults:
            for idx, name in enumerate(arg_names[-len(self.func.func_defaults):]):
                func_default_dic[name] = self.func.func_defaults[idx]

        info_list = []
        for idx, name in enumerate(arg_names[:len(args)]):
            info_list.append("{0}={1}".format(name, args[idx]))

        for idx, name in enumerate(arg_names[len(args):]):
            if name in kwargs:
                info_list.append("{0}={1}".format(name, kwargs[name]))
            else:
                info_list.append("{0}={1}".format(name, func_default_dic[name]))
        return "{0}({1})".format(func_info, ",".join(info_list))


g_manager = CPuttingManager()


def getobinfo(obstr):
    module = None
    clsname = None
    obname = None
    namelst = obstr.split(".")
    try:
        for n in xrange(len(namelst), 0, -1):
            mdname = ".".join(namelst[:n])
            try:
                __import__(mdname)
                module = sys.modules[mdname]
            except ImportError:
                continue
            if module:
                if n < len(namelst):
                    clsname = namelst[n]
                    obname = ".".join(namelst[n:])
                break
        clsob = module.__dict__.get(clsname, None)
        clsob = clsob if isinstance(clsob, classtype) else None
        retob = eval(str(obname), module.__dict__)
    except:
        clsob, retob = None, None
    if "." not in obstr:
        retob = module
    return module, clsob, retob


def OpenDebug(obstr):
    mod_ob, clsob, retob = getobinfo(obstr)
    g_manager.CreateInfo(mod_ob, retob, clsob)
    print("open debug: {0}".format(obstr))


def CloseDebug(obstr):
    mod_ob, clsob, retob = getobinfo(obstr)
    g_manager.RemoveInfo(mod_ob, retob, clsob)
    print("close debug: {0}".format(obstr))
