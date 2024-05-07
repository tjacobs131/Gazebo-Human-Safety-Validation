import os
import sys
import subprocess
from ament_index_python import get_package_share_directory
from launch import LaunchContext, LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.event_handlers import OnProcessStart

def generate_launch_description():

    robot_name_in_model = 'ceres_alpha'

    default_urdf_model_path = os.path.join(get_package_share_directory("validate"), 'models/ceres_alpha.urdf')

    initial_pos_x_arg = DeclareLaunchArgument(
        name='initial_pos_x',
        default_value='0.0',
        description='Initial position x'
    )

    initial_pos_y_arg = DeclareLaunchArgument(
        name='initial_pos_y',
        default_value='0.0',
        description='Initial position y'
    )

    initial_pos_yaw_arg = DeclareLaunchArgument(
        name='initial_pos_yaw',
        default_value='0.0',
        description='Initial position yaw'
    )

    # Use arguments to set the initial position of the robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', robot_name_in_model, 
            '-x', LaunchConfiguration('initial_pos_x'), 
            '-y', LaunchConfiguration('initial_pos_y'),
            '-z', '0.91',
            '-Y', LaunchConfiguration('initial_pos_yaw'),
            '-file', LaunchConfiguration('urdf_model')],
        output='screen'
    )
    
    # Declare the launch arguments  
    declare_urdf_model_path_cmd = DeclareLaunchArgument(
        name='urdf_model', 
        default_value=default_urdf_model_path, 
        description='Absolute path to robot urdf file')
    
    with open(default_urdf_model_path, 'r') as infp:
        robot_desc = infp.read()

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}]
    )
    
    ld = LaunchDescription()
    ld.add_action(initial_pos_x_arg)
    ld.add_action(initial_pos_y_arg)
    ld.add_action(initial_pos_yaw_arg)
    ld.add_action(declare_urdf_model_path_cmd)
    ld.add_action(spawn_entity)

    ld.add_action(state_publisher)

    return ld