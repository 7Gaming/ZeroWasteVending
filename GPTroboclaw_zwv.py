# Import necessary libraries
import os
import time
from datetime import datetime
from roboclaw_3 import Roboclaw
import numpy
import matplotlib.pyplot as plt

# Define a custom class Roboclaw_zwv that extends the Roboclaw class
class Roboclaw_zwv(Roboclaw):
    def __init__(self, comport, rate, timeout=0.01, retries=3, log_file_dir="../../Logs"):
        # Initialize the custom Roboclaw_zwv class with additional parameters
        Roboclaw.__init__(self, comport, rate, timeout=0.01, retries=3)
        self.log_file_dir = log_file_dir  # Directory for log files

    # Read various metrics from the Roboclaw for a given address
    def read_metrics(self, address):
        # Timestamp when each metric is read
        read_1_time = time.time()
        _, M1Position, _ = self.ReadEncM1(address)  # Read motor position
        read_2_time = time.time()
        _, M1Speed, _ = self.ReadSpeedM1(address)  # Read motor speed
        read_3_time = time.time()
        _, M1Current, _ = self.ReadCurrents(address)  # Read motor current
        read_4_time = time.time()

        # Return a tuple with timestamps and metric values
        return read_1_time, M1Position, read_2_time, M1Speed, read_3_time, M1Current, read_4_time

    # Create a log file for storing metric data
    def create_log_file(self):
        # Generate a unique log file name based on the current timestamp
        log_file_name = str(datetime.now()).replace('-', '').replace(':', '').replace('.', '') + '.csv'
        log_file_path = os.path.join(self.log_file_dir, log_file_name)  # Full log file path
        self.log_file = open(log_file_path, 'w')  # Open the log file for writing

    # Write metrics to a specified file
    def output_metrics_to_file(self, address, file):
        # Read metrics and convert them to a comma-separated string
        metrics = self.read_metrics(address)
        metrics_as_string = ','.join(list(map(lambda metric: str(metric), metrics))
        # Write the metrics to the log file
        file.write(metrics_as_string + '\n')

    # Display metrics on the screen
    def output_metrics_to_screen(self, address):
        # Read metrics and display them on the console
        read_start, position, _, speed, _, current, read_end = self.read_metrics(address)
        print("Sampling metrics - ")
        print(f"Read Start : {read_start}")
        print(f"Position : {position}")
        print(f"Speed : {speed}")
        print(f"Current : {current}")
        print(f"Read End : {read_end}")

    # Get metrics from a log file
    def get_metrics_from_log(self, log_file_path):
        # Read metrics from a specified log file
        with open(log_file_path, 'r') as log_file:
            log_file_lines = log_file.readlines()
            # Parse the lines into a list of metrics (each metric is a list of floats)
            metrics = list(map(lambda line: [float(field) for field in line.split(',')], log_file_lines))
        return metrics

    # Plot metrics from a log file
    def graph_metrics(self, log_file_path):
        # Get metrics from a log file
        metrics = self.get_metrics_from_log(log_file_path)

        # Extract data for plotting
        absolute_times = list(map(lambda metric: metric[0], metrics))
        base_time = absolute_times[0]
        relative_times = list(map(lambda absolute_time: (absolute_time - base_time) * 1000, absolute_times))
        absolute_positions = list(map(lambda metric: metric[1], metrics))
        base_position = absolute_positions[0]
        relative_positions = list(map(lambda absolute_position: absolute_position - base_position, absolute_positions))
        speeds = list(map(lambda metric: metric[3], metrics))
        currents = list(map(lambda metric: metric[5] * 10, metrics))

        # Create a figure with three subplots for position, speed, and current
        figure, axis = plt.subplots(3, 1)

        # Plot position data
        axis[0].plot(relative_times, relative_positions)
        axis[0].set(ylabel='position (encoder count)')

        # Plot speed data
        axis[1].plot(relative_times, speeds)
        axis[1].set(ylabel='speed (encoder count/sec)')

        # Plot current data
        axis[2].plot(relative_times, currents)
        axis[2].set(xlabel='time (ms)', ylabel='current (mA)')

        # Display the plots
        plt.show()

    # Execute a sequence of buffered commands while logging metrics
    def execute_buffered_commands_with_logging(self, address, commands, before_wait_time=0.5, after_wait_time=0.5):
        # Create a log file to store metrics
        self.create_log_file()

        begin_time = time.time()
        # Capture metrics for a specified time before executing commands
        while (time.time() - begin_time) < before_wait_time:
            self.output_metrics_to_file(address, self.log_file)

        # Execute a sequence of commands
        for command in commands:
            command()

        buffers = (0, 0, 0)
        # Wait until the command buffers are empty
        while buffers[1] != 0x80:
            self.output_metrics_to_file(address, self.log_file)
            buffers = self.ReadBuffers(address)

        begin_time = time.time()
        # Capture metrics for a specified time after executing commands
        while (time.time() - begin_time) < after_wait_time:
            self.output_metrics_to_file(address, self.log_file)

        # Close the log file
        self.log_file.close()
