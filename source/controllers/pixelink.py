#!/usr/bin/env python
#   --------------------------------------------------------------------------
#   Copyright 2014 SRE-F, ESA (European Space Agency)
#       Hans Smit <hsmit@rssd.esa.int>
#
#   This code is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 or 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#   --------------------------------------------------------------------------
"""
A wrapper around the PixeLINK API exposed in PxlAPi40.dll.
The complete driver implementation is not yet complete, but the core
functionality for adjusting ROI, shutter time, and frame grabbing are in place.

There are 2 implementations:
    1) PxLapi class: the "core" c-style function calls with either returned error
       codes or thrown exceptions.
    2) PixeLINK class: high level objected-oriented implementation.

There are 2 optional dependencies:
    1) numpy: open source numerical library that has a N-dimensional array object
    2) esapy.imaging.cvcamera: ESA SRF-F image processing package

If both packages are not available, then the module will degrade "nicely" and
still function properly, but with limited functionality related to image
and data processing.

There are limitations as well:
    1) single channel (uint8) gray scale (no color frame grabbing).
    2) no image processing routines. This can be implemented using scipy.

This module was tested using the camera model: PixeLINK GigE PL-B781G.

"""
from __future__ import print_function

__created__   = "12/02/2014"
__author__    = "Hans Smit"
__email__     = "hsmit@rssd.esa.int"
__copyright__ = "Copyright 2014, SRE-F, ESA"
__license__   = "GNU GPL"
__version__   = "1.0.1"

#TODO: need to dynamically search for this
DLL_PATH = r'c:\windows\system32\pxlapi40.dll'
HAS_NUMPY = False

import os
import threading
import ctypes as C
import ctypes.wintypes as W
from functools import wraps

try:
    # try and import numpy, if it is not installed on the user's computer
    # then use raw ctypes string buffers instead.
    import numpy
    HAS_NUMPY = True
except ImportError as ex:
    HAS_NUMPY = False
    print("warning: pixelink.py numpy is not installed. Using raw ctypes buffers instead.")

try:
    # try and import my Camera class that handles image processing
    # if this fails, define a 'dummy' Camera class interface instead.
    from esapy.imaging.cvcamera import Camera
except ImportError:
    class Camera(object):
        def __init__(self, *args, **kwargs):
            """ constructor """
        def get_property_value(self, key):
            """ to be overridden by sub class. """
        def set_property_value(self, key, val):
            """ to be overridden by sub class. """
        def _get_frame(self):
            """ to be overridden by sub class. """
        def grab(self):
            return self._get_frame()


# =============================================================================
class PxLapi(object):
    """
    The PxLapi class is a thin wrapper around the dynamic library (.dll, .so)
    that exposes the PixeLINK API. This uses ctypes to adapt from C to Python.
    """
    START_STREAM   = 0
    PAUSE_STREAM   = 1
    STOP_STREAM    = 2

    ## Feature IDs list for future Python driver functionality
    #define FEATURE_BRIGHTNESS              0
    #define FEATURE_PIXELINK_RESERVED_1     1
    #define FEATURE_SHARPNESS               2
    #define FEATURE_COLOR_TEMP              3
    #define FEATURE_HUE                     4
    #define FEATURE_SATURATION              5
    #define FEATURE_GAMMA                   6
    FEATURE_SHUTTER                = 7
    FEATURE_GAIN                   = 8
    #define FEATURE_IRIS                    9
    #define FEATURE_FOCUS                   10
    #define FEATURE_SENSOR_TEMPERATURE      11
    #define FEATURE_TRIGGER                 12
    #define FEATURE_ZOOM                    13
    #define FEATURE_PAN                     14
    #define FEATURE_TILT                    15
    #define FEATURE_OPT_FILTER              16
    #define FEATURE_GPIO                    17
    #define FEATURE_FRAME_RATE              18
    FEATURE_ROI                    = 19
    #define FEATURE_FLIP                    20
    #define FEATURE_PIXEL_ADDRESSING        21
    #define FEATURE_PIXEL_FORMAT            22
    #define FEATURE_EXTENDED_SHUTTER        23
    #define FEATURE_AUTO_ROI                24
    #define FEATURE_LOOKUP_TABLE            25
    #define FEATURE_MEMORY_CHANNEL          26
    #define FEATURE_WHITE_SHADING           27          /* Seen in Capture OEM as White Balance */
    #define FEATURE_ROTATE                  28
    #define FEATURE_IMAGER_CLK_DIVISOR      29          /* DEPRECATED - New applications should not use. */
    #define FEATURE_TRIGGER_WITH_CONTROLLED_LIGHT   30  /* Allows trigger to be used more deterministically where  lighting cannot be controlled.                         */
    #define FEATURE_MAX_PIXEL_SIZE          31          /* The number of bits used to represent 16-bit data (10 or 12) */
    #define FEATURE_BODY_TEMPERATURE		32
    #define FEATURE_MAX_PACKET_SIZE  		33
    #define FEATURES_TOTAL                  34

    ## Feature aliases for backward compatibility
    #define FEATURE_DECIMATION              FEATURE_PIXEL_ADDRESSING   /* Really, decimation is just one type of pixel addressing          */
    #define FEATURE_EXPOSURE                FEATURE_SHUTTER            /* IIDC'c EXPOSURE is equivalent to feature SHUTTER                 */
    #define FEATURE_WHITE_BAL               FEATURE_COLOR_TEMP         /* IIDC's white balance is usually referred to as color temperature */
    #define FEATURE_TEMPERATURE             FEATURE_SENSOR_TEMPERATURE /* Now more specific, as the temperature is from the sensor */

    ## For PxLGetCameraFeatures
    #define FEATURE_ALL 0xFFFFFFFF

    ## Feature Flags
    #define FEATURE_FLAG_PRESENCE       0x00000001  /* The feature is supported on this camera. */
    #define FEATURE_FLAG_MANUAL         0x00000002
    #define FEATURE_FLAG_AUTO           0x00000004
    #define FEATURE_FLAG_ONEPUSH        0x00000008
    #define FEATURE_FLAG_OFF            0x00000010
    #define FEATURE_FLAG_DESC_SUPPORTED 0x00000020
    #define FEATURE_FLAG_READ_ONLY      0x00000040
    #define FEATURE_FLAG_SETTABLE_WHILE_STREAMING 0x00000080
    #define FEATURE_FLAG_PERSISTABLE    0x00000100  /* The feature will be saved with PxLSaveSettings */
    #define FEATURE_FLAG_EMULATION      0x00000200  /* The feature is implemented in the API, not the camera */
    #define FEATURE_FLAG_VOLATILE       0x00000400  /* The features (settable) value or limits, may change as the result of changing some other feature.  See help file for details on feature interaction */
    ## Exactly one of these 'mode' bits should be set with each feature set operation
    #define FEATURE_FLAG_MODE_BITS (FEATURE_FLAG_MANUAL | FEATURE_FLAG_AUTO | FEATURE_FLAG_ONEPUSH | FEATURE_FLAG_OFF)

    # =========================================================================
    class FRAME_DESC(C.Structure):
        """ The 524 byte size structure passed to the GetNextFrame function
        that is populated with camera settings and frame information.
        """
        PXL_MAX_STROBES = 16
        PXL_MAX_KNEE_POINTS = 4
        _fields_ = [
            ("uSize", C.c_uint),
            ("fFrameTime", C.c_float),
            ("uFrameNumber", C.c_uint),
            ("fBrightnessValue", C.c_float),
            ("fAutoExposureValue", C.c_float),
            ("fSharpnessValue", C.c_float),
            ("fWhiteBalanceValue", C.c_float),
            ("fHueValue", C.c_float),
            ("fSaturationValue", C.c_float),
            ("fGammaValue", C.c_float),
            ("fShutterValue", C.c_float),
            ("fGainValue", C.c_float),
            ("fIrisValue", C.c_float),
            ("fFocusValue", C.c_float),
            ("fTemperatureValue", C.c_float),
            ("fTriggerMode", C.c_float),
            ("fTriggerType", C.c_float),
            ("fTriggerPolarity", C.c_float),
            ("fTriggerDelay", C.c_float),
            ("fTriggerParameter", C.c_float),
            ("fZoomValue", C.c_float),
            ("fPanValue", C.c_float),
            ("fTiltValue", C.c_float),
            ("fOpticalFilterValue", C.c_float),
            ("fGPIOMode", C.c_float * PXL_MAX_STROBES),
            ("fGPIOPolarity", C.c_float * PXL_MAX_STROBES),
            ("fGPIOParameter1", C.c_float * PXL_MAX_STROBES),
            ("fGPIOParameter2", C.c_float * PXL_MAX_STROBES),
            ("fGPIOParameter3", C.c_float * PXL_MAX_STROBES),
            ("fFrameRateValue", C.c_float),
            ("fRoiLeft", C.c_float),
            ("fRoiTop", C.c_float),
            ("fRoiWidth", C.c_float),
            ("fRoiHeight", C.c_float),
            ("fFlipHorizontal", C.c_float),
            ("fFlipVertical", C.c_float),
            ("fDecimationValue", C.c_float),
            ("fPixelFormatValue", C.c_float),
            ("ExtendedShutterKneePoint", C.c_float * PXL_MAX_KNEE_POINTS),
            ("fAutoROILeft", C.c_float),
            ("fAutoROITop", C.c_float),
            ("fAutoROIWidth", C.c_float),
            ("fAutoROIHeight", C.c_float),
            ("fDecimationModeValue", C.c_float),
            ("fWhiteShadingRedGain", C.c_float),
            ("fWhiteShadingGreenGain", C.c_float),
            ("fWhiteShadingBlueGain", C.c_float),
            ("fRotateValue", C.c_float),
            ("fImagerClkDivisorValue", C.c_float),
            ("fTriggerWithControlledLightValue", C.c_float),
            ("fMaxPixelSizeValue", C.c_float),
            ("fTriggerNumberValue", C.c_float),
            ("fImageProcessingValue", C.c_uint),
        ]

        def todict(self):
            """ TODO: implemented """
            result = {}
            return result

    # =========================================================================
    class ERROR_REPORT(C.Structure):
        """ This class is used as input to the GetErrorReport
        function. Wrapper class around the PxlAPi40.dll ERROR_REPORT
        structure. """
        _fields_ = [
            ("uReturnCode", C.c_int),
            ("strFunctionName", C.c_char * 32),
            ("strReturnCode", C.c_char * 32),
            ("strReport", C.c_char * 256),
        ]
        def __str__(self):
            msg = ''
            msg += ' errorCode: 0x%08x %s,' % (int(self.uReturnCode), self.strReturnCode)
            msg += ' errorDesc: %s,' % self.strReport
            msg += ' function: %s' % self.strFunctionName
            return msg


    # -------------------------------------------------------------------------
    def __init__(self, useReturnCodes=False, libPath = DLL_PATH):
        self.__lib = C.windll.LoadLibrary(libPath)
        self.__libPath = libPath
        self._useReturnCodes = useReturnCodes
        self._frameDesc = self.FRAME_DESC()
        #self._lib = self.__lib# for debugging

    # -------------------------------------------------------------------------
    @property
    def lib(self):
        return self.__lib

    # -------------------------------------------------------------------------
    def __str__(self):
        return "lib = {0}, libPath = {1}".format(self.__lib, self.__libPath)

    __repr__ = __str__

    # -------------------------------------------------------------------------
    def wrap_return_code(func):
        """
        Decorator that helps convert the PxLapi methods to either return error
        codes or raise exception on error codes.
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):

            result = func(self, *args, **kwargs)
            if self._useReturnCodes:
                return result

            toReturn = None # default to methos returns nothing
            if isinstance(result, tuple) or isinstance(result, list):
                if len(result) > 1:
                    toReturn = result[1]
                rc = result[0]
            else:
                rc = result

            if rc != 0:
                if len(args) > 0 and isinstance(args[0], C.c_void_p):
                    hCamera = args[0]
                else:
                    hCamera = None

                # must call unwrapped method, else
                #    'ERROR_REPORT' object is not iterable
                # is thrown. I don't yet understand this.
                (rc, report) = self._GetErrorReport(hCamera)
                ex = PxLerror(self, rc, hCamera, '', report)
                raise ex
            else:
                return toReturn

        return wrapper

    # -------------------------------------------------------------------------
    def _GetErrorReport(self, hCamera):
        """ Retrieve the error report without using the wrapped API method. This
        is to ensure the exception::
            'ERROR_REPORT' object is not iterable
        is not thrown.
        Calling a wrapped function from within the wrap_return_code.wrapper
        function is not allowed.
        """
        report = self.ERROR_REPORT()
        rc = self.__lib.PxLGetErrorReport(hCamera, C.byref(report))
        return (rc, report)

    # -------------------------------------------------------------------------
    @wrap_return_code
    def GetErrorReport(self, hCamera):
        """ Get the last error description report from the camera. This should
        be called each time a PxLapi function is called and the return code (rc)
        is a error code.

        returns: class:`PxLapi.ERROR_REPORT` type
        """
        return self._GetErrorReport(hCamera)

    # -------------------------------------------------------------------------
    @wrap_return_code
    def GetNumberCameras(self):
        """ Retrieves the list of cameras connected to the network (or computer)
        and returns the list of serial numbers. The number of cameras can be
        determine from the returned list length.
        """
        numCameras = C.c_ulong(0)
        rc = self.__lib.PxLGetNumberCameras(None, C.byref(numCameras))
        if rc != 0:
            return (rc, [])

        serialNumbers = (C.c_long*numCameras.value)()
        rc = self.__lib.PxLGetNumberCameras(C.byref(serialNumbers), C.byref(numCameras))
        return (rc, [int(v) for v in serialNumbers])


    # -------------------------------------------------------------------------
    @wrap_return_code
    def Initialize(self, serialNumber=0):
        """ Initialize communication with the camera. This function must be
        called before any other driver functions.
        """
        hCamera = W.HANDLE(0)
        rc = self.__lib.PxLInitialize(C.c_uint32(serialNumber), C.POINTER(W.HANDLE)(hCamera))
        if (0 == rc):
            return (rc, hCamera)
        return (rc, 0)

    # -------------------------------------------------------------------------
    @wrap_return_code
    def Uninitialize(self, hCamera):
        """ Close communcication with the camera. This function must be the
        last call made to the underlying driver.
        """
        if hCamera:
            rc = self.__lib.PxLUninitialize(hCamera)
        else:
            rc = 0
        return rc

    # -------------------------------------------------------------------------
    @wrap_return_code
    def SetStreamState(self, hCamera, state):
        """ Set the stream state: STOP_STREAM, PAUSE_STREAM, START_STREAM.
        Some API calls require the stream state to be stopped before setting
        a feature, uscah as ROI.
        """
        rc = self.__lib.PxLSetStreamState(hCamera, state)
        return rc

    # -------------------------------------------------------------------------
    @wrap_return_code
    def GetNextFrame(self, hCamera, w, h):
        """ Retrieve the next frame when the camera is in "streaming" mode.
        Make sure SetStreamState(hCamera, PxLapi.START_STREAM) has been called
        before calling this function.

        TODO: in the future, the width and hieght arguments may not be needed
        since this information can be retrieved by making a call to:
        GetFeature(hCamera, PxLapi.FEATURE_ROI, 4)
        """
        w = int(w)
        h = int(h)

        if HAS_NUMPY:
            c_void_p = C.POINTER(C.c_void_p)
            data = numpy.zeros((h, w), dtype='uint8')
            data_p = data.ctypes.data_as(c_void_p)
        else:
            # make the ctypes string buffer act like a numpy.array
            data = C.create_string_buffer('\0', (h*w))
            setattr(data, 'shape', (h, w))
            setattr(data, 'tostring', lambda : data.raw)
            data_p = C.byref(data)

        rc = self.__lib.PxLGetNextFrame(hCamera, w * h, data_p, C.byref(self._frameDesc))
        return (rc, data)

    # -------------------------------------------------------------------------
    @wrap_return_code
    def GetFeature(self, hCamera, feature, numParams=1):
        """ Retrieve a camera setting using the feature id definitions. """
        value = (C.c_float*numParams)()
        flags = C.c_ulong(0)
        paramLen = C.c_ulong(numParams)
        rc = self.__lib.PxLGetFeature(hCamera, feature, C.byref(flags), C.byref(paramLen), C.byref(value))
        if rc != 0:
            return (rc, 0)
        else:
            if numParams == 1:
                return (rc, value[0])
            else:
                return (rc, [float(v) for v in value])


    # -------------------------------------------------------------------------
    @wrap_return_code
    def SetFeature(self, hCamera, feature, value):
        """ Set a camera setting using a feature id definition. """
        flags = 0
        if isinstance(value, list) or isinstance(value, tuple):
            numParams = len(value)
            val = (C.c_float*numParams)(*value)
        else:
            numParams = 1
            val = C.c_float(value)
        rc = self.__lib.PxLSetFeature(hCamera, feature, flags, numParams, C.byref(val))
        return rc



# =============================================================================
class PxLerror(Exception):
    """ PixeLINK API exception """

    # -------------------------------------------------------------------------
    def __init__(self, api, errorCode, hCamera = None, extraInfo = '', report=None):
        Exception.__init__(self, '')

        if report is None:
            (_rc, report) = api.GetErrorReport(hCamera)

        self.errorCode = errorCode
        self.hCamera = hCamera
        self.uReturnCode = report.uReturnCode
        self.strFunctionName = report.strFunctionName
        self.strReturnCode = report.strReturnCode
        self.strReport = report.strReport
        self.extraInfo = extraInfo

    # -------------------------------------------------------------------------
    def __str__(self):
        if self.hCamera:
            camAddress = self.hCamera.value
        else:
            camAddress = 0
        msg = 'PixeLINK API error - '
        msg += self.extraInfo
        msg += ' hCamera: 0x%08x,' % camAddress
        msg += ' errorCode: 0x%08x %s,' % (int(self.errorCode), self.strReturnCode)
        msg += ' errorDesc: %s,' % self.strReport
        msg += ' function: %s' % self.strFunctionName
        return msg

    __repr__ = __str__




# =============================================================================
class PixeLINK(Camera):
    """ High level interface to the PixeLINK camera. """

    # --------------------------------------------------------------------------
    def __init__(self, logid="CAM", startStreaming=True):
        super(PixeLINK, self).__init__(logid)
        self._mutex = threading.Lock()
        self._api = PxLapi()
        self._hCamera = self._api.Initialize(0)
        self._streaming = False
        self._roi = self.get_property_value(PxLapi.FEATURE_ROI)
        if startStreaming:
            self.streaming = True

    # --------------------------------------------------------------------------
    def __del__(self):
        # incase the user forgot to call the close method.
        self.close()

    # --------------------------------------------------------------------------
    def _get_frame(self):
        self._mutex.acquire()
        try:
            r = self._roi
            data = self._api.GetNextFrame(self._hCamera, r[2], r[3])
            return data
        finally:
            self._mutex.release()

    # --------------------------------------------------------------------------
    @staticmethod
    def get_feature_id(key):
        """ Convert the property key string to a PixeLINK feature id code. """
        if key == 'IntegrationTime':
            featureId = PxLapi.FEATURE_SHUTTER
        elif key == 'ROI':
            featureId = PxLapi.FEATURE_ROI
        else:
            featureId = 0

        return featureId

    # --------------------------------------------------------------------------
    def get_property_value(self, key):
        """ Retrieve the current setting for a feature from the camera. """
        if isinstance(key, str):
            featureId = self.get_feature_id(key)
            if featureId == 0:
                raise RuntimeWarning('Invalid key: %s' % key)
        else:
            featureId = key # must be an PxLapi.FEATURE_* (int or long)

        count = [1, 4][featureId == PxLapi.FEATURE_ROI]

        self._mutex.acquire()
        try:
            return self._api.GetFeature(self._hCamera, featureId, count)
        finally:
            self._mutex.release()

    # --------------------------------------------------------------------------
    def set_property_value(self, key, value):
        """ Send a configuration parameter to the camera. """
        if isinstance(key, str):
            featureId = self.get_feature_id(key)
            if featureId == 0:
                raise RuntimeWarning('Invalid key: %s' % key)
        else:
            featureId = key # must be an PxLapi.FEATURE_* (int or long)

        self._mutex.acquire()
        try:
            self._api.SetFeature(self._hCamera, featureId, value)
        finally:
            self._mutex.release()

    # --------------------------------------------------------------------------
    @property
    def streaming(self):
        return self._streaming

    # --------------------------------------------------------------------------
    @streaming.setter
    def streaming(self, state):
        if isinstance(state, bool):
            # convert to an int type
            state = [PxLapi.STOP_STREAM, PxLapi.START_STREAM][state]

        self._mutex.acquire()
        try:
            self._api.SetStreamState(self._hCamera, state)
            self._streaming = (state == PxLapi.START_STREAM)
        finally:
            self._mutex.release()

    # --------------------------------------------------------------------------
    @property
    def shutter(self):
        return self.get_property_value(PxLapi.FEATURE_SHUTTER)

    # --------------------------------------------------------------------------
    @shutter.setter
    def shutter(self, seconds):
        return self.set_property_value(PxLapi.FEATURE_SHUTTER, seconds)

    # --------------------------------------------------------------------------
    @property
    def roi(self):
        return [int(v) for v in self._roi]

    # --------------------------------------------------------------------------
    @roi.setter
    def roi(self, ltwhTuple):
        """ Setting the region of interest can only occuring if the streaming
        is in a stopped state. Be sure to execute::

             cam.streaming=False

        before setting this property.
        """
        self.set_property_value(PxLapi.FEATURE_ROI, ltwhTuple)
        self._roi = self.get_property_value(PxLapi.FEATURE_ROI)

    # --------------------------------------------------------------------------
    def close(self):
        """ Stop streaming and close communication with the camera. """

        # disallow close more than once check.
        if self._hCamera is None:
            return

        self._mutex.acquire()
        try:
            self._api.SetStreamState(self._hCamera, PxLapi.STOP_STREAM)
            self._api.Uninitialize(self._hCamera)
            self._hCamera = None
            self._api = None # no further calls are allowed to this class
        finally:
            self._mutex.release()


# =============================================================================
def Save(fname, data):

    if os.path.exists(fname):
        os.remove(fname)

    name = fname.lower()
    if name.endswith('.bmp'):
        SaveAsBMP(fname, data)

    elif name.endswith('.fits') or name.endswith('.fit'):
        SaveAsFits(fname, data)

# =============================================================================
def SaveAsBMP(fname, data):
    import struct

    (h, w) = data.shape
    rawBytes = data.tostring()
    info = {'width': w, 'height': h, 'colordepth': 8}

    #Here is a minimal dictionary with header values.
    #Of importance is the offset, headerlength, width,
    #height and colordepth.
    #Edit the width and height to your liking.
    #These header values are described in the bmp format spec.
    #You can find it on the internet. This is for a Windows
    #Version 3 DIB header.

    headerEntries = (
        ('<B', 66, 'mn1'),
        ('<B', 77, 'mn2'),
        ('<L', 0,  'filesize'),
        ('<H', 0,  'undef1'),
        ('<H', 0,  'undef2'),
        ('<L', 54, 'offset'),
        ('<L', 40, 'headerlength'),
        ('<L', 0,  'width'),
        ('<L', 0,  'height'),
        ('<H', 0,  'colorplanes'),
        ('<H', 24, 'colordepth'),
        ('<L', 0,  'compression'),
        ('<L', 0,  'imagesize'),
        ('<L', 0,  'res_hor'),
        ('<L', 0,  'res_vert'),
        ('<L', 0,  'palette'),
        ('<L', 0,  'importantcolors'),
    )
    header = ''
    for entry in headerEntries:
        frmt, val, key = entry
        if key in info:
            val = info[key]
        header += struct.pack(frmt, val)

    outfile = open(fname, 'wb')
    outfile.write(header + rawBytes)
    outfile.close()

# =============================================================================
def SaveAsFits(fname, data, header=None, dtype=None):

    import pyfits

    if dtype is not None:
        data = data.astype(dtype)
    fits = pyfits.PrimaryHDU(data)

    if header:
        for entry in header:
            try:
                fits.header.update(entry.key, entry.value, entry.desc)
            except ValueError as e:
                s = "Failed to write fits header entry: "
                s += entry.key + "=" + str(entry.value) + ";" + str(e)
                print(s)

    fits.writeto(fname)

# =============================================================================
def TestCameraAPI():
    print("Running tests on the Camera API...")
    api = PxLapi()
    hCamera = None
    try:
        serialNums =  api.GetNumberCameras()
        print(serialNums)

        hCamera = api.Initialize()

        # test integration time setting
        print("shutter", api.GetFeature(hCamera, PxLapi.FEATURE_SHUTTER))
        api.SetFeature(hCamera, PxLapi.FEATURE_SHUTTER, 1.5)
        print("shutter", api.GetFeature(hCamera, PxLapi.FEATURE_SHUTTER))
        report = api.GetErrorReport(hCamera)
        print("report", str(report))

        # test roi functionality
        roi = api.GetFeature(hCamera, PxLapi.FEATURE_ROI, 4)
        w = roi[2]
        h = roi[3]
        print("roi", api.GetFeature(hCamera, PxLapi.FEATURE_ROI, 4))
        try:
            api.SetFeature(hCamera, PxLapi.FEATURE_ROI, [0, 0, 1000, 1000])
        except PxLerror as ex:
            print(str(ex))
        print("roi", api.GetFeature(hCamera, PxLapi.FEATURE_ROI, 4))

        # test frame grabbing
        api.SetStreamState(hCamera, PxLapi.START_STREAM)
        try:
            for i in range(1):
                data = api.GetNextFrame(hCamera, w, h)
                print("grabbed frame #%02d" %i, data.shape)
        except PxLerror as ex:
            print(ex)
        api.SetStreamState(hCamera, PxLapi.STOP_STREAM)

    except PxLerror as ex:
        print(str(ex))

    finally:
        api.Uninitialize(hCamera)

# =============================================================================
def TestCameraClass():
    print("Running tests on the Camera class...")
    cam = PixeLINK()
    shutter0 = cam.shutter
    print("shutter0", shutter0)
    roi0 = cam.roi
    print("roi0", roi0)

    cam.shutter = 1e-3
    print("shutter", cam.shutter)

    # this will fail because the camera is streaming. Catch the error.
    try:
        cam.roi = [0, 0, 1000, 1000]
    except PxLerror as ex:
        print(str(ex))

    # stop the streaming and try to set to ROI again
    if cam.streaming:
        cam.streaming = False
        print("streaming", cam.streaming)

    # now the setting of the ROI will be set without errors.
    try:
        cam.roi = [0, 0, 1000, 1000]
        print("roi", cam.roi)
    except PxLerror as ex:
        print(str(ex))

    # test frame grabbing
    cam.streaming = True
    data = cam.grab()
    print("data.shape", data.shape)
    cam.streaming = False

    #reset features to original values
    cam.roi = roi0
    cam.shutter = shutter0
    cam.close()

    Save('test.bmp', data)

# =============================================================================
def RunTests():
    TestCameraAPI()
    TestCameraClass()

# =============================================================================
if __name__ == "__main__":
    RunTests()

