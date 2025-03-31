from time import sleep
import serial.tools.list_ports
import sys
# sys.path.append(r'Maestro-master')
sys.path.append(r'C:\Program Files (x86)\Pololu\Maestro\Maestro-master')
import maestro
import warnings
from helper import check_minmax
# Servo control module through Pololu Maestro
# Grace Gang, Esme Zhang, 20210207
# NOTE: target is in microsecond instead of quarter microsecond, therefore x4
# TODOS

class Pololu:
    count = 0
    def __init__(self, chs=[0, 1, 2, 3, 4, 5]):
        if Pololu.count > 0:
            raise Exception('An object has already been initialized')
        else:
            Pololu.count += 1
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                if 'Pololu Micro Maestro 6-Servo Controller Command Port' in p.description:
                    self.m = maestro.Controller(p.device)

            # Set default parameters
            self._default_speed = [0, 2, 3, 3, 3, 3]
            self._default_acc = [0, 2, 3, 3, 3, 3]
            # NOTE: in microsecond. When setTarget, multiply by 4 to be in quarter-microsecond
            self._default_min = [1500, 496, 496, 496, 400, 496]
            self._default_max = [1500, 2496, 2496, 2496, 3000, 2496]
            self._mid_pos = [1500, 1540, 1496, 1496, 1496, 1496]
            self._chs = chs
            self.set_default_params()
            self.home()
            print('Servo control initialized successfully.')

    def __del__(self):
        self.close()

    # Set speed, acceleration, min and max (software min max)
    def set_default_params(self,):
        [self.set_speed(ch, self._default_speed[ch]) for ch in self._chs]
        [self.set_accel(ch, self._default_acc[ch]) for ch in self._chs]
        [self.set_range(ch, self._default_min[ch], self._default_max[ch]) for ch in self._chs]

    def home(self):
        [self.set_position(ch, self._mid_pos[ch]) for ch in self._chs]

    def set_speed(self, ch, speed):
        if speed > self._default_speed[ch]:
            warnings.warn(f'Requested speed exceeds max allowed ({self._default_speed[ch]}). Speed set to {self._default_speed[ch]}.')
            speed = self._default_speed[ch]
        self.m.setSpeed(ch, speed)

    def set_accel(self, ch, acc):
        if acc > self._default_acc[ch]:
            warnings.warn(f'Requested acceleration exceeds max allowed ({self._default_acc[ch]}). Acceleration set to {self._default_acc[ch]}.')
            acc = self._default_acc[ch]
        self.m.setAccel(ch, acc)

    def set_range(self, ch, min_, max_):
        if min_ < self._default_min[ch]:
            warnings.warn(f'Requested minimum exceeds range. Minimum set to default {self._default_min[ch]}.')
            min_ = self._default_min[ch]
        if max_ > self._default_max[ch]:
            warnings.warn(f'Requested maximum exceeds range. Maximum set to default {self._default_max[ch]}.')
            max_ = self._default_max[ch]
        self.m.setRange(ch, min_*4, max_*4)


    def set_position(self, ch, target, blocking=True, interval=0.5):
        target = check_minmax(target, self._default_min[ch], self._default_max[ch])
        target = int(target)

        if blocking is True:
            pos0 = self.m.getPosition(ch)
            self.m.setTarget(ch, target*4)
            sleep(interval)
            pos1 = self.m.getPosition(ch)
            while pos1 != target and pos0 != pos1:
                pos0 = pos1
                sleep(interval)
                pos1 = self.m.getPosition(ch)
        else:
            self.m.setTarget(ch, target*4)


    def get_position(self, ch, ):
        return self.m.getPosition(ch, ) // 4

    def get_range(self, ch):
        return self._default_min[ch], self._default_max[ch]

    def is_moving(self, ch, ):
        return self.m.isMoving(ch, )

    def stop(self, ch):
        return self.m.setTarget(ch, self.m.getPosition(ch))

    def close(self):
        Pololu.count = 0
        self.home()
        self.m.usb.close()
