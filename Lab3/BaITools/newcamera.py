
#!/usr/bin/env python

"""
camera.py: Python wrapper for Thorlab DCx camera SDK.
Adapted from:
https://github.com/manoharan-lab/camera-controller/blob/master/thorcam.py
https://github.com/ddietze/Py-Hardware-Support
"""
__author__      = "Grace J. Gang"

# Need to implement., from matlab:
# get framerate not working properly?
# IsVideoFinish??
# callliberrcheck

# Look up Python equivalent of MatLab overloading
# not sure if byref is necessary - probably not
# add error checking

# assumes uc480_64.dll added to system path. If not can specify path

from ctypes import *
import time
import numpy as np
# from uc480_h import *

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


class CameraOpenError(Exception):
    def __init__(self, mesg):
        self.mesg = mesg
    def __str__(self):
        return self.mesg

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

    def __init__(self):
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
        self.open()
        self.initialize_memory()

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


    def open(self,  roi_shape=(1280, 1024), roi_pos=(0,0), exposure=0.01, framerate=1.0):
        self.roi_shape = roi_shape
        self.roi_pos = roi_pos

        is_InitCamera = self._lib.is_InitCamera
        is_InitCamera.argtypes = [POINTER(c_int)]
        self.hid = c_int(0)
        i = is_InitCamera(byref(self.hid))

        if i == 0:
            print("ThorCam opened successfully.")

            self.set_color_mode()
            self.set_pixel_clock()
            self.set_roi_shape(self.roi_shape)
            self.set_roi_pos(self.roi_pos)
            self.set_framerate(framerate)
            self.set_exposure(exposure)
            _ = self.get_framerate_range()
            _ = self.get_exposure_range()

        else:
            raise CameraOpenError("Opening the ThorCam failed with error code "+str(i))


    def close(self):
        if self.meminfo != None:
            self.clear_image()
        if self.hid != None:
            # self.stop_live_capture()
            i = self._lib.is_ExitCamera(self.hid)
            if i == 0:
                print("ThorCam closed successfully.")
            else:
                print("Closing ThorCam failed with error code "+str(i))
        else:
            return


    def get_image(self, buffer_number=None):
        im = np.frombuffer(self.meminfo[0], c_uint16).reshape(self.roi_shape[1], self.roi_shape[0])
        return im


    def clear_image(self,):
        self._lib.is_FreeImageMem(self.hid, self.meminfo[0], self.meminfo[1])


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
        self._lib.is_SetAllocatedImageMem(self.hid, xdim, ydim, self.bit_depth, c_buf, byref(memid))
        self._lib.is_SetImageMem(self.hid, c_buf, memid)
        self.meminfo = [c_buf, memid]


    def capture(self):
        self._lib.is_FreezeVideo(self.hid, IS_WAIT)
        im = self.get_image()
        return im


    def set_exposure(self, exposure):
        #exposure should be given in ms
        exposure_c = c_double(exposure)
        is_Exposure = self._lib.is_Exposure
        is_Exposure.argtypes = [c_int, c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.hid, IS_EXPOSURE_CMD_SET_EXPOSURE , exposure_c, sizeof(exposure_c)) #12 is for setting exposure
        self.exposure = exposure_c.value


    def get_exposure(self):
        #exposure should be given in ms
        exposure_c = c_double(0)
        is_Exposure = self._lib.is_Exposure
        is_Exposure.argtypes = [c_int, c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.hid, IS_EXPOSURE_CMD_GET_EXPOSURE, exposure_c, sizeof(exposure_c))
        return exposure_c.value


    # Returns min, max and inc, in that order
    def get_exposure_range(self, ):
        c_range = (c_double * 3)(0)
        is_Exposure = self._lib.is_Exposure
        is_Exposure.argtypes = [c_int, c_uint, POINTER(c_double), c_uint]
        is_Exposure(self.hid, IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE, c_range, sizeof(c_range))
        self.exposurerange = np.frombuffer(c_range, c_double)
        return self.exposurerange


    def set_framerate(self, framerate):
        #must reset exposure after setting framerate
        framerate_c = c_double(framerate)
        newfps = c_double(0)
        is_SetFrameRate = self._lib.is_SetFrameRate
        is_SetFrameRate.argtypes = [c_int, c_double, POINTER(c_double)]
        is_SetFrameRate(self.hid, framerate_c, byref(newfps))
        self.framerate = newfps.value


    # not sure why 2 functions in SDK is not returning what's expected...
    def get_framerate(self, ):
        # # for use with is_CaptureVideo??? gives 0s....
        # framerate_c = c_double(framerate)
        # is_GetFramesPerSecond = self._lib.is_GetFramesPerSecond
        # is_GetFramesPerSecond.argtypes = [c_int, POINTER(c_double)]
        # is_GetFramesPerSecond(self.hid, byref(framerate_c))
        # return framerate_c.value

        # # always returns default??
        # fps = c_double(1)
        # is_SetFrameRate = c._lib.is_SetFrameRate
        # is_SetFrameRate.argtypes = [c_int, c_uint, POINTER(c_double)]
        # is_SetFrameRate(c.hid, IS_GET_FRAMERATE, byref(fps))
        # return fps.value

        return self.framerate

    # only depend on pixel clock.
    def get_framerate_range(self,):
        min_c = c_double(0)
        max_c = c_double(0)
        int_c = c_double(0)

        is_SetFrameRate = self._lib.is_GetFrameTimeRange
        is_SetFrameRate.argtypes = [c_int, POINTER(c_double), POINTER(c_double), POINTER(c_double)]
        is_SetFrameRate(self.hid, min_c, max_c, int_c)
        self.frameraterange = [1 / max_c.value, 1 / min_c.value ]
        return self.frameraterange


    def set_roi(self, roi_shape, roi_pos):
        roi_c = IS_RECT(roi_pos[0], roi_pos[1], roi_shape[0], roi_shape[1])
        is_AOI = self._lib.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_RECT), c_uint]
        out = is_AOI(self.hid, IS_AOI_IMAGE_SET_AOI, byref(roi_c), sizeof(roi_c))
        is_AOI(self.hid, IS_AOI_IMAGE_GET_AOI, byref(roi_c), sizeof(roi_c))
        self.roi_shape = [roi_c.s32Width, roi_c.s32Height]
        self.roi_pos = [roi_c.s32X, roi_c.s32Y]

        if out == 0:
            print("ThorCam ROI set successfully.")
            self.initialize_memory()
        else:
            print("Set ThorCam ROI failed with error code "+str(i))


    def set_roi_shape(self, roi_shape):
        AOI_size = IS_SIZE_2D(roi_shape[0], roi_shape[1]) #Width and Height

        is_AOI = self._lib.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_SIZE_2D), c_uint]
        i = is_AOI(self.hid, 5, byref(AOI_size), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.hid, 6, byref(AOI_size), 8 )#6 for getting size, 4 for getting position
        self.roi_shape = [AOI_size.s32Width, AOI_size.s32Height]

        if i == 0:
            print("ThorCam ROI size set successfully.")
            self.initialize_memory()
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))


    def set_roi_pos(self, roi_pos):
        AOI_pos = IS_POINT_2D(roi_pos[0], roi_pos[1]) #Width and Height

        is_AOI = self._lib.is_AOI
        is_AOI.argtypes = [c_int, c_uint, POINTER(IS_POINT_2D), c_uint]
        i = is_AOI(self.hid, 3, byref(AOI_pos), 8 )#5 for setting size, 3 for setting position
        is_AOI(self.hid, 4, byref(AOI_pos), 8 )#6 for getting size, 4 for getting position
        self.roi_pos = [AOI_pos.s32X, AOI_pos.s32Y]

        if i == 0:
            print("ThorCam ROI position set successfully.")
        else:
            print("Set ThorCam ROI size failed with error code "+str(i))


    def set_color_mode(self, mode='mono10'):
        if  mode == 'mono10':
            self._lib.is_SetColorMode(self.hid, IS_CM_MONO10) # monochrome 10 bit.
            self.bit_depth = 16
        elif mode == 'mono8':
            self._lib.is_SetColorMode(self.hid, IS_CM_MONO8) # monochrome 8 bit.
            self.bit_depth = 8


    def set_pixel_clock(self, default_pc=24):
        pixelclock_c = c_uint(default_pc)
        is_PixelClock = self._lib.is_PixelClock
        is_PixelClock.argtypes = [c_int, c_uint, POINTER(c_uint), c_uint]
        is_PixelClock(self.hid,  IS_PIXELCLOCK_CMD_SET, byref(pixelclock_c), sizeof(pixelclock_c))
        self.pixelclock = pixelclock_c.value


    def get_pixel_clock(self, ):
        pixelclock_c = c_uint(0)
        is_PixelClock = self._lib.is_PixelClock
        is_PixelClock.argtypes = [c_int, c_uint, POINTER(c_uint), c_uint]
        is_PixelClock(self.hid,  IS_PIXELCLOCK_CMD_GET, byref(pixelclock_c), sizeof(pixelclock_c))
        self.pixelclock = pixelclock_c.value
        return self.pixelclock


    def get_allowed_pixel_clock(self, ):
        num_c = c_uint(0)
        is_PixelClock = self._lib.is_PixelClock
        is_PixelClock.argtypes = [c_int, c_uint, POINTER(c_uint), c_uint]
        is_PixelClock(self.hid,  IS_PIXELCLOCK_CMD_GET_NUMBER, num_c, sizeof(num_c))
        pclist_c = (c_uint * num_c.value)(0)
        is_PixelClock(self.hid,  IS_PIXELCLOCK_CMD_GET_LIST, pclist_c, sizeof(pclist_c))
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
    # c.open()
    # c.initialize_memory()
    im = c.capture()
    pl.plot(im)
    c.close()
    pl.show()
