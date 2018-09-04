#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 19:34:53 2018

@author: quentinpeter
"""
from PyQt5 import QtCore

class Hardware_Singleton(QtCore.QObject):
    """Singleton to connect stage"""
    
    _mutex = QtCore.QMutex()
    
    def __init__(self, name, connect_callback=None):
        super().__init__()
        QtCore.QMutexLocker(Hardware_Singleton._mutex)
        if "_number_instances" not in type(self):
            type(self)._hardware = None
            type(self)._isConnecting = False
            type(self)._mutex = QtCore.QMutex()
            type(self)._number_instances = 1
        else:
            type(self)._number_instances += 1
        self._connect_callback = connect_callback
        self._name = name
        self._thread = Hardware_Thread(self._set_hardware, self._open_connection)
        self._connect()

    def __getattr__(self, name):
        if not self._isConnected():
            raise RuntimeError(f"{self.name} not connected")
        else:
            return getattr(type(self)._hardware, name)
        
    def __del__(self):
        type(self)._number_instances -= 1
        if type(self)._number_instances == 0:
            self._disconnect()

    def _isConnected(self):
        QtCore.QMutexLocker(type(self)._mutex)
        return type(self)._hardware is not None

    def _set_hardware(self, hardware):
        QtCore.QMutexLocker(type(self)._mutex)
        
        if hardware is None or hardware == type(self)._hardware:
            return
    
        type(self)._hardware = hardware
        type(self)._isConnecting = False
        if self._isConnected() and self._connect_callback is not None:
            self._connect_callback()

    def _connect(self):
        QtCore.QMutexLocker(type(self)._mutex)
        if not self._isConnected() and not type(self)._isConnecting:
            type(self)._isConnecting = True
            self.thread.start()

    def _disconnect(self):
        QtCore.QMutexLocker(type(self)._mutex)
        if self._isConnected():
            self.close_connection()
            type(self)._hardware = None
            
    def _open_connection(self):
        pass
    
    def _close_connection(self):
        pass
            
class Hardware_Thread(QtCore.QThread):
    def __init__(self, callback, newConnection):
        super().__init__()
        self._callback = callback
        self._newConnection = newConnection

    def run(self):
        self._callback(self._newConnection())