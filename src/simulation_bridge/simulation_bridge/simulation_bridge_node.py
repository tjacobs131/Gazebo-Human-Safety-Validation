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

class SimulationBridge(Node):

    received_path = False

    xy_tolerance = 0.85
    yaw_tolerance = 0.40
    standing_still_time = 0
    standing_still_time_threshold = 4 # The amount of odometry messages to confirm that the robot is standing still

    def __init__(self):
        super().__init__('simulation_bridge')
        # Set up publisher
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)
        self.goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 1)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "odom", self._odometry, 1)
        self.planned_path = self.create_subscription(Path, "plan", self._planned_path, 1)

        self.get_logger().info("Started Simulation Bridge")
        self.logger = self.get_logger()

        self.start()

    def _odometry(self, msg):
        # Store odometry data to be used in the move_to_goal function
        self.position = msg.pose.pose.position
        if msg.twist.twist.angular.z < 0.05 and msg.twist.twist.linear.x < 0.1:
            self.standing_still_time += 1
        else: 
            self.standing_still_time = 0
            
    def _planned_path(self, msg):
        if not self.received_path:
            self.logger.info("Planned path received")
            self.received_path = True

    def move_to_goal(self, x, y, orientation):
        # Sends a goal to the navigation stack and waits for the robot to reach it

        #Parameters:
        #    x (float): x coordinate of the goal
        #    y (float): y coordinate of the goal
        #    orientation (float): w component of the quaternion representing the orientation of the goal

        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.orientation.w = orientation

        self.received_path = False
        while not self.received_path:
            self.goal_pub.publish(goal)
            sleep(0.5)
            rclpy.spin_once(self)

        while not self.reached_goal(x, y):
            sleep(0.5)
            rclpy.spin_once(self)
        
    def reached_goal(self, x, y):
        # Check odometry to see if the robot has reached the goal within tolerance
        if self.position is None:
            return False
        
        if (abs(self.position.x - x) < self.xy_tolerance and abs(self.position.y - y) < self.xy_tolerance # Check position
                and self.standing_still_time > self.standing_still_time_threshold): # Check if the robot is not rotating
                return True
            
        return False
    
    def wait(self, seconds):
        # Wait for a number of seconds
        start_time = default_timer()
        while default_timer() - start_time < seconds:
            rclpy.spin_once(self)
            sleep(0.1)

    def start(self):
        self.logger.info("Starting")

        self.move_to_goal(-2.0, 2.0, 1.0)

        self.move_to_goal(2.0, 2.0, -0.71)
        
        self.move_to_goal(2.0, -2.0, -1.0)

        self.move_to_goal(-2.0, -2.0, 1.0)

def main():
    if is_node_running('simulation_bridge'):
        print("Node already running")
        raise SystemExit

    rclpy.init()

    simulation_bridge = SimulationBridge()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()

def is_node_running(node_name):
    result = subprocess.run(['ros2', 'node', 'list'], stdout=subprocess.PIPE)
    return node_name in result.stdout.decode('utf-8')