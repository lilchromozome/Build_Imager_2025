
#!/usr/bin/env python

"""
camera.py: Python wrapper for Thorlab DCx camera SDK.
Adapted from:
https://github.com/manoharan-lab/camera-controller/blob/master/thorcam.py
https://github.com/ddietze/Py-Hardware-Support
"""
__author__      = "Grace J. Gang"

# TODO: singleton counts and exit failure defeats purpose of each other...
# exiting kernel invokes __del__, error if camera already closed

from ctypes import *
import time
import numpy as np
import warnings
from helper import check_minmax

IS_CM_MONO8 = 6
IS_CM_MONO10 = 34

IS_SET_TRIG_SOFTWARE          =    0x0008
IS_SET_TRIGGER_CONTINUOUS     =    0x1000
IS_SET_TRIGGER_SOFTWARE       =    (IS_SET_TRIGGER_CONTINUOUS | IS_SET_TRIG_SOFTWARE)

IS_WAIT                      =       0x0001
IS_DONT_WAIT                 =       0x0000

IS_EXPOSURE_CMD_GET_CAPS                        = 1
IS_EXPOSURE_CMD_GET_EXPOSURE_DEFAULT            = 2
IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN          = 3
IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX          = 4
IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC          = 5
IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE              = 6
IS_EXPOSURE_CMD_GET_EXPOSURE                    = 7
IS_EXPOSURE_CMD_GET_FINE_INCREMENT_RANGE_MIN    = 8
IS_EXPOSURE_CMD_GET_FINE_INCREMENT_RANGE_MAX    = 9
IS_EXPOSURE_CMD_GET_FINE_INCREMENT_RANGE_INC    = 10
IS_EXPOSURE_CMD_GET_FINE_INCREMENT_RANGE        = 11
IS_EXPOSURE_CMD_SET_EXPOSURE                    = 12

IS_AOI_IMAGE_SET_AOI        =        0x0001
IS_AOI_IMAGE_GET_AOI        =        0x0002

IS_PIXELCLOCK_CMD_GET_NUMBER    = 1
IS_PIXELCLOCK_CMD_GET_LIST      = 2
IS_PIXELCLOCK_CMD_GET_RANGE     = 3
IS_PIXELCLOCK_CMD_GET_DEFAULT   = 4
IS_PIXELCLOCK_CMD_GET           = 5
IS_PIXELCLOCK_CMD_SET           = 6

IS_GET_FRAMERATE              =      0x8000
IS_GET_DEFAULT_FRAMERATE      =      0x8001

IS_CAPTURE_STATUS           =      0x0003

IS_NO_SUCCESS                 =        -1  #  function call failed
IS_SUCCESS                    =        0   #  function call succeeded

# Error handling
class uc480Error(Exception):
    """uc480 exception class handling errors related to communication with the uc480 camera.
    """
    def __init__(self, error, mess, fname=""):
        """Constructor.

        :param int error: Error code.
        :param str mess: Text message associated with the error.
        :param str fname: Name of function that caused the error (optional).
        """
        self.error = error
        self.mess = mess
        self.fname = fname

    def __str__(self):
        if self.fname != "":
            return self.mess + ' in function ' + self.fname
            # return ('UEYECamera:{0:}, Error code: {1:}: {2:}'.format( function, pErr.value, ppcErr.value[1]))
        else:
            return self.mess


def assrt(retVal, fname=""):
    if not (retVal == IS_SUCCESS):
        raise uc480Error(retVal, "Error: uc480 function call failed! Error code = " + str(retVal), fname)
    return retVal


class IS_RECT(Structure):
    _fields_ = [("s32X", c_int),
                ("s32Y", c_int),
                ("s32Width", c_int),
                ("s32Height", c_int)]

class IS_POINT_2D(Structure):
    _fields_ = [("s32X", c_int),
                ("s32Y", c_int)]

class IS_SIZE_2D(Structure):
    _fields_ = [("s32Width", c_int),
                ("s32Height", c_int)]

class Camera:
    count = 0
    def __init__(self):
        if Camera.count > 0:
            raise Exception('An object has already been initialized')
        else:
            # camera properties
            self.hid = None
            self.meminfo = None   #replaces imagebufferpointer and imagebufferpid
            self.pixelclock = 0
            self.allowedpixelclock = 0
            self.exposure = None
            self.roi_shape = None
            self.roi_pos = None
            self.exposurerange = None
            self.framerate = 0
            self.frameraterange = 0
            self.pausetime = 0
            self.bit_depth = None

            # dll
            self._lib = None
            self.connect_to_library()
            Camera.count += 1

    # connect to uc480 DLL library
    def connect_to_library(self, library=None):
        print("Load uc480 library..")
        if library is None:
            try:
                self._lib = windll.LoadLibrary("uc480_64.dll")
            except:
                print("ThorCam drivers not available.")
        else:
            self._lib = windll.LoadLibrary(library)


    def open(self,  roi_shape=(1280, 1024), roi_pos=(0,0), exposure=10., framerate=1.0):
        self.roi_shape = roi_shape
        self.roi_pos = roi_pos

        # is_InitCamera = self._lib.is_InitCamera
        # is_InitCamera.argtypes = [POINTER(c_int)]
        # self.hid = c_int(0)
        # out = is_InitCamera(byref(self.hid))

        self.hid = c_int(0)
        self.call('is_InitCamera', byref(self.hid), None)

        self.set_color_mode()
        self.set_pixel_clock()
        _ = self.get_framerate_range()
        _ = self.get_exposure_range()
        self.set_roi(self.roi_shape, self.roi_pos)
        self.set_framerate(framerate)
        self.set_exposure(exposure)

        self.initialize_memory()
        print('ThorCam opened successfully.')


    def close(self):
        Camera.count = 0
        if self.meminfo != None:
            self.clear_image()
        if self.hid != None:
            self.call('is_ExitCamera', self.hid, argtypes=[c_int])
            print('ThorCam closed successfully.')
        else:
            print('Invalid camera handle.')


    def call(self, function, *args, argtypes=None, ):
        """Wrapper around library function calls to allow the user to call any library function.

        :param str function: Name of the library function to be executed.
        :param mixed args: Arguments to pass to the function.
        :raises uc480Error: if function could not be properly executed.
        """
        func = getattr(self._lib, function, None)
        if argtypes is not None:
            func.argtypes = argtypes
        assrt(func(*args), function)
        # if out == 0:
        #     return out
        # else:
        #     pErr = c_int(out)
        #     ppcErr = c_char_p()
        #     is_GetError = self._lib.is_GetError
        #     is_GetError.argtypes = [c_int, c_int,  POINTER(c_char_p)]
        #     out_ = is_GetError(self.hid, pErr, byref(ppcErr))
        #     if out_ == 0:
        #         raise uc480Error(pErr.value, ppcErr.value[1], function)
        #     else:
        #         raise uc480Error(pErr.value, ppcErr.value[1], 'is_GetError')
            # print("WARNING: Function {} does not exist in this library version..".format(function))


    def get_image(self, buffer_number=None):
        im = np.frombuffer(self.meminfo[0], c_uint16).reshape(self.roi_shape[1], self.roi_shape[0])
        return im


    def clear_image(self,):
        self._lib.is_FreeImageMem(self.hid, self.meminfo[0], self.meminfo[1])
        # self.call('is_FreeImageMem', self.hid, self.meminfo[0], self.meminfo[1])


    def initialize_memory(self):
        if self.meminfo != None:
            self.clear_image()

        xdim = self.roi_shape[0]
        ydim = self.roi_shape[1]
        imagesize = xdim * ydim
        memid = c_int(0)

        if self.bit_depth == 16:
            c_buf = (c_uint16 * imagesize)(0)
        elif self.bit_depth == 8:
            c_buf = (c_uint8 * imagesize)(0)

        self.call('is_SetAllocatedImageMem', self.hid, xdim, ydim, self.bit_depth, c_buf, byref(memid))
        self.call('is_SetImageMem', self.hid, c_buf, memid)
        self.meminfo = [c_buf, memid]


    def capture(self):
        self.call('is_FreezeVideo', self.hid, IS_WAIT)
        im = self.get_image()
        return im


    def set_exposure(self, exposure):
        exposure = check_minmax(exposure, self.exposurerange[0], self.exposurerange[1])
        #exposure should be given in ms
        exposure_c = c_double(exposure)
        self.call('is_Exposure', self.hid, IS_EXPOSURE_CMD_SET_EXPOSURE , exposure_c, sizeof(exposure_c),
            argtypes=[c_int, c_uint, POINTER(c_double), c_uint])
        self.exposure = exposure_c.value


    def get_exposure(self):
        #exposure should be given in ms
        exposure_c = c_double(0)
        self.call('is_Exposure', self.hid, IS_EXPOSURE_CMD_GET_EXPOSURE , exposure_c, sizeof(exposure_c),
            argtypes=[c_int, c_uint, POINTER(c_double), c_uint])
        self.exposure = exposure_c.value
        return self.exposure


    # Returns min, max and inc, in that order
    def get_exposure_range(self, ):
        c_range = (c_double * 3)(0)
        self.call('is_Exposure', self.hid, IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE, c_range, sizeof(c_range),
            argtypes=[c_int, c_uint, POINTER(c_double), c_uint])
        self.exposurerange = np.frombuffer(c_range, c_double)
        return self.exposurerange


    def set_framerate(self, framerate):
        framerate = check_minmax(framerate, self.frameraterange[0], self.frameraterange[1])
        framerate_c = c_double(framerate)
        newfps = c_double(0)
        self.call('is_SetFrameRate', self.hid, framerate_c, byref(newfps),
            argtypes=[c_int, c_double, POINTER(c_double)])
        # must reset exposure after setting framerate
        self.get_exposure_range()
        self.get_exposure()
        self.framerate = newfps.value


    def get_framerate(self, ):
        return self.framerate


    # only depend on pixel clock.
    def get_framerate_range(self,):
        min_c = c_double(0)
        max_c = c_double(0)
        int_c = c_double(0)
        self.call('is_GetFrameTimeRange', self.hid, min_c, max_c, int_c,
            argtypes=[c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double)])
        self.frameraterange = [1 / max_c.value, 1 / min_c.value ]
        return self.frameraterange


    def set_roi(self, roi_shape, roi_pos):
        roi_c = IS_RECT(roi_pos[0], roi_pos[1], roi_shape[0], roi_shape[1])
        out = self.call('is_AOI', self.hid, IS_AOI_IMAGE_SET_AOI, byref(roi_c), sizeof(roi_c),
            argtypes=[c_int, c_uint, POINTER(IS_RECT), c_uint])
        self.call('is_AOI', self.hid, IS_AOI_IMAGE_GET_AOI, byref(roi_c), sizeof(roi_c),
            argtypes=[c_int, c_uint, POINTER(IS_RECT), c_uint])
        self.roi_shape = [roi_c.s32Width, roi_c.s32Height]
        self.roi_pos = [roi_c.s32X, roi_c.s32Y]
        self.initialize_memory()


    def set_color_mode(self, mode='mono10'):
        if  mode == 'mono10':
            self.call('is_SetColorMode', self.hid, IS_CM_MONO10)
            self.bit_depth = 16
        elif mode == 'mono8':
            self.call('is_SetColorMode', self.hid, IS_CM_MONO8)
            self.bit_depth = 8


    def set_pixel_clock(self, default_pc=24):
        pixelclock_c = c_uint(default_pc)
        self.call('is_PixelClock', self.hid, IS_PIXELCLOCK_CMD_SET, byref(pixelclock_c), sizeof(pixelclock_c),
            argtypes=[c_int, c_uint, POINTER(c_uint), c_uint])
        self.pixelclock = pixelclock_c.value


    def get_pixel_clock(self, ):
        pixelclock_c = c_uint(0)
        self.call('is_PixelClock', self.hid,  IS_PIXELCLOCK_CMD_GET, byref(pixelclock_c), sizeof(pixelclock_c),
            argtypes=[c_int, c_uint, POINTER(c_uint), c_uint])
        self.pixelclock = pixelclock_c.value
        return self.pixelclock


    def get_allowed_pixel_clock(self, ):
        num_c = c_uint(0)
        self.call('is_PixelClock', self.hid,  IS_PIXELCLOCK_CMD_GET_NUMBER, num_c, sizeof(num_c),
            argtypes=[c_int, c_uint, POINTER(c_uint), c_uint])
        pclist_c = (c_uint * num_c.value)(0)
        self.call('is_PixelClock', self.hid,  IS_PIXELCLOCK_CMD_GET_LIST, pclist_c, sizeof(pclist_c))
        self.allowedpixelclock = np.frombuffer(pclist_c, c_uint)
        return num_c.value, self.allowedpixelclock


    def get_properties(self,):
        print('Exposure',  '\t', '{0:.2f}'.format(self.exposure), ' ms')
        print('Exposure Range',  '\t', '[{0:.2f}, {1:.2f}]'.format(self.exposurerange[0], self.exposurerange[1]), ' ms')
        print('Framerate',  '\t', '{0:.1f}'.format(self.framerate), )
        print('Frame Range',  '\t', '[{0:.1f}, {1:.1f}]'.format(self.frameraterange[0], self.frameraterange[1]))
        print('Pixel Clock', '\t', self.pixelclock, 'MHz')


    def __del__(self):
        self.close()


if __name__ == "__main__":

    import pylab as pl
    c = Camera()
    c.open()
    # c.initialize_memory()
    im = c.capture()
    pl.plot(im)
    c.close()
    pl.show()
