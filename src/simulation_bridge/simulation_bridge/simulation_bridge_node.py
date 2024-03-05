import rclpy
from rclpy.node import Node
import pcg_gazebo
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Joy
import time

class SimulationBridge(Node):

    def __init__(self):
        super().__init__('simulation_bridge')
        # Set up publisher
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "/odom", self._odometry, 10)
        self.joy_sub = self.create_subscription(Joy, "joy", self._joy, 1)

        self.get_logger().info("Started Simulation Bridge")

        self.logger = self.get_logger()

        start = time.time()
        while time.time() - start < 12:
            pass

        self.start()

    def _odometry(self, msg):
        self.logger.info("Odometry:")
        self.logger.info(msg.pose.pose.orientation.x)
        self.logger.info(msg.pose.pose.orientation.y)
        self.logger.info(msg.pose.pose.orientation.z)

    def _joy(self, msg):
        vel_msg = Twist()

        if(msg.buttons[5]):
            
            if msg.axes[1] > 0.2 or msg.axes[1] < -0.2:

                if(msg.buttons[9]):
                    vel_msg.linear.x = msg.axes[1] * 4
                else:
                    vel_msg.linear.x = msg.axes[1] * 2
            else:
                vel_msg.linear.x = 0.0
                
            if msg.axes[0] > 0.2 or msg.axes[0] < -0.2:
                vel_msg.angular.z = msg.axes[0]
            else:
                vel_msg.angular.z = 0.0

            self.vel_pub.publish(vel_msg)

        else:
            self.vel_pub.publish(vel_msg)


    def start(self):
        cmd = Twist()
        cmd.linear.x = -0.0

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
