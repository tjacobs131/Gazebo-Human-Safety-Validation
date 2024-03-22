import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from time import sleep

class SimulationBridge(Node):

    def __init__(self):
        super().__init__('simulation_bridge')
        # Set up publisher
        self.vel_pub = self.create_publisher(Twist, "/cmd_vel", 5)
        self.goal_pub = self.create_publisher(PoseStamped, "/goal_pose", 1)

        # Set up subscribers
        self.odom_sub = self.create_subscription(Odometry, "odom", self._odometry, 10)
        # Set up subscriber for move_base result
        # self.move_base_result_sub = self.create_subscription(
        #     MoveBaseResult,
        #     "/move_base/result",
        #     self.move_base_result_callback,
        #     10
        # )
        self.planner_sub = self.create_subscription(PoseStamped, "/compute_path_to_pose/_action/status", self._planner, 10)

        self.get_logger().info("Started Simulation Bridge")
        self.logger = self.get_logger()

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
        
        # Send nav goal
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.pose.position.x = 5.0
        goal.pose.position.y = 5.0
        goal.pose.position.z = 0.0
        goal.pose.orientation.x = 0.0
        goal.pose.orientation.y = 0.0
        goal.pose.orientation.z = 0.0
        goal.pose.orientation.w = 1.0

        sleep(10)

        self.goal_pub.publish(goal)

        # goal_received = False
        # while not goal_received:
        #     self.goal_pub.publish(goal) 
        #     # You might want to add a small delay here to avoid flooding the topic
        #     time.sleep(0.1)

        #     # Check if goal has been received
        #     if self.goal_received:
        #         goal_received = True
        #         self.logger.info("Goal received!")



def main(args=None):
    rclpy.init(args=args)

    simulation_bridge = SimulationBridge()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
