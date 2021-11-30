# -*- coding: utf-8 -*-

from func import *

import ast
import inspect
import traceback
import linecache

import types
import tokenize


NOT_DEBUG_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.FunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.TryExcept,
    ast.TryFinally,
)


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

    @staticmethod
    def getmaxloc(node):
        loc = None
        for node_ in ast.walk(node):
            if not hasattr(node_, 'lineno') or not hasattr(node_, 'col_offset'):
                continue
            loc_ = (node_.lineno, node_.col_offset)
            if loc is None or loc_ > loc:
                loc = loc_
        return loc
    
    def generic_visit(self, node):
        ast.NodeTransformer.generic_visit(self, node)
        if isinstance(node, ast.stmt) and not isinstance(node, NOT_DEBUG_NODES) and not (
            isinstance(node, ast.ImportFrom) and node.module == "putting"):
            line = self.getmaxloc(node)[0]
            val = ast.Name(self.m_insname, ast.Load())
            hook_func = ast.Attribute(val, "record", ast.Load())
            debug_call = ast.Call(hook_func, [], [], None, None)
            if isinstance(node, ast.Return):
                debug_statement = ast.Expr(debug_call, lineno=line)
                return [debug_statement, node]
            else:
                debug_statement = ast.Expr(debug_call, lineno=line)
                return [node, debug_statement]
        else:
            if isinstance(node, NOT_DEBUG_NODES) and not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                line = getattr(node.body[0], "lineno", 0)
                val = ast.Name(self.m_insname, ast.Load())
                hook_func = ast.Attribute(val, "record", ast.Load())
                debug_call = ast.Call(hook_func, [], [], None, None)
                debug_statement = ast.Expr(debug_call, lineno=line - 1)
                node.body.insert(0, debug_statement)
                if isinstance(node, ast.If) and node.orelse:
                    line = getattr(node.orelse[0], "lineno", 0)
                    debug_statement = ast.Expr(debug_call, lineno=line - 1)
                    node.orelse.insert(0, debug_statement)
                ast.fix_missing_locations(node)
                line = self.getmaxloc(node)[0]
                debug_statement = ast.Expr(debug_call, lineno=line)
                return [node, debug_statement]
            
            return node
            

class CInfo(object):
    OBJ_MAX_LEN = 3000
    def __init__(self, depth=0):
        self.m_ID = id(self)
        self.m_LastLine = 0
        self.m_Lines = []
        self.m_codelines = []
        self.m_firstline = 0
        self.m_reader = []
        self.m_isreturn = False
        self.m_Depth = depth
        self.m_endLine = 0
        frame = inspect.currentframe(-1).f_back
        self._initdata(frame)
        self._call_info(frame)
        
    def _initdata(self, frame):
        lines, _ = inspect.findsource(frame)
        self.m_Lines = lines
        codelines, startline = inspect.getsourcelines(frame)
        self.m_firstline = startline
        self.m_codelines = codelines
        self.m_endLine = self.m_firstline + len(self.m_codelines) - 1
    
    def _call_info(self, frame):
        loginfo = "====================(Star(ID:%s))===================" % self.m_ID
        TRACE(loginfo)
        lst = traceback.format_stack()
        strmsg = "".join(lst[:len(lst) - 3])
        loginfo = "traceback(\n" + strmsg + ")"
        TRACE(loginfo)
        multitext = ""
        tolen = False
        for _line in xrange(self.m_firstline - 1, frame.f_lineno):
            istolen, loginfo = self._format_exp(frame, multitext + self.m_Lines[_line])
            if not loginfo:
                multitext += self.m_Lines[_line]
            else:
                tolen = True
                multitext = ""
                TRACE("%s" % loginfo)
        self.m_LastLine = max(frame.f_lineno, self.m_LastLine)
    
    def _exp_info(self, frame):
        if frame.f_lineno < self.m_LastLine:
            if self.m_Depth:
                self.m_LastLine = frame.f_lineno
        multitext = ""  # 用于处理多行代码问题
        firstline = True
        self.m_endLine = self.m_firstline + len(self.m_codelines) - 1
        for _line in xrange(self.m_LastLine, frame.f_lineno):
            istolen, loginfo = self._format_exp(frame, multitext + self.m_Lines[_line])
            if not loginfo:
                multitext += self.m_Lines[_line]
            else:
                empty = len(loginfo) <= 1 or loginfo[-2] == " "
                infoline = _line + 1
                endexec = (infoline == self.m_endLine and loginfo[loginfo.rfind("\t")] == "\t")
                if firstline and not empty and (infoline != self.m_endLine or endexec) and istolen:
                    flag = "*"
                elif empty:
                    flag = ""
                else:
                    flag = ""
                if multitext:
                    linecnt = multitext.count("\n\t") + 1
                    infoline -= linecnt
                    for sline in xrange(infoline + 1, infoline + linecnt + 1):
                        loginfo = loginfo.replace("\n ", "\n%d %s" % (sline, flag), 1)
                TRACE("%d %s" % (infoline, flag) + loginfo)
                multitext = ""
                firstline = False if not empty and istolen else firstline
        return self.m_LastLine < frame.f_lineno
    
    def _end_info(self, frame):
        if self.m_isreturn:
            return False
        self.m_endLine = self.m_firstline + len(self.m_codelines) - 1
        nowline = frame.f_lineno
        rettext = self.m_Lines[nowline] if nowline < self.m_endLine else ""
        if nowline < self.m_endLine and "\treturn " not in rettext:
            return False
        if "\treturn " in rettext:
            istoken, loginfo = self._format_exp(frame, rettext)
            if not istoken and nowline < self.m_endLine:
                return False
            TRACE("%d *" % (nowline + 1) + loginfo)
        loginfo = "==================(END:Info(ID:%s))=================" % self.m_ID
        TRACE(loginfo)
        self.m_isreturn = True
        return True
    
    def _regentokenize(self, frame, tokelst):
        obstr = ""
        isobstr = False
        lasttoken = ""
        nonum = 0
        replas = {}
        _locals = frame.f_locals
        _globals = frame.f_globals
        for idx, (itype, token, srow_scol, erow_ecol, line) in enumerate(tokelst):
            if token == ".":
                isobstr = True
                nonum = 0
                if not obstr:
                    obstr += lasttoken
                obstr += token
            else:
                nonum += 1
                if nonum > 1:
                    obstr = ""
                if isobstr:
                    obstr += token
                    if idx >= len(tokelst) - 1 or tokelst[idx + 1][1] != ".":
                        replas[idx] = obstr
                isobstr = False
            lasttoken = token
                
        for idx, (itype, token, srow_scol, erow_ecol, line) in enumerate(tokelst):
            if itype == tokenize.NAME:
                word = token
                if word in _locals and not isinstance(_locals[word], functypes):
                    valstr = str(_locals[word])
                    if len(valstr) >= CInfo.OBJ_MAX_LEN:
                        valstr = valstr[:CInfo.OBJ_MAX_LEN]
                        valstr += "..."
                    token += "(%s)" % valstr
                elif word in _globals and not isinstance(_globals[word], functypes):
                    valstr = str(_globals[word])
                    if len(valstr) >= CInfo.OBJ_MAX_LEN:
                        valstr = valstr[: CInfo.OBJ_MAX_LEN]
                        valstr += "..."
                    token += "(%s)" % valstr
            tokelst[idx] = (itype, token, srow_scol, erow_ecol, line)
        for _idx, obstr in replas.iteritems():
            if "(" in obstr:
                continue
            try:
                _getval = eval(obstr, _globals, _locals)
                if isinstance(_getval, (functypes, types.ModuleType)):
                    continue
                valstr = str(_getval)
                if len(valstr) >= CInfo.OBJ_MAX_LEN:
                    valstr = valstr[:CInfo.OBJ_MAX_LEN]
                    valstr += "..."
                itype, token, srow_scol, erow_ecol, line = tokelst[_idx]
                tokelst[_idx] = (itype, "%s(%s)" % (token, valstr), srow_scol, erow_ecol, line)
            except:
                continue
            
    def _format_exp(self, frame, text):
        if "import " in text:
            return 1, text
        tokelst = []
        textlst = [text]
        
        def _reader():
            try:
                return textlst.pop(0)
            except IndexError:
                raise StopIteration
        try:
            tokenize.tokenize(_reader, lambda *agrs: tokelst.append(agrs))
        except tokenize.TokenError:
            return 0, None
        istoken = (tokelst and tokelst[0][0] != tokenize.N_TOKENS)
        self._regentokenize(frame, tokelst)
        return istoken, tokenize.untokenize(tokelst)
    
    def record(self):
        if self.m_isreturn:
            return
        frame = inspect.currentframe(-1).f_back
        self._exp_info(frame)
        if not self._end_info(frame):
            self.m_LastLine = max(frame.f_lineno, self.m_LastLine)
            

if not global().has_key("g_debugmanager") 
    g_debugmanager = CDebugManager()
