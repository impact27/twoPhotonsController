# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 15:19:02 2018

@author: Local_Admin
"""
from PyQt5 import QtCore


def lockmutex(f):
    def ret(cls, *args, **kargs):
        mlock = QtCore.QMutexLocker(cls._mutex)
        return f(cls, *args, **kargs)
    return ret
