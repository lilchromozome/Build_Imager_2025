import serial.tools.list_ports
from helper import check_minmax
import warnings
# Lighting control module through Numato USB Relay
# Grace Gang, Esme Zhang, 20210107

MIN_INTENSITY, MAX_INTENSITY = 0, 63

class Lighting:
    count = 0
    def __init__(self, port=None ):
        if Lighting.count > 0:
            raise Exception('An object has already been initialized')
        else:
            if port is None:
                Lighting.count += 1
                self._intensity = 0
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    if 'USB Serial Device' in p.description:
                        self.s = serial.Serial(p.device, 19200, timeout=1)
            else: 
                self.s = serial.Serial(port, 19200, timeout=1)
            print('Light control initialized successfully.')

                
                
    def __del__(self):
        Lighting.count = 0
        self.set_intensity(0)
        self.s.close()

    def set_intensity(self, intensity):
        intensity = check_minmax(intensity, MIN_INTENSITY, MAX_INTENSITY)
        self._intensity = int(intensity)
        self.s.write(('relay writeall '+ format(self._intensity, '02X') +'\r').encode('utf-8'))

    def get_intensity(self):
        return self._intensity

    def print_intensity(self):
        print(self._intensity)

    def is_open(self):
        print(self.s.isOpen())

    def close(self):
        Lighting.count = 0
        self.set_intensity(0)
        self.s.close()
