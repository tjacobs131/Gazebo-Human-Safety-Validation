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
        self.vel_pub = self.create_publisher(Twist, "cmd_vel", 1)

        # Set up subscriber
        self.odo_sub = self.create_subscription(Odometry, "odom", self._odometry, 1)

        self.get_logger().info("Started Simulation Bridge")

        self.logger = self.get_logger()

        start = time.time()
        while time.time() - start < 14:
            pass

        self.start()

    def _odometry(self, msg):
        self.logger.info(msg)


    def start(self):
        cmd = Twist()
        cmd.linear.x = -1.0

        self.logger.info("Publishing: " + str(cmd.linear.x))
        self.vel_pub.publish(cmd)
        


def main(args=None):
    rclpy.init(args=args)

    simulation_bridge = SimulationBridge()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
