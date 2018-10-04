# -*- coding: utf-8 -*-

class HardwareError(RuntimeError):
    pass

class MotionError(RuntimeError):
    pass

class CoordinatesError(RuntimeError):
    pass

class FocusError(RuntimeError):
    pass

class ParseError(RuntimeError):
    pass