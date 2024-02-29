import rclpy
from rclpy.node import Node
import pcg_gazebo

class SimulationBridge(Node):

    def __init__(self):
        super().__init__('simulation_bridge')
        simulation = pcg_gazebo.simulation

        self.get_logger().info("Started Simulation Bridge")

        self.left_wheel = simulation.Link('left_wheel')
        self.right_wheel = simulation.Link('right_wheel')

        self.start()


    def start(self):
        print(self.left_wheel)
        print(self.right_wheel)


def main(args=None):
    rclpy.init(args=args)

    simulation_bridge = SimulationBridge()

    simulation_bridge.init()

    rclpy.spin(simulation_bridge)

    simulation_bridge.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
