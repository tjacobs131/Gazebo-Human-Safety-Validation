import curses
import os
import math
import subprocess
from timeit import default_timer

from ament_index_python import get_package_share_directory
import rclpy
from rclpy.node import Node
from time import sleep, time
from std_msgs.msg import Bool

class MetricsProcessor(Node):

    target_variables = ["robot_on_person_collision", "minimum_distance_to_people", "intimate_space_intrusions", "personal_space_intrusions"]

    def __init__(self):
        super().__init__('metrics_processor')

        self.logger = self.get_logger()
        self.logger.info("Started Metrics Processor")

        self.done_sub = self.create_subscription(Bool, 'robot_done', self.__done_callback, 1)

    def start(self):
        # Get metrics file from base workspace directory
        metrics_path = os.path.realpath(os.path.join(get_package_share_directory("metrics_processor"), '../../../..', 'metrics.txt'))
        safety_metrics = {}

        with open(metrics_path, "r") as file:
            metrics = file.read()
            if metrics is None:
                self.logger.error("No metrics found in file")
            else:
                variables = metrics.split("\n")[0].split("\t")
                values = metrics.split("\n")[1].split("\t")

                self.logger.info(f"Variables: {variables}")
                self.logger.info(f"Values: {values}")

                for i in range(len(variables)):
                    if variables[i] in self.target_variables:
                        safety_metrics[variables[i]] = values[i]                

        # Store metrics in a new file
        metrics_path = os.path.realpath(os.path.join(get_package_share_directory("metrics_processor"), '../../../..', 'safety_metrics.txt'))
        with open(metrics_path, "w") as file:
            for key in safety_metrics:
                self.logger.info(f"{key}: {safety_metrics[key]}")
                file.write(f"{key}: {safety_metrics[key]}\n")

    def __done_callback(self, msg):
        if msg.data == True:
            self.start()


def main():

    rclpy.init()

    metrics_processor = MetricsProcessor()

    rclpy.spin(metrics_processor)

    metrics_processor.destroy_node()
    rclpy.shutdown()