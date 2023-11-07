import os
import time
from datetime import datetime
from roboclaw_3 import Roboclaw
import numpy
import matplotlib.pyplot as plt

class Roboclaw_zwv(Roboclaw):
    def __init__(self, comport, rate, timeout=0.01, retries=3, log_file_dir = "../../Logs"):
        Roboclaw.__init__(self, comport, rate, timeout=0.01, retries=3)
        self.log_file_dir = log_file_dir
        
    def read_metrics(self, address):
        read_1_time = time.time()
        _,M1Position,_ = self.ReadEncM1(address)
        read_2_time = time.time()
        _,M1Speed,_ = self.ReadSpeedM1(address)
        read_3_time = time.time()
        _,M1Current,_ = self.ReadCurrents(address)
        read_4_time = time.time()
        
        return read_1_time,M1Position,read_2_time,M1Speed,read_3_time,M1Current,read_4_time

    def create_log_file(self):
        log_file_name = str(datetime.now()).replace('-', '').replace(':', '').replace('.', '') + '.csv'
        log_file_path = os.path.join(self.log_file_dir, log_file_name)
        self.log_file = open(log_file_path, 'w')

    def output_metrics_to_file(self, address, file):
        metrics = self.read_metrics(address)
        metrics_as_string = ','.join(list(map(lambda metric: str(metric), metrics)))
        file.write(metrics_as_string + '\n')

    def output_metrics_to_screen(self, address):
        read_start,position,_,speed,_,current,read_end = self.read_metrics(address)
        print("Sampling metrics - ")
        print(f"Read Start : {read_start}")
        print(f"Position : {position}")
        print(f"Speed : {speed}")
        print(f"Current : {current}")
        print(f"Read End : {read_end}")
        
    def get_metrics_from_log(self, log_file_path):
        with open(log_file_path, 'r') as log_file:
            log_file_lines = log_file.readlines()
            metrics = list(map(lambda line: [float(field) for field in line.split(',')], log_file_lines))
            return metrics
        
    def graph_metrics(self, log_file_path):
        metrics = self.get_metrics_from_log(log_file_path)
        
        absolute_times = list(map(lambda metric: metric[0], metrics))
        base_time = absolute_times[0]
        relative_times = list(map(lambda absolute_time: (absolute_time - base_time) * 1000, absolute_times))
        
        absolute_positions = list(map(lambda metric: metric[1], metrics))
        base_position = absolute_positions[0]
        relative_positions = list(map(lambda absolute_position: absolute_position - base_position, absolute_positions))

        speeds = list(map(lambda metric: metric[3], metrics))
        currents = list(map(lambda metric: metric[5] * 10, metrics))
        
        figure, axis = plt.subplots(3,1)
        
        axis[0].plot(relative_times, relative_positions)
        axis[0].set(ylabel='position (encoder count)')
        
        axis[1].plot(relative_times, speeds)
        axis[1].set(ylabel='speed (encoder count/sec)')
        
        axis[2].plot(relative_times, currents)
        axis[2].set(xlabel='time (ms)', ylabel='current (mA)')
        
        plt.show()
        
    def execute_buffered_commands_with_logging(self, address, commands, before_wait_time = .5, after_wait_time = .5):
        self.create_log_file()
        
        begin_time = time.time()
        while (time.time() - begin_time) < before_wait_time:
            self.output_metrics_to_file(address, self.log_file)
            
        for command in commands:
            command()
        
        buffers = (0,0,0)
        while buffers[1]!=0x80:
            self.output_metrics_to_file(address, self.log_file)
            buffers = self.ReadBuffers(address)
        
        begin_time = time.time()
        while (time.time() - begin_time) < after_wait_time:
            self.output_metrics_to_file(address, self.log_file)
            
        self.log_file.close()