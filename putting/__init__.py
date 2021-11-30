# -*- coding: utf-8 -*-

import putter
import func
import define


def open(ob_str):
    _, clsob, retob = func.getobj_bystr(ob_str)
    putter.g_debugmanager.add_info(retob, clsob)
    print("open debug: {0}".format(ob_str))


def close(obstr):
    _, clsob, retob = func.getobj_bystr(obstr)
    putter.g_debugmanager.remove_info(retob, clsob)
    print("close debug: {0}".format(obstr))


CInfo = putter.CInfo


def set_out_trace(trace_fun):
    define.TRACE = trace_fun
    reload(func)
    reload(putter)

