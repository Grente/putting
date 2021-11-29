# -*- coding: utf-8 -*-

import putter
import func


def open(ob_str):
    if not putter.g_hookmanager:
        return

    _, clsob, retob = func.getobj_bystr(ob_str)
    putter.g_hookmanager.add_info(retob, clsob)
    print("open debug: {0}".format(ob_str))


def close(obstr):
    if not putter.g_hookmanager:
        return

    _, clsob, retob = func.getobj_bystr(obstr)
    putter.g_hookmanager.remove_info(retob, clsob)
    print("close debug: {0}".format(obstr))


CInfo = putter.CInfo
