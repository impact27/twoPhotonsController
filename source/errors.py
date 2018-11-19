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

class ScriptError(RuntimeError):
    pass

class CameraError(RuntimeError):
    pass

def logError():
    with open('error_log.txt', 'a') as f:
        f.write(str(datetime.datetime.now()))
        f.write('\r\n')
        f.write(traceback.format_exc())
        f.write('\r\n\r\n')
