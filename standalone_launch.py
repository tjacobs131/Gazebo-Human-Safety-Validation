import os
from ament_index_python.packages import get_package_share_directory
import launch
import launch.actions
import launch.events
import launch_ros

def monitor_and_relaunch():
    pkg_share = get_package_share_directory('validate')
    hunav_pkg_share = get_package_share_directory('hunav_evaluator')
    validate_launch_file = os.path.join(pkg_share, 'launch/run_scenarios.launch.py')
    goals_file = os.path.join(pkg_share, 'params/goals.yaml')
    config_file = os.path.join(hunav_pkg_share, 'config/agents.yaml')

    while True:
        pass
        

if __name__ == '__main__':
    monitor_and_relaunch()