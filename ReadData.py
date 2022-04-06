import numpy as np
from scipy.io import loadmat 
import pprint   

class time_value_pair(object):

    def __init__(self, name, info, unit):

        self.name = name
        self.time = info[0]
        self.value = info[1]
        self.unit = unit

    def update(self, time, value):

        self.time = np.append(self.time, time)
        self.value = np.append(self.value, value)

class all_data(object):

    def __init__(self, data):

        variables_raw = data.keys()
        variables = list(variables_raw)
        self.signal = []

        time_list = []
        samplingTime_list = []
        j=0
        timelength = []
        for i in range(0, len(variables)):
            if variables[i] != '__header__' and variables[i] != '__version__' and variables[i] != '__globals__' and variables[i] != 'header':
                signal = get_signal(variables[i], data)
                self.signal.append(signal)      
                j = j + 1
                
def convert_signals(data):
    variables_raw = data.keys()
    variables = list(variables_raw)

def get_signal(signal, data):

    variables_raw = data.keys()
    variables = list(variables_raw)
    signal_list = list(filter(lambda x: signal in x, variables))

    if (len(signal_list) == 0):
        print("Signal named '", signal,"' not found")
        return 0
    elif (len(signal_list) > 1):
        print("More than one '",signal,"' found, choose one and repeat")
        pprint.pprint(signal_list)
        return 0

    unit = data[signal_list[0]]['unit'][0][0][0]
    time = data[signal_list[0]]['time'][0][0][:,0]
    value = data[signal_list[0]]['signals'][0][0][:,0][0][0][:,0]

    if '_gyrX_' in signal:
        value = value*180/np.pi
        unit = 'deg/s'
    if '_gyrY_' in signal:
        value = value*180/np.pi
        unit = 'deg/s'
    if '_gyrZ_' in signal:
        value = value*180/np.pi  
        unit = 'deg/s'  

    return time_value_pair(signal, [time, value], unit)

def get_data(file):

    data = loadmat(file)

    dataset = all_data(data)

    return dataset

















