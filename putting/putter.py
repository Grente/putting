# -*- coding: utf-8 -*-

from func import *

import ast
import inspect
import traceback
import linecache

import types


class CDebugManager(object):
    def __init__(self):
        self.m_ObDct = {}

    def add_info(self, obj, clsob=None):
        self.get_obj(obj).add_info(obj, clsob)

    def remove_info(self, obj, clsob=None):
        self.get_obj(obj).remove(obj, clsob)
        if isinstance(obj, types.ModuleType):
            self.m_ObDct.pop(id(obj), None)

    def get_obj(self, obj):
        mod = inspect.getmodule(obj)
        if not mod:
            TRACE("[ERROR]:not found  %s belong module" % obj)
            return
        linecache.checkcache()
        keyid = id(mod)
        if keyid not in self.m_ObDct:
            ob = CDebugModule(mod)
            self.m_ObDct[keyid] = ob
        else:
            ob = self.m_ObDct[keyid]
        return ob


class CDebugModule(object):
    def __init__(self, mod):
        self.m_mod = mod
        self.m_name = mod.__name__
        self.m_file = mod.__file__

    def _getusefulobs(self, obj):
        oblst = []
        if isinstance(obj, types.ModuleType):
            for name, ob in obj.__dict__.iteritems():
                if not isinstance(ob, classtype) and not isinstance(ob, types.FunctionType):
                    continue
                if ob.__module__ != self.m_name:
                    continue
                oblst.append(ob)
        else:
            oblst.append(obj)
        return oblst

    def _getobname(self, ob):
        if isinstance(ob, (types.MethodType, types.FunctionType)):
            retname = ob.__name__
        elif isinstance(ob, (staticmethod, classmethod)):
            retname = ob.__get__(0).__name__
        elif isinstance(ob, classtype):
            retname = ob.__name__
        else:
            retname = ob.__name__
        return retname

    def add_info(self, obj, clsob=None, depth=0):
        mod_tree = ast.parse(inspect.getsource(self.m_mod), self.m_file)
        tree_info = {}
        for _obj in mod_tree.body:
            if isinstance(_obj, (ast.FunctionDef, ast.ClassDef)):
                tree_info[_obj.name] = _obj
        oblst = self._getusefulobs(obj)
        addoblst = []
        for ob in oblst:
            if isinstance(ob, functypes) and clsob:
                _tree = None
                clsname = self._getobname(clsob)
                _clstree = tree_info.get(clsname)
                for tree_ob in _clstree.body:
                    if not isinstance(tree_ob, ast.FunctionDef):
                        continue
                    if tree_ob.name != self._getobname(ob):
                        continue
                    _tree = tree_ob
                    break
            else:
                _tree = tree_info.get(self._getobname(ob))
            if not _tree:
                TRACE("[ERROR]:%s has not found %s tree" % (self.m_name, self._getobname(ob)))
                continue
            if isinstance(ob, classtype):
                treelst = [tree_ob for tree_ob in _tree.body if isinstance(tree_ob, ast.FunctionDef)]
            else:
                treelst = [_tree]
            for _tree_ob in treelst:
                CDebugWrap(_tree_ob).visit(_tree_ob)
                ast.fix_missing_locations(_tree_ob)

            addoblst.append(ob)

        if not addoblst:
            return
        env = {}
        code = compile(mod_tree, self.m_file, 'exec')
        exec(code, env)

        for ob in addoblst:
            name = self._getobname(ob)
            if isinstance(ob, functypes) and clsob:
                newob = getattr(env[self._getobname(clsob)], name, None)
            else:
                newob = env[name]
            if not newob:
                continue
            self._update_ob(name, ob, newob)

    def remove(self, obj, clsob=None):
        # 编译原来的模块
        oblst = self._getusefulobs(obj)
        _tree = ast.parse(inspect.getsource(self.m_mod), self.m_file)
        code = compile(_tree, self.m_file, 'exec')
        env = {}
        exec(code, env)
        for ob in oblst:
            name = self._getobname(ob)
            if isinstance(ob, functypes) and clsob:
                newob = getattr(env[self._getobname(clsob)], name, None)
            else:
                newob = env[name]
            if not newob:
                continue
            self._update_ob(name, ob, newob)

    def _update_ob(self, name, oldob, newob):
        if isinstance(oldob, classtype):
            olddct = get_cls_funcdct(oldob)
            newdct = get_cls_funcdct(newob)
        else:
            olddct = {name: oldob}
            newdct = {name: newob}
        for _name, oldob in olddct.iteritems():
            update(oldob, newdct.get(_name, None))


class CDebugWrap(ast.NodeTransformer):
    def __init__(self, node):
        self.m_insname = "_ins_tx"
        ast.NodeTransformer.__init__(self)
        self._initnode(node)

    def _initnode(self, node):
        target = ast.Name(self.m_insname, ast.Store())
        name = ast.Name("CInfo", ast.Load())
        call_func = ast.Call(name, [], [], None, None)
        line = getattr(node.body[0], "lineno", 0)
        state = ast.Assign(targets=[target], value=call_func, lineno=line - 1)
        node.body.insert(0, state)
        ast.fix_missing_locations(node)

        _alias = ast.alias("CInfo", None)
        _impname = ast.Name("putting", ast.Store())
        line = getattr(node.body[0], "lineno", 0)
        _impob = ast.ImportFrom(module='putting', names=[_alias], level=0, lineno=line)
        node.body.insert(0, _impob)
        ast.fix_missing_locations(node)


class CInfo(object):
    def __init__(self):
        self.m_ID = id(self)
        self.call_info()

    def call_info(self):
        loginfo = "====================(Star(ID:%s))===================" % self.m_ID
        TRACE(loginfo)
        lst = traceback.format_stack()
        strmsg = "".join(lst[:len(lst) - 3])
        loginfo = "traceback(\n" + strmsg + ")"
        TRACE(loginfo)
        TRACE("====================(End(ID:%s))===================" % self.m_ID)


g_hookmanager = CDebugManager()
