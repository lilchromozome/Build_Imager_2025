from time import sleep

from thorlabs_tsi_sdk.tl_camera import TLCameraSDK
from thorlabs_tsi_sdk.tl_camera import TLCamera

import numpy as np
from matplotlib import pyplot as plt

import os

cwd = os.getcwd()
absolute_path_to_dlls = cwd + r'/dlls'

os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']
try:
    # Python 3.8 introduces a new method to specify dll directory
    os.add_dll_directory(absolute_path_to_dlls)
except AttributeError:
    pass


class ZeluxCamera(object):
    def __init__(self):
        self._sdk = TLCameraSDK()
        available_cameras = self._sdk.discover_available_cameras()
        if len(available_cameras) < 1:
            raise ValueError("no cameras detected")
        self._cam = self._sdk.open_camera(available_cameras[0])
        # enable frame rate control 
        self._cam.is_frame_rate_control_enabled = 1
        self.image_widt1h = self._cam.image_width_pixels
        self.image_height = self._cam.image_height_pixels
        
        self._cam.frames_per_trigger_zero_for_unlimited = 1  # start camera in continuous mode
        self._cam.image_poll_timeout_ms = 2000  # 2.0 second timeout
        self._cam.arm(2)

    def __del__(self):
        self._cam.disarm()
        self._cam.dispose()
        self._sdk.dispose()
        
    def open(self):
        pass
        
    def close(self):
        self.__del__()
    
    def capture(self, interval=1.0):
        # self._cam.frames_per_trigger_zero_for_unlimited = 0  # start camera in continuous mode
        # self._cam.image_poll_timeout_ms = 2000  # 2.0 second timeout
        # self._cam.arm(2)
        self._cam.issue_software_trigger()
        frame = self._cam.get_pending_frame_or_null()
        # self._cam.disarm()
        im = frame.image_buffer.copy()
        sleep(interval)
        return im    
        
    def set_exposure(self, exposure):
        # exposure should be given in ms
        self._cam.exposure_time_us = exposure*1000

    def get_exposure(self):
        #exposure should be given in ms
        return self._cam.exposure_time_us/1000

    # Returns min, max and inc, in that order
    # TODO not sure how to get inc. only returning min and max
    def get_exposure_range(self, ):
        rng = self._cam.exposure_time_range_us
        return [rng[0]/1000,rng[1]/1000]
    
    def set_framerate(self, framerate):
        self._cam.frame_rate_control_value = framerate
        
    def get_framerate(self):
        return self._cam.frame_rate_control_value

    def get_framerate_range(self):
        rng = self._cam.frame_rate_control_value_range
        return [rng[0],rng[1]]
        
    def get_properties(self):
        print('Camera Model', '\t', 'Thorlabs CS165MU')
        print('Pixel Size', '\t', str(3.45), ' microns')
        print('Image size', '\t', '[1440, 1080]')
        print('Exposure',  '\t', '{0:.2f}'.format(self.get_exposure()), ' ms')
        print('Exposure Range',  '\t', '[{0:.2f}, {1:.2f}]'.format(self.get_exposure_range()[0], self.get_exposure_range()[1]), ' ms')
        print('Framerate',  '\t', '{0:.1f}'.format(self.get_framerate()), )
        print('Frame Range',  '\t', '[{0:.1f}, {1:.1f}]'.format(self.get_framerate_range()[0], self.get_framerate_range()[1]))

# myCamera = ZeluxCamera()
# im = myCamera.acquire()
# print(im.shape)
# print(np.mean(im))
