from subprocess import check_output
from gevent.queue import Queue
from datetime import datetime
from tabulate import tabulate
from Crypto.Cipher import AES
from Crypto import Random
import gevent
import sys
import os

from .utils import emotiv_info,get_key2
from .logger import logger
from .constants import *

DEVICE_POOL_INTERVAL = 0.01

class Epoc(object):
    def __init__(self, socket, display = True):
        self.key = ''
        self.serial = ''
        self.chanels = []
        self.running = False
        self.sampling_rate = 256
        self.hidraw = ''
        self.display = display
        self.sensors = {
            'F3':  {'value': 0, 'quality': 0},
            'FC6': {'value': 0, 'quality': 0},
            'P7':  {'value': 0, 'quality': 0},
            'T8':  {'value': 0, 'quality': 0},
            'F7':  {'value': 0, 'quality': 0},
            'F8':  {'value': 0, 'quality': 0},
            'T7':  {'value': 0, 'quality': 0},
            'P8':  {'value': 0, 'quality': 0},
            'AF4': {'value': 0, 'quality': 0},
            'F4':  {'value': 0, 'quality': 0},
            'AF3': {'value': 0, 'quality': 0},
            'O2':  {'value': 0, 'quality': 0},
            'O1':  {'value': 0, 'quality': 0},
            'FC5': {'value': 0, 'quality': 0},
            'X':   {'value': 0, 'quality': 0},
            'Y':   {'value': 0, 'quality': 0},
            'Unknown': {'value': 0, 'quality': 0}
        }
        self.battery = 0
        self.encrypted_queue = Queue()
        self.deencrypted_queue = Queue()
        self.socket = socket



    def get_sensors(self):
        return self.sensors

    def start(self):
        '''
        Setup for headset Epoc + on Linux platform
        Retrive data from headset and put to a Queue to be processed
        '''
        self.serial, self.hidraw = emotiv_info()
        self.key = get_key2(sn =self.serial,model = 6)

        self.running = True
        #Initializing Threads
        logs = gevent.spawn(run = self.send_data)
        crypto = gevent.spawn(run = self.decrypter)
        stream = gevent.spawn(run = self.streamer)
        gevent.joinall([crypto,logs,stream])
    


    def send_data(self):
        while self.running and self.display:
            os.system('clear')
            data = []
            [data.append([item[0],item[1]['value'],item[1]['quality']]
            ) for item in self.sensors.items()]
            self.socket.emit('data', self.sensors, namespace='/test')
            print(tabulate(data, headers=['Sensor','Value','Quality'],tablefmt="github"))
            gevent.sleep(0)

    def streamer(self):
        with open(f'/dev/{self.hidraw}','rb') as hid:
            while self.running:
                try:
                    data = hid.read(32)
                    if data is not '':
                        self.encrypted_queue.put_nowait(data)
                        gevent.sleep(0)
                    else:
                        gevent.sleep(DEVICE_POOL_INTERVAL)

                except Exception as e:
                    logger.info('Streaming error')
                    logger.error(e)
                    self.running = False
                except KeyboardInterrupt as e:
                    logger.info('Interruped')
                    self.running = False

    def decrypter(self):
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_ECB, iv)
        while self.running:
            if not self.encrypted_queue.empty():
                data = self.encrypted_queue.get()
                try:
                    decrypted_data = cipher.decrypt(data[:16]) + cipher.decrypt(data[16:])
                    self.deencrypted_queue.put_nowait(Packet(decrypted_data,self.sensors))
                except Exception as e:
                    logger.info('Decryption error')
                    logger.error(e)
                    self.running = False
                except KeyboardInterrupt as e:
                    logger.info('Exit')
                    self.running = False
                gevent.sleep(0)
            gevent.sleep(0)
    
    def update_sensors(self):
        pass


# battery = 0
class Packet(object):
    '''
    Basic semantics for input bytes
    '''
    def __init__(self, data,sensors):
        '''
        Initializes packet data. Sets the global battery value.
        Updates each sensor with current sensor value from the packet data.
        '''

        self.data = data
        self.battery = 0
        self.count = data[0]

        #Battery level
        # if self.count > 127:
        #     # logger.info('Im here')
        #     self.battery = self.count
        #     battery = battery_values[str(self.battery)]
        #     self.count = 128
        
        # self.sync = self.count == 0xe9
        self.gyro_x = data[29] - 106
        self.gyro_y = data[30] - 105
        sensors['X']['value'] = self.gyro_x
        sensors['Y']['value'] = self.gyro_y


        for name, bits in sensor_bits.items():
            #Get Level for sensors subtract 8192 to get signed value
            value = self.get_level(self.data, bits) - 8192
            setattr(self, name, (value,))
            sensors[name]['value'] = value

        self.handle_quality(sensors)
        self.sensors = sensors
# 
    def convert_epoc(self, value_1, value_2):
        edk_value = '%.8f'%(((int(value_1)*.128205128205129)+4201.02564096001)+((int(value_2)-128)*32.82051289))
        if self.integer == True:
            return str(int(float(edk_value)))
        return edk_value

    def get_level(self,data, bits):
        '''
        Returns sensor level value from data using sensor bit mask in micro volts (uV).
        '''
        level = 0
        for i in range(13, -1, -1):
            level <<= 1
            b, o = int(bits[i] / 8) + 1, bits[i] % 8
            level |= (data[b] >> o) & 1
        return level

    def handle_quality(self, sensors):
        '''
        Sets the quality value for the sensor from the quality bits in the packet data.
        Optionally will return the value.
        '''
        # if self.old_model:
        #     current_contact_quality = get_level(self.raw_data, quality_bits) / 540
        # else:
        current_contact_quality = self.get_level(self.data, quality_bits) / 1024
        sensor = self.data[0]
        
# 
        sensor = self.data[0]
        if sensor == 0 or sensor == 64:
            sensors['F3']['quality'] = current_contact_quality
        elif sensor == 1 or sensor == 65:
            sensors['FC5']['quality'] = current_contact_quality
        elif sensor == 2 or sensor == 66:
            sensors['AF3']['quality'] = current_contact_quality
        elif sensor == 3 or sensor == 67:
            sensors['F7']['quality'] = current_contact_quality
        elif sensor == 4 or sensor == 68:
            sensors['T7']['quality'] = current_contact_quality
        elif sensor == 5 or sensor == 69:
            sensors['P7']['quality'] = current_contact_quality
        elif sensor == 6 or sensor == 70:
            sensors['O1']['quality'] = current_contact_quality
        elif sensor == 7 or sensor == 71:
            sensors['O2']['quality'] = current_contact_quality
        elif sensor == 8 or sensor == 72:
            sensors['P8']['quality'] = current_contact_quality
        elif sensor == 9 or sensor == 73:
            sensors['T8']['quality'] = current_contact_quality
        elif sensor == 10 or sensor == 74:
            sensors['F8']['quality'] = current_contact_quality
        elif sensor == 11 or sensor == 75:
            sensors['AF4']['quality'] = current_contact_quality
        elif sensor == 12 or sensor == 76 or sensor == 80:
            sensors['FC6']['quality'] = current_contact_quality
        elif sensor == 13 or sensor == 77:
            sensors['F4']['quality'] = current_contact_quality
        elif sensor == 14 or sensor == 78:
            sensors['F8']['quality'] = current_contact_quality
        elif sensor == 15 or sensor == 79:
            sensors['AF4']['quality'] = current_contact_quality
        else:
            sensors['Unknown']['quality'] = current_contact_quality
            sensors['Unknown']['value'] = sensor




if __name__ ==  '__main__':
    epoc = Epoc()
    try:
        epoc.run()
    except Exception as e:
        logger.error(e)
    except KeyboardInterrupt as e:
        logger.error(e)

