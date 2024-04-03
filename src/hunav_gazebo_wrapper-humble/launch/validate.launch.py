from os import path
from os import environ
from os import pathsep
import os
from scripts import GazeboRosPaths
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (IncludeLaunchDescription, SetEnvironmentVariable, 
                            DeclareLaunchArgument, ExecuteProcess, Shutdown, 
                            RegisterEventHandler, TimerAction, LogInfo)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (PathJoinSubstitution, LaunchConfiguration, 
                            PythonExpression, EnvironmentVariable)
from launch_ros.actions import Node
from launch.actions import TimerAction
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import (OnExecutionComplete, OnProcessExit,
                                OnProcessIO, OnProcessStart, OnShutdown)

def generate_launch_description():

    # to activate the use of nvidia gpu
    use_nvidia_gpu = [
        '__NV_PRIME_RENDER_OFFLOAD=1 ',
        '__GLX_VENDOR_LIBRARY_NAME=nvidia ',
    ]

    robot_name_in_model = 'pmb2'

    # Pose where we want to spawn the robot
    spawn_x_val = '0.0'
    spawn_y_val = '0.0'
    spawn_z_val = '1.3'
    spawn_yaw_val = '0.00'

    pkg_gazebo_ros = FindPackageShare(package='gazebo_ros').find('gazebo_ros')
    # Set the path to this package.
    pkg_share = FindPackageShare(package='hunav_gazebo_wrapper').find('hunav_gazebo_wrapper')
    
    default_urdf_model_path = os.path.join(pkg_share, 'models/ceres_alpha.urdf')

    joystick_config = FindPackageShare(package='teleop_twist_joy').find('teleop_twist_joy')
    joystick_config = os.path.join(joystick_config, 'config/xbox.config.yaml') 

    goal_params = DeclareLaunchArgument(
        'goals',
        description='Path to the goal configuration file')
    
    goals_config = LaunchConfiguration('goals')

    # World generation parameters
    urdf_model = LaunchConfiguration('urdf_model')
    world_file_name = LaunchConfiguration('base_world')
    gz_obs = LaunchConfiguration('use_gazebo_obs')
    rate = LaunchConfiguration('update_rate')
    robot_name = LaunchConfiguration('robot_name')
    global_frame = LaunchConfiguration('global_frame_to_publish')
    use_navgoal = LaunchConfiguration('use_navgoal_to_start')
    ignore_models = LaunchConfiguration('ignore_models')

    # agent configuration file
    agent_conf_file = PathJoinSubstitution([
        FindPackageShare('hunav_agent_manager'),
        'config',
        LaunchConfiguration('configuration_file')
    ])

    # Read the yaml file and load the parameters
    hunav_loader_node = Node(
        package='hunav_agent_manager',
        executable='hunav_loader',
        output='screen',
        parameters=[agent_conf_file]
    )

    # world base file
    world_file = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'worlds',
        world_file_name
    ])

    # the node looks for the base_world file in the directory 'worlds'
    # of the package hunav_gazebo_plugin direclty. So we do not need to 
    # indicate the path
    hunav_gazebo_worldgen_node = Node(
        package='hunav_gazebo_wrapper',
        executable='hunav_gazebo_world_generator',
        output='screen',
        parameters=[{'base_world': world_file},
        {'use_gazebo_obs': gz_obs},
        {'update_rate': rate},
        {'robot_name': robot_name},
        {'global_frame_to_publish': global_frame},
        {'use_navgoal_to_start': use_navgoal},
        {'ignore_models': ignore_models}]
        #arguments=['--ros-args', '--params-file', conf_file]
    )

    ordered_launch_event = RegisterEventHandler(
        OnProcessStart(
            target_action=hunav_loader_node,
            on_start=[
                LogInfo(msg='HunNavLoader started, launching HuNav_Gazebo_world_generator after 2 seconds...'),
                TimerAction(
                    period=2.0,
                    actions=[hunav_gazebo_worldgen_node],
                )
            ]
        )
    )

    # Then, launch the generated world in Gazebo 
    my_gazebo_models = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'models',
    ])

    config_file_name = 'params.yaml' 
    config_file = path.join(pkg_share, 'launch', config_file_name)
    
    model, plugin, media = GazeboRosPaths.get_paths()
    #print('model:', model)

    if 'GAZEBO_MODEL_PATH' in environ:
        model += pathsep+environ['GAZEBO_MODEL_PATH']
    if 'GAZEBO_PLUGIN_PATH' in environ:
        plugin += pathsep+environ['GAZEBO_PLUGIN_PATH']
    if 'GAZEBO_RESOURCE_PATH' in environ:
        media += pathsep+environ['GAZEBO_RESOURCE_PATH']


    env = {
        'GAZEBO_MODEL_PATH': model,
        'GAZEBO_PLUGIN_PATH': plugin,
        'GAZEBO_RESOURCE_PATH': media
    }
    print('env:', env)

    set_env_gazebo_model = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH', 
        value=[EnvironmentVariable('GAZEBO_MODEL_PATH'), my_gazebo_models]
    )
    set_env_gazebo_resource = SetEnvironmentVariable(
        name='GAZEBO_RESOURCE_PATH', 
        value=[EnvironmentVariable('GAZEBO_RESOURCE_PATH'), my_gazebo_models]
    )
    set_env_gazebo_plugin = SetEnvironmentVariable(
        name='GAZEBO_PLUGIN_PATH', 
        value=[EnvironmentVariable('GAZEBO_PLUGIN_PATH'), plugin]
    )

    # the world generator will create this world
    # in this path
    world_path = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'worlds',
        'generatedWorld.world'
    ])

    # Gazebo server
    gzserver_cmd = [
        #use_nvidia_gpu,
        'gzserver ',
        #'--pause ',
         world_path, 
        '-s ', 'libgazebo_ros_init.so',
        '-s ', 'libgazebo_ros_factory.so',
        '-s ', 'libgazebo_ros_state.so',
        '--verbose',
        '--ros-args',
        '--params-file', config_file,
    ]

    # Gazebo client
    gzclient_cmd = [
        use_nvidia_gpu,
        'gzclient',
        '--verbose'
    ]

    gzserver_process = ExecuteProcess(
        cmd=gzserver_cmd,
        output='screen',
        shell=True,
        on_exit=Shutdown(),
    )

    gzclient_process = ExecuteProcess(
        cmd=gzclient_cmd,
        output='screen',
        shell=True,
        on_exit=Shutdown(),
    )

    # Do not launch Gazebo until the world has been generated
    ordered_launch_event2 = RegisterEventHandler(
        OnProcessStart(
            target_action=hunav_gazebo_worldgen_node,
            on_start=[
                LogInfo(msg='GenerateWorld started, launching Gazebo after 2 seconds...'),
                TimerAction(
                    period=2.0,
                    actions=[gzserver_process, gzclient_process],
                )
            ]
        )
    )

    # hunav_manager node
    hunav_manager_node = Node(
        package='hunav_agent_manager',
        executable='hunav_agent_manager',
        name='hunav_agent_manager',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )
    
    urdf_path = os.path.join(pkg_share + "/models/ceres_alpha.urdf")
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{'robot_description': robot_desc}],
    )

    metrics_file = PathJoinSubstitution([
        FindPackageShare('hunav_evaluator'),
        'config',
        LaunchConfiguration('metrics_file')
    ])

    hunav_evaluator_node = Node(
        package='hunav_evaluator',
        executable='hunav_evaluator_node',
        output='screen',
        parameters=[metrics_file]
    )

    hunav_rviz2_package = get_package_share_directory('hunav_rviz2_panel')

    hunav_rviz2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(hunav_rviz2_package + '/launch/hunav_rviz2_launch.py'),
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(pkg_share + '/launch/slam.launch.py')
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(pkg_share + '/launch/nav2_bringup.launch.py')
    )

    odometry_readout = TimerAction(
        period=7.0,
        actions=[
            ExecuteProcess(
                cmd=['gnome-terminal', '--geometry=60x24+2560+0', '--',
                    'ros2', 'run', 
                    'odometry_readout', 'odometry_readout_node'],
                name='odometry_readout',
                
                output='screen'
            )
        ]
    )

    simulation_bridge = Node(
        package='simulation_bridge',
        executable='simulation_bridge',
        name='simulation_bridge',
        parameters=[{"params_file": goals_config}],
        output='screen'
    )
    
    joy_node = Node(
        package='joy', executable='joy_node', name='joy_node',
        parameters=[{
            'dev': '/dev/input/js0',
            'deadzone': 0.1,
            'autorepeat_rate': 30.0,
        }]
    )

    teleop_node = Node(
        package='teleop_twist_joy', 
        executable='teleop_node',
        name='teleop_twist_joy_node', 
        parameters=[joystick_config],
    )

    # Launch the robot
    spawn_entity_cmd = Node(
        package='gazebo_ros', 
        executable='spawn_entity.py',
        arguments=['-entity', robot_name_in_model, 
                   '-file', default_urdf_model_path,
                        '-x', spawn_x_val,
                        '-y', spawn_y_val,
                        '-z', spawn_z_val,
                        '-Y', spawn_yaw_val],
                        output='screen')
    
    pmb2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(pkg_share + '/launch/pmb2_pal.launch.py')
    )

    # DO NOT Launch this if any robot localization is launched
    static_tf_node = Node(
        package = "tf2_ros", 
        executable = "static_transform_publisher",
        output='screen',
        arguments = ['0', '0', '0', '0', '0', '0', 'map', 'odom']
        # other option: arguments = "0 0 0 0 0 0 pmb2 base_footprint".split(' ')
    )

      # Declare the launch arguments  
    declare_urdf_model_path_cmd = DeclareLaunchArgument(
        name='urdf_model', 
        default_value=default_urdf_model_path, 
        description='Absolute path to robot urdf file')

    declare_agents_conf_file = DeclareLaunchArgument(
        'configuration_file',
        description='Specify configuration file name in the cofig directory'
    )

    declare_metrics_conf_file = DeclareLaunchArgument(
        'metrics_file', default_value='metrics.yaml',
        description='Specify the name of the metrics configuration file in the cofig directory'
    )

    declare_arg_world = DeclareLaunchArgument(
        'base_world', default_value='simple.world',
        description='Specify world file name'
    )
    declare_gz_obs = DeclareLaunchArgument(
        'use_gazebo_obs', default_value='true',
        description='Whether to fill the agents obstacles with closest Gazebo obstacle or not'
    )
    declare_update_rate = DeclareLaunchArgument(
        'update_rate', default_value='100.0',
        description='Update rate of the plugin'
    )
    declare_robot_name = DeclareLaunchArgument(
        'robot_name', default_value='pmb2',
        description='Specify the name of the robot Gazebo model'
    )
    declare_frame_to_publish = DeclareLaunchArgument(
        'global_frame_to_publish', default_value='map',
        description='Name of the global frame in which the position of the agents are provided'
    )
    declare_use_navgoal = DeclareLaunchArgument(
        'use_navgoal_to_start', default_value='false',
        description='Whether to start the agents movements when a navigation goal is received or not'
    )
    declare_ignore_models = DeclareLaunchArgument(
        'ignore_models', default_value='ground_plane',
        description='list of Gazebo models that the agents should ignore as obstacles as the ground_plane. Indicate the models with a blank space between them'
    )
    declare_arg_verbose = DeclareLaunchArgument(
        'verbose', default_value='true',
        description='Set "true" to increase messages written to terminal.'
    )

    ld = LaunchDescription()

    # set environment variables
    ld.add_action(set_env_gazebo_model)
    ld.add_action(set_env_gazebo_resource)
    ld.add_action(set_env_gazebo_plugin)

    # Declare the launch arguments
    ld.add_action(declare_agents_conf_file)
    ld.add_action(declare_metrics_conf_file)
    ld.add_action(declare_arg_world)
    ld.add_action(declare_gz_obs)
    ld.add_action(declare_update_rate)
    ld.add_action(declare_robot_name)
    ld.add_action(declare_frame_to_publish)
    ld.add_action(declare_use_navgoal)
    ld.add_action(declare_ignore_models)
    ld.add_action(declare_arg_verbose)

    ld.add_action(hunav_rviz2)

    ld.add_action(simulation_bridge)
    ld.add_action(odometry_readout)

    ld.add_action(declare_urdf_model_path_cmd)
    ld.add_action(spawn_entity_cmd)

    ld.add_action(state_publisher)

    ld.add_action(joy_node)
    ld.add_action(teleop_node)

    # ld.add_action(slam)
    ld.add_action(nav2_bringup)

    # Generate the world with the agents
    # launch hunav_loader and the WorldGenerator
    # 2 seconds later
    ld.add_action(hunav_loader_node)
    ld.add_action(ordered_launch_event)


    # hunav behavior manager node
    ld.add_action(hunav_manager_node)
    # hunav evaluator
    ld.add_action(hunav_evaluator_node)

    # ld.add_action(static_tf_node)


    # launch Gazebo after worldGenerator 
    # (wait a bit for the world generation) 
    #ld.add_action(gzserver_process)
    ld.add_action(ordered_launch_event2)
    #ld.add_action(gzclient_process)    

    return ld

    


# Add boolean commands if true
def _boolean_command(arg):
    cmd = ['"--', arg, '" if "true" == "', LaunchConfiguration(arg), '" else ""']
    py_cmd = PythonExpression(cmd)
    return py_cmd
