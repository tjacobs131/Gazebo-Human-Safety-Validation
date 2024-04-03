import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions.declare_launch_argument import DeclareLaunchArgument
from launch.actions.include_launch_description import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node  

def generate_launch_description():
    pkg_share = get_package_share_directory('hunav_gazebo_wrapper')

    goal_params = DeclareLaunchArgument(
        'goals',
        default_value=pkg_share + '/params/goals.yaml',
        description='Path to the goal configuration file')
    
    declare_agents_conf_file = DeclareLaunchArgument(
        'configuration_file', default_value='scenario1.yaml',
        description='Specify configuration file name in the config directory'
    )


    # include secondary launch file that takes in the platform argument
    validate = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([get_package_share_directory('hunav_gazebo_wrapper'), '/launch/validate.launch.py']),
        launch_arguments=[('goals', LaunchConfiguration('goals')), ('configuration_file', LaunchConfiguration('configuration_file'))],
    )

    ld = LaunchDescription()
    ld.add_action(declare_agents_conf_file)
    ld.add_action(goal_params )
    ld.add_action(validate )

    # add some other actions

    return ld