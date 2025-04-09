import serial
import serial.tools.list_ports
import time

class FilterWheel(object):
    def __init__(self,):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if 'USB Serial Port' in p.description:
                self.serialConnection = serial.Serial(port=p.device,baudrate=115200)
        print('Filter wheel initialized successfully.')
    def set_speed(self,speed):
            # position should be 0 or 1
            speed = int(speed)
            assert(speed>=0)
            assert(speed<=1)
            self.serialConnection.write(b'speed=' + str(speed).encode(encoding='UTF-8')+b'\r')
    def set_position(self,pos):
        # position should be 1, 2, 3, 4, 5, or 6
        pos = int(pos)
        assert(pos>=1 and pos <=6), r'Position should be intergers between 1 and 6.'
        self.serialConnection.write(b'pos=' + str(pos).encode(encoding='UTF-8')+b'\r')
    def close(self):
        self.serialConnection.close()
    def __del__(self):
        try:
            self.close()
        except:
            pass



# myFilterWheel = filterWheel('COM3')


# myFilterWheel.set_speed(0)
# myFilterWheel.set_position(3)
# time.sleep(2)
# myFilterWheel.set_position(5)
# time.sleep(2)

# myFilterWheel.set_speed(1)
# myFilterWheel.set_position(3)
# time.sleep(2)
# myFilterWheel.set_position(5)
# time.sleep(2)








