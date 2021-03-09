#!/usr/bin/python
from cryptography.fernet import Fernet
from subprocess import check_output
import os

from .logger import logger


def hidraw_raw():
        '''
        Returns hidraw raw and path.
        '''
        raw = []
        for filename in os.listdir('/sys/class/hidraw'):
            real_path = str(check_output(['realpath',f'/sys/class/hidraw/{filename}']))
            path = '/{}/'.format('/'.join(real_path.split('/')[1:-4]))
            raw.append([path,filename])

        return raw

def emotiv_info():
        '''
        Returns headset serial number and hidraw path.
        '''
        try:
            for path,filename in hidraw_raw():
                with open(f'{path}/manufacturer','r') as f:
                    manufacturer = f.readline()
                
                if 'Emotiv' or 'emotiv' in manufacturer:
                    with open(f'{path}serial', 'r') as f:
                        serial = f.readline().strip()
                        hidraw = f'hidraw{int(filename[-1])+1}'
                        return serial, hidraw
        except Exception as e:
            logger.info( f'Couldn\'t open file: {e}')


def is_old_model(serial_number):
    if "GM" in serial_number[-2:]:
        return False
    return True

def get_key2(sn, model):
        k = ['\0'] * 16
        
        
        # --- Model 1 > [Epoc::Research]
        if model == 1:
            k = [sn[-1],'\0',sn[-2],'H',sn[-1],'\0',sn[-2],'T',sn[-3],'\x10',sn[-4],'B',sn[-3],'\0',sn[-4],'P']
            self.samplingRate = 128
            
        # --- Model 2 > [Epoc::Standard]
        if model == 2:   
            k = [sn[-1],'\0',sn[-2],'T',sn[-3],'\x10',sn[-4],'B',sn[-1],'\0',sn[-2],'H',sn[-3],'\0',sn[-4],'P']
            self.samplingRate = 128
            
        # --- Model 3 >  [Insight::Research]
        if model == 3:
            k = [sn[-2],'\0',sn[-1],'D',sn[-2],'\0',sn[-1],'\x0C',sn[-4],'\0',sn[-3],'\x15',sn[-4],'\0',sn[-3],'X']
            self.samplingRate = 128
            
        # --- Model 4 > [Insight::Standard]
        if model == 4: 
            k = [sn[-1],'\0',sn[-2],'\x15',sn[-3],'\0',sn[-4],'\x0C',sn[-3],'\0',sn[-2],'D',sn[-1],'\0',sn[-2],'X']
            self.samplingRate = 128
        # --- Model 5 > [Epoc+::Research]
        if model == 5:
            k = [sn[-2],sn[-1],sn[-2],sn[-1],sn[-3],sn[-4],sn[-3],sn[-4],sn[-4],sn[-3],sn[-4],sn[-3],sn[-1],sn[-2],sn[-1],sn[-2]]
            self.samplingRate = 256
            
        # --- Model 6 >  [Epoc+::Standard]
        if model == 6:
            k = [sn[-1],sn[-2],sn[-2],sn[-3],sn[-3],sn[-3],sn[-2],sn[-4],sn[-1],sn[-4],sn[-2],sn[-2],sn[-4],sn[-4],sn[-2],sn[-1]]
        
        key = ''.join(k)
        return str(key)


def get_key(serial, is_research = True):

    file_name = 'key_research.key' if is_research else 'key.key'

    if os.path.exists(file_name):
        try:
            with open(file_name,'rb') as key_file:
                return  key_file.read().decode('utf-8')
        except Exception as e:
            logger.error(e)

    key = '{}\0{}H{}\0{}T{}\x10{}B{}\0{}P'.format(
        *map(serial.__getitem__,[-1,-2,-1,-2,-3,-4,-3,-4])
    ) if is_research else '{}\0{}T{}\0{}B{}\x10{}H{}\0{}P'.format(
        *map(serial.__getitem__,[-1,-2,-3,-4,-1,-2,-3,-4])
    )
    try:
        with open(file_name,'wb') as key_file:
            key_file.write(key.encode())
    except Exception as e:
        logger.error(e)

    return key 


def new_key(serial):
    key = '{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}{}'.format(
        *map(serial.__getitem__,[-1,-2,-2,-3,-3,-3,-2,-4,-1,-4,-2,-2,-4,-4,-2,-1])
    )
    return key

def epoc_plus_key(serial):
    key = '{}\x00{}\x15{}\x00{}\x0C{}\x00{}D{}\x00{}X'.format(
        *map(serial.__getitem__,[-1,-2,-3,-4,-3,-2,-1,-2])
    )
    return key

def validate_data(data, new_format=False):
    if new_format:
        if len(data) == 64:
            data.insert(0, 0)
        if len(data) != 65:
            return None
    else:
        if len(data) == 32:
            data.insert(0, 0)
        if len(data) != 33:
            return None
    return data


values_header = "Timestamp,F3 Value,F3 Quality,FC5 Value,FC5 Quality,F7 Value,F7 Quality,T7 Value,T7 Quality,P7 Value," \
                "P7 Quality,O1 Value,O1 Quality,O2 Value,O2 Quality,P8 Value,P8 Quality,T8 Value,T8 Quality,F8 Value,F8 Quality," \
                "AF4 Value,AF4 Quality,FC6 Value,FC6 Quality,F4 Value,F4 Quality,AF3 Value,AF3 Quality,X Value,Y Value,Z Value\n"




def bits_to_float(b):
    print('bits to float')
    print('b: {}'.format(b))
    print('bj: {}'.format("".join(b)))
    b = "".join(b)
    print('a: {}'.format(b))
    # s = struct.pack('L', b)
    # print("s: {}".format(s))
    return struct.unpack('>d', b)[0]


def writer_task_to_line(next_task):
    return "{timestamp},{f3_value},{f3_quality},{fc5_value},{fc5_quality},{f7_value}," \
           "{f7_quality},{t7_value},{t7_quality},{p7_value},{p7_quality},{o1_value}," \
           "{o1_quality},{o2_value},{o2_quality},{p8_value},{p8_quality},{t8_value}," \
           "{t8_quality},{f8_value},{f8_quality},{af4_value},{af4_quality},{fc6_value}," \
           "{fc6_quality},{f4_value},{f4_quality},{af3_value},{af3_quality},{x_value}," \
           "{y_value},{z_value}\n".format(
        timestamp=str(next_task.timestamp),
        f3_value=next_task.data['F3']['value'], 
        f3_quality=next_task.data['F3']['quality'],
        fc5_value=next_task.data['FC5']['value'], 
        fc5_quality=next_task.data['FC5']['quality'],
        f7_value=next_task.data['F7']['value'], 
        f7_quality=next_task.data['F7']['quality'],
        t7_value=next_task.data['T7']['value'], 
        t7_quality=next_task.data['T7']['quality'],
        p7_value=next_task.data['P7']['value'], 
        p7_quality=next_task.data['P7']['quality'],
        o1_value=next_task.data['O1']['value'], 
        o1_quality=next_task.data['O1']['quality'],
        o2_value=next_task.data['O2']['value'], 
        o2_quality=next_task.data['O2']['quality'],
        p8_value=next_task.data['P8']['value'], 
        p8_quality=next_task.data['P8']['quality'],
        t8_value=next_task.data['T8']['value'], 
        t8_quality=next_task.data['T8']['quality'],
        f8_value=next_task.data['F8']['value'], 
        f8_quality=next_task.data['F8']['quality'],
        af4_value=next_task.data['AF4']['value'], 
        af4_quality=next_task.data['AF4']['quality'],
        fc6_value=next_task.data['FC6']['value'], 
        fc6_quality=next_task.data['FC6']['quality'],
        f4_value=next_task.data['F4']['value'], 
        f4_quality=next_task.data['F4']['quality'],
        af3_value=next_task.data['AF3']['value'], 
        af3_quality=next_task.data['AF3']['quality'],
        x_value=next_task.data['X']['value'], 
        y_value=next_task.data['Y']['value'],
        z_value=next_task.data['Z']['value']
        )