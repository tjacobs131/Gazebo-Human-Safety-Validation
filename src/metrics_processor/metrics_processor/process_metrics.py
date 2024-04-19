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
from std_srvs.srv import Trigger

class MetricsProcessor(Node):

    target_variables = ["robot_on_person_collision", "minimum_distance_to_people", "intimate_space_intrusions", "personal_space_intrusions"]

    def __init__(self):
        super().__init__('metrics_processor')

        self.logger = self.get_logger()
        self.logger.info("Started Metrics Processor")

        self.recording_srv = self.create_service(Trigger, 'hunav_trigger_recording', self.__recording_callback)

    def start(self):
        sleep(0.5) # Give hunav_evaluator time to save metrics file

        # Get metrics file from base workspace directory
        metrics_path = os.path.realpath(os.path.join(get_package_share_directory("metrics_processor"), '../../../..', 'metrics.txt'))
        safety_metrics = {}

        with open(metrics_path, "r") as file:
            metrics = file.read()
            if metrics is None:
                self.logger.error("No metrics found in file")
            else:
                variables = metrics.split("\n")[0].split("\t")
                values = metrics.split("\n")[-2].split("\t")

                self.logger.info("Saving safety metrics")
                for i in range(len(variables)):
                    if variables[i] in self.target_variables:
                        self.logger.info(f"{variables[i]}: {values[i]}")
                        safety_metrics[variables[i]] = values[i]                

        # Store metrics in a new file
        metrics_path = os.path.realpath(os.path.join(get_package_share_directory("metrics_processor"), '../../../..', 'safety_metrics.txt'))
        with open(metrics_path, "w") as file:
            for key in safety_metrics:
                file.write(f"{key}: {safety_metrics[key]}\n")
            file.close()

        self.logger.info("Scenario complete, shutting down...") # Signal to the scenario launcher that the metrics have been saved


    def __recording_callback(self, request, response):
        response.success = True
        response.message = "Recording started"

        self.start()

        return response


def main():

    rclpy.init()

    metrics_processor = MetricsProcessor()

    rclpy.spin(metrics_processor)

    metrics_processor.destroy_node()
    rclpy.shutdown()