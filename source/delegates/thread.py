# -*- coding: utf-8 -*-
"""
Created on Tue Sep 11 15:19:02 2018

@author: Local_Admin
"""
from PyQt5 import QtCore

class MutexContainer():
    def __init__(self, mutex):
        self.mutex = mutex
    def __enter__(self):
        self.mutex.lock()
    def __exit__(self, type, value, traceback):
        self.mutex.unlock()
        
        
def lockmutex(f):
    def ret(cls, *args, **kargs):
        with MutexContainer(cls._mutex):
            return f(cls, *args, **kargs)
        raise RuntimeError("How can this be here?")
    return ret
