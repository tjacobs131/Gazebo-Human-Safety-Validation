import curses
import math
import subprocess
from timeit import default_timer
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
from nav2_msgs.action import NavigateToPose
from time import sleep, time

class OdometryReadout(Node):

    received_path = False

    xy_tolerance = 0.85
    yaw_tolerance = 0.40
    standing_still_time = 0
    standing_still_time_threshold = 4 # The amount of odometry messages to confirm that the robot is standing still

    def __init__(self):
        super().__init__('odometry_readout')

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "odom", self._odometry, 1)

        self.get_logger().info("Started Odometry Readout")
        self.logger = self.get_logger()

    def _odometry(self, msg):
        position = msg.pose.pose.position
        orientation = msg.pose.pose.orientation
        linear_velocity = msg.twist.twist.linear
        angular_velocity = msg.twist.twist.angular

        self.logger.info("\n\n----- Odometry -----\n\n"

        + "Position:\n"
        + f"  x: {position.x:.3f}\n"
        + f"  y: {position.y:.3f}\n"
        + f"  z: {position.z:.3f}\n"
        
        + "Orientation (quaternion):\n"
        + f"  x: {orientation.x:.3f}\n"
        + f"  y: {orientation.y:.3f}\n"
        + f"  z: {orientation.z:.3f}\n"
        + f"  w: {orientation.w:.3f}\n"
        
        + "Linear Velocity:\n"
        + f"  x: {linear_velocity.x:.3f}\n"
        + f"  y: {linear_velocity.y:.3f}\n"
        + f"  z: {linear_velocity.z:.3f}\n"
        
        + "Angular Velocity:\n"
        + f"  x: {angular_velocity.x:.3f}\n" 
        + f"  y: {angular_velocity.y:.3f}\n"
        + f"  z: {angular_velocity.z:.3f}\n")


def main():
    if is_node_running('odometry_readout'):
        print("Node already running")
        raise SystemExit

    rclpy.init()

    odometry_readout = OdometryReadout()

    rclpy.spin(odometry_readout)

    odometry_readout.destroy_node()
    rclpy.shutdown()

def is_node_running(node_name):
    result = subprocess.run(['ros2', 'node', 'list'], stdout=subprocess.PIPE)
    return node_name in result.stdout.decode('utf-8') 