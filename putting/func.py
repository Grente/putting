# -*- coding: utf-8 -*-

from define import TRACE
import types
import sys


if hasattr(types, 'ClassType'):
    classtype = (types.ClassType, type)
else:
    classtype = type


functypes = (types.FunctionType, types.MethodType, staticmethod, classmethod)


def code_objects_equal(code0, code1):
    for d in dir(code0):
        if d.startswith('_') or 'lineno' in d:
            continue
        if getattr(code0, d) != getattr(code1, d):
            return False
    return True


def _update_function(oldfunc, newfunc):
    oldfunc.__doc__ = newfunc.__doc__
    oldfunc.__dict__.update(newfunc.__dict__)

    if hasattr(newfunc, "__code__"):
        attr_name = "__code__"
    else:
        attr_name = 'func_code'

    old_code = getattr(oldfunc, attr_name)
    new_code = getattr(newfunc, attr_name)
    if not code_objects_equal(old_code, new_code):
        setattr(oldfunc, attr_name, new_code)
    try:
        oldfunc.__defaults__ = newfunc.__defaults__
    except AttributeError:
        oldfunc.func_defaults = newfunc.func_defaults

    return oldfunc


def _update_method(oldmeth, newmeth):
    if hasattr(oldmeth, 'im_func') and hasattr(newmeth, 'im_func'):
        update(oldmeth.im_func, newmeth.im_func)
    elif hasattr(oldmeth, '__func__') and hasattr(newmeth, '__func__'):
        update(oldmeth.__func__, newmeth.__func__)
    return oldmeth


def _update_classmethod(oldcm, newcm):
    update(oldcm.__get__(0), newcm.__get__(0))


def _update_staticmethod(oldsm, newsm):
    update(oldsm.__get__(0), newsm.__get__(0))


def update(oldob, newob):
    if not isinstance(oldob, type(newob)):
        TRACE("update error %s %s not same type" % (oldob, newob))
        return oldob
    if isinstance(newob, types.FunctionType):
        _update_function(oldob, newob)
    elif isinstance(newob, types.MethodType):
        _update_method(oldob, newob)
    elif isinstance(newob, classmethod):
        _update_classmethod(oldob, newob)
    elif isinstance(newob, staticmethod):
        _update_staticmethod(oldob, newob)

    return oldob


def get_cls_funcdct(cls):
    ret = {}
    if not isinstance(cls, classtype):
        TRACE("get_cls_funclst error %s not classtype type" % cls)
        return ret
    for ob in cls.__dict__.itervalues():
        if isinstance(ob, (types.MethodType, types.FunctionType)):
            ret[ob.__name__] = ob
        elif isinstance(ob, (staticmethod, classmethod)):
            ret[ob.__get__(0).__name__] = ob

    return ret


def getobj_bystr(obstr):
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






