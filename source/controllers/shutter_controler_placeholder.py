# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 11:02:12 2017

@author: quentinpeter
"""

class shutter_controller():
    def __init__(self):
        self._state = False
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def set_state(self, state):
        self._state = state
        