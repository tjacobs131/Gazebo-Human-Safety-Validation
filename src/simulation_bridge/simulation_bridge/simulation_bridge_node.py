import curses
import subprocess
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry, Path
from time import sleep

class SimulationBridge(Node):

    received_path = False

    def __init__(self):
        super().__init__('simulation_bridge')
        # Set up publisher
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)
        self.goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 1)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "odom", self._odometry, 1)
        self.planned_path = self.create_subscription(Path, "planned_path", self._planned_path, 1)

        self.get_logger().info("Started Simulation Bridge")
        self.logger = self.get_logger()

        self.start()

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

    def _planned_path(self, msg):
        self.logger.info("Planned path received")
        self.received_path = True


    def start(self):
        self.logger.info("Starting")
        
        # Send nav goal
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.pose.position.x = 5.0
        goal.pose.position.y = 5.0
        goal.pose.orientation.z = 1.0
        goal.pose.orientation.w = -1.0

        while(not self.received_path):
            self.goal_pub.publish(goal)
            sleep(0.5)
            rclpy.spin_once(self)

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