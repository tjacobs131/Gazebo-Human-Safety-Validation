import curses
import math
import subprocess
import yaml
from timeit import default_timer
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
from nav2_msgs.action import NavigateToPose
from time import sleep, time
from dataclasses import dataclass
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

class SimulationBridge(Node):

    @dataclass
    class Goal:
        x: float
        y: float
        yaw: float

    received_path = False

    xy_tolerance = 0.85
    yaw_tolerance = 0.40
    standing_still_time = 0
    standing_still_time_threshold = 4 # The amount of odometry messages to confirm that the robot is standing still\

    movement_goals = []

    def __init__(self):
        super().__init__('simulation_bridge')

        self.logger = self.get_logger()
        self.logger.info("Started Simulation Bridge")

        self.load_goals()

        # Set up publishers
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)
        self.goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 1)
        self.done_pub = self.create_publisher(Bool, "robot_done", 1)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "odom", self._odometry, 1)
        self.planned_path = self.create_subscription(Path, "plan", self._planned_path, 1)

        # Set up stop evaluation client
        self.eval_client = self.create_client(Trigger, 'hunav_trigger_recording')

        self.start()

    def load_goals(self):
        # Get parameter file
        self.declare_parameter(name="params_file", value="goals.yaml")
        self.param = self.get_parameter(name="params_file").value
        if self.param is None:
            self.logger.error("No goals parameter found")
        else:
            self.logger.info(f"Using parameter file: {self.param}")

        # Load goals from parameter file
        with open(self.param, "r") as file:
            config = yaml.safe_load(file)
            goals = config["/simulation_bridge"]["ros__parameters"]["goals"]
            if goals is None:
                self.logger.error("No goals found in parameter file")
                raise ValueError("No goals found in parameter file")
            else:
                try:
                    while True:
                        goal = goals["goal" + str(len(self.movement_goals))]
                        self.movement_goals.append(self.Goal(goal["x_pos"], goal["y_pos"], goal["yaw"]))
                except KeyError:
                    pass
        self.logger.info(f"Goals: {self.movement_goals}")

    def _odometry(self, msg):
        # Store odometry data to be used in the move_to_goal function
        self.position = msg.pose.pose.position
        if msg.twist.twist.angular.z < 0.05 and msg.twist.twist.linear.x < 0.1:
            self.standing_still_time += 1
        else: 
            self.standing_still_time = 0
            
    def _planned_path(self, msg):
        # Confirm that the planned goal has been turned into a path
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
        if self.position is None:
            return False
        
        # Check odometry to see if the robot has reached the goal within tolerance
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
        # Iterate through the goals and move to each one
        for goal in self.movement_goals:
            self.logger.info(f"Moving to goal: {goal}")
            self.move_to_goal(goal.x, goal.y, goal.yaw)
            self.logger.info("Goal reached")
            
            if goal == self.movement_goals[-1]:
                self.logger.info("All goals reached")
                msg = Bool()
                msg.data = True
                self.eval_client.wait_for_service()
                request = Trigger.Request()
                self.eval_client.call(request)
                
                self.done_pub.publish(msg)


def main():
    rclpy.init()

    simulation_bridge = SimulationBridge()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()