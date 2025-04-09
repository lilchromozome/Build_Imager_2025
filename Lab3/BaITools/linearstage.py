
import os
import time

import numpy as np
from helper import check_minmax

cwd = os.getcwd()
absolute_path_to_dlls = cwd + os.sep + 'dlls'
absolute_path_to_dlls = r'C:\Program Files\Thorlabs\APT\APT Server'


os.environ['PATH'] = absolute_path_to_dlls + os.pathsep + os.environ['PATH']
try:
    # Python 3.8 introduces a new method to specify dll directory
    os.add_dll_directory(absolute_path_to_dlls)
except AttributeError:
    pass

import thorlabs_apt as apt

class LinearStage():
    def __init__(self):
        device_info = apt.list_available_devices()
        self.serial_num = device_info[0][1]
        self.hardware_info = apt.hardware_info(self.serial_num)
        self._motor = apt.Motor(self.serial_num)
        (min_pos, max_pos, units, pitch) = self._motor.get_stage_axis_info()
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.units = units
        self.pitch = pitch
        
        (max_accn, max_vel) = self._motor.get_velocity_parameter_limits()
        self._motor.set_velocity_parameters(min_vel=0.0,accn=max_accn,max_vel=max_vel)
        # self.home()
        # self._homed = True

    def home(self):
        self._motor.move_home(True)
        self._homed = True

    def set_position(self, pos):
        # assert self._homed, 'Motor has not been homed. Run the LinearStage.home() method before trying to move the motor'
        # assert pos>self.min_pos, 'Target position, '+ str(pos)+ ', is below the minimum position, ' + str(self.min_pos)
        # assert pos<self.max_pos,  'Target position, '+ str(pos)+ ', is above the maximum position, ' + str(self.max_pos)
        pos = check_minmax(pos, self.min_pos, self.max_pos)
        self._motor.move_to(pos,blocking=True)

    def move(self,relative_pos):
        pos = self._motor.position + relative_pos
        self.move_to(pos)
        
    def get_position(self, ):
        print(self._motor.position)



# myLinearStage = LinearStage()

# myLinearStage.home()

# # Check if the motor works
# for n in np.arange(5):
#     myLinearStage.move_to(3 + n*3)
#     time.sleep(0.5)

# # Check if the motor works
# for n in np.arange(5):
#     myLinearStage.move_to(3 + (4-n)*3)
#     time.sleep(0.5)


