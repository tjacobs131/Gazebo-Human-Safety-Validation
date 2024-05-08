from datetime import datetime
import os
from pathlib import Path
import signal
import sys
from colorama import Fore
import yaml
from ament_index_python.packages import get_package_share_directory
import launch
import launch.actions
import launch.events
import launch_ros
import subprocess
from time import sleep, time

def start():
    signal.signal(signal.SIGINT, signal_handler)

    timeout_time = 6

    kill_all()
    
    run_scenarios(timeout_time)

def run_scenarios(timeout_time):
    if len(sys.argv) > 1:
        scenario_count = int(sys.argv[1])
    else:
        scenario_count = 1
    
    pkg_share = get_package_share_directory('validate')
    validate_launch_file = 'run_scenario.launch.py'

    current_time = datetime.now()

    while True:
        scenario_file_name = 'scenario' + str(scenario_count) + '.yaml'
        goals_file = os.path.join(pkg_share, 'params/robot_goals/', scenario_file_name)
        config_file = os.path.join(pkg_share, 'params/agent_goals/', scenario_file_name)

        if not os.path.exists(goals_file) or not os.path.exists(config_file) or scenario_count < 1:
            if scenario_count == None:
                print(Fore.RED, "Scenario error")
                kill_all()
                exit(1)

            print(Fore.GREEN, "All scenarios completed.")
            exit(0)

        evaluation_timeout_timer = 0

        # Get initial position from goals file
        initial_pos_x, initial_pos_y, initial_pos_yaw = get_initial_position(goals_file)

        print(Fore.GREEN, "Launching scenario ", scenario_count, "...")
        # Pass the goals file and config file to the launch file
        proc = subprocess.Popen(['ros2', 'launch', 'validate', validate_launch_file, 'goals_file:=' + goals_file, 'configuration_file:=' + config_file,
                                 'initial_pos_x:=' + initial_pos_x,
                                 'initial_pos_y:=' + initial_pos_y,
                                 'initial_pos_yaw:=' + initial_pos_yaw], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            scenario_count = monitor_scenario_completion(proc, evaluation_timeout_timer, timeout_time, scenario_count, current_time)
        except Exception as e:
            print(Fore.RED, "Error: ", e)
            print(Fore.RED, "Killing...")
            proc.kill()
            proc.wait()  # Wait for the process to terminate

def get_initial_position(goals_file):
    print(goals_file)
    with open(goals_file, 'r') as file:
        config = yaml.safe_load(file)
        config = config["/simulation_bridge"]["ros__parameters"]
        initial_pos_x = config["init_pos_x"]
        initial_pos_y = config["init_pos_y"]
        initial_pos_yaw = config["init_pos_yaw"]

    return str(initial_pos_x), str(initial_pos_y), str(initial_pos_yaw)

def monitor_scenario_completion(proc, evaluation_timeout_timer, timeout_time, scenario_count, current_time):
    while True:
        line = proc.stdout.readline()
        if not line:
            poll = proc.poll()
            if poll is not None:
                # Process has terminated
                if poll == 0:
                    print(Fore.GREEN, "Scenario completed successfully.")
                else:
                    print(Fore.RED, "Scenario failed with exit code ", poll)
                    print(Fore.GREEN, "Launching same scenario...")
                return scenario_count
        
        line = line.decode('utf-8').strip()

        print(Fore.WHITE, line)

        if 'Calling evaluation service...' in line:
            print('Waiting for evaluation to finish...')
            evaluation_timeout_timer = time()

        if 'Scenario failed, shutting down...' in line:
            print(Fore.RED, "Scenario failed.")
            print(Fore.GREEN, "Launching same scenario...")
            terminate_process(proc)
            return scenario_count

        elif 'Scenario complete, shutting down...' in line:
            print('Killing...')
            save_results(scenario_count, current_time)
            terminate_process(proc)
            print(Fore.GREEN, "Scenario completed successfully.")
            print(Fore.GREEN, "Launching next scenario...")
            if not sys.argv[1] == None:
                return -1
            return scenario_count + 1

        if evaluation_timeout_timer > 0 and time() - evaluation_timeout_timer > timeout_time:
            print(Fore.YELLOW, "Timeout, evaluation service likely crashed.")
            print(Fore.YELLOW, "Killing...")

            # Should relaunch with same scenario
            terminate_process(proc)
            return scenario_count

def save_results(scenario_count, current_time):
    print(Fore.GREEN, "Getting safety metrics...")

    path = Path.cwd()
    current_time_folder = current_time.strftime('%Y-%m-%d_%H-%M-%S')
    scenario_metrics_folder = os.path.join(path, "scenario_metrics", current_time_folder)
    Path(scenario_metrics_folder).mkdir(parents=True, exist_ok=True)

    scenario_metrics_file = os.path.join(scenario_metrics_folder, 'metrics_scenario' + str(scenario_count) + '.txt')
    print(Fore.YELLOW, f'Saving metrics for scenario {scenario_count} in {scenario_metrics_file}')

    with open(os.path.join(path, 'safety_metrics.txt'), 'r') as file:
        with open(scenario_metrics_file, 'w') as metrics_file:
            metrics_file.write(file.read())
            metrics_file.close()

    # Run metrics_graphing.py
    print(Fore.GREEN, "Generating graph...")
    subprocess.run(['python3', 'metrics_graphing.py'])


def terminate_process(proc):
    print(Fore.RED, "Killing...")

    proc.send_signal(signal.SIGINT)
    proc.wait()

    kill_all()

def signal_handler(sig, frame):
    print(Fore.RED, "Ctrl+C detected, killing...")
    kill_all()
    exit(0)
    

def kill_all():
    print(Fore.GREEN, "Killing existing processes and waiting...")

    sleep(1)

    # Get ros2 node list
    ros2_node_list = subprocess.run(['ros2', 'node', 'list'], stdout=subprocess.PIPE)
    ros2_node_list = ros2_node_list.stdout.decode('utf-8').split('\n')
    skip_node_timeout = 4

    print("Killing nodes...")

    for node in ros2_node_list:
        if node:
            print(Fore.GREEN, "Shutting down node: ", node)
            sleep(0.1)
            try:
                subprocess.run(['ros2', 'lifecycle', 'set', node, 'shutdown'], timeout=skip_node_timeout)
            except subprocess.TimeoutExpired:
                print(Fore.YELLOW, "Timeout, node may still be running...")
                continue

            print("Node ", node, " was shut down successfully")

    kill_process('rviz2')
    kill_process('gzserver')
    kill_process('gzclient')
    kill_process('ros2')

    subprocess.run(['ros2', 'daemon', 'stop'])

def kill_process(process_name):
    timeout_time = 4
    timeout_timer = time()
    while True:
        result = subprocess.run(['sudo', 'pkill', '-KILL', process_name])
        if result.returncode == 1:
            print(Fore.GREEN, process_name, " killed.")
            return

        if time() - timeout_timer > timeout_time:
            print(Fore.YELLOW, "Timeout, ", process_name, " may still be running.")
            return


if __name__ == '__main__':
    start()