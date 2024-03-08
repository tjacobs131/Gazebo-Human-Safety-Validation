import math
import rclpy
from rclpy.node import Node
import pcg_gazebo
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import time

class SimulationBridge(Node):

    def __init__(self):
        super().__init__('simulation_bridge')
        # Set up publisher
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "wheel/odometry", self._odometry, 10)

        self.get_logger().info("Started Simulation Bridge")

        self.logger = self.get_logger()

        start = time.time()
        while time.time() - start < 12:
            pass

        self.start()

    def _odometry(self, msg):
        self.logger.info("\n\n----- Odometry -----\n")

        # Position
        position = msg.pose.pose.position
        self.logger.info("Position:")
        self.logger.info(f"  x: {position.x:.3f}")
        self.logger.info(f"  y: {position.y:.3f}")
        self.logger.info(f"  z: {position.z:.3f}")

        # Orientation (quaternion)
        orientation = msg.pose.pose.orientation
        self.logger.info("Orientation (quaternion):")
        self.logger.info(f"  x: {orientation.x:.3f}")
        self.logger.info(f"  y: {orientation.y:.3f}")
        self.logger.info(f"  z: {orientation.z:.3f}")
        self.logger.info(f"  w: {orientation.w:.3f}")

        # Linear Velocity
        linear_velocity = msg.twist.twist.linear
        self.logger.info("Linear Velocity:")
        self.logger.info(f"  x: {linear_velocity.x:.3f}")
        self.logger.info(f"  y: {linear_velocity.y:.3f}")
        self.logger.info(f"  z: {linear_velocity.z:.3f}")

        # Angular Velocity
        angular_velocity = msg.twist.twist.angular
        self.logger.info("Angular Velocity:")
        self.logger.info(f"  x: {angular_velocity.x:.3f}")
        self.logger.info(f"  y: {angular_velocity.y:.3f}")
        self.logger.info(f"  z: {angular_velocity.z:.3f}")


    def start(self):
        self.logger.info("Starting")


def main(args=None):
    rclpy.init(args=args)

    simulation_bridge = SimulationBridge()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
