# -*- coding: utf-8 -*-
# from controllers.pixelink import PxLerror

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

class ScriptError(RuntimeError):
    pass

class CameraError(RuntimeError):
    pass