#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 19:34:53 2018

@author: quentinpeter
"""
from PyQt5 import QtCore
import time

class Hardware_Singleton(QtCore.QObject):
    """Singleton to connect stage"""
    
    _mutex = QtCore.QMutex()
    
    def __init__(self, name, connect_callback=None):
        super().__init__()
        QtCore.QMutexLocker(Hardware_Singleton._mutex)
        if "_number_instances" not in dir(type(self)):
            type(self)._hardware = None
            type(self)._isConnecting = False
            type(self)._mutex = QtCore.QMutex()
            type(self)._number_instances = 1
            type(self)._name = name
            type(self)._thread = Hardware_Thread(self._set_hardware, self._open_connection)
        else:
            type(self)._number_instances += 1
        
        self._connect_callback = connect_callback
        self._connect()

    def __getattr__(self, name):
        if type(self)._isConnecting and not self._isConnected():
            type(self)._mutex.lock()
            print(f"Waiting because of a call to {self._name}")
            type(self)._mutex.unlock()
            type(self)._thread.wait(60000)
            time.sleep(1)
        if not self._isConnected():
            raise RuntimeError(f"{self._name} not connected")
        else:
            return getattr(type(self)._hardware, name)
        
    def __setattr__(self, name, value):
        if type(self)._isConnecting and not self._isConnected():
            type(self)._mutex.lock()
            print(f"Waiting because of a call to {self._name}")
            type(self)._mutex.unlock()
            type(self)._thread.wait(60000)
            time.sleep(1)
        if not self._isConnected():
            raise RuntimeError(f"{self._name} not connected")
        else:
            getattr(type(self)._hardware, name) = value
        
        
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
        print(f'{self._name} set')
        type(self)._isConnecting = False
        if self._isConnected() and self._connect_callback is not None:
            self._connect_callback()

    def _connect(self):
        QtCore.QMutexLocker(type(self)._mutex)
        if not self._isConnected() and not type(self)._isConnecting:
            type(self)._isConnecting = True
            type(self)._thread.start()

    def _disconnect(self):
        QtCore.QMutexLocker(type(self)._mutex)
        if self._isConnected():
            self._close_connection()
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
        HW = self._newConnection()
        self._callback(HW)