import os
from colorama import Fore
from ament_index_python.packages import get_package_share_directory
import launch
import launch.actions
import launch.events
import launch_ros
import subprocess
from time import sleep, time

def monitor_and_relaunch():
    timeout_time = 6
    pkg_share = get_package_share_directory('validate')
    validate_launch_file = 'run_scenario.launch.py'
    goals_file = os.path.join(pkg_share, 'params/robot_goals/scenario1_baseline.yaml')
    config_file = os.path.join(pkg_share, 'params/agent_goals/scenario1.yaml')

    run_scenarios(validate_launch_file, goals_file, config_file, timeout_time)

def run_scenarios(validate_launch_file, goals_file, config_file, timeout_time):
    while True:
        evaluation_timeout_timer = 0

        # Kill any existing gzserver and gzclient
        print(Fore.GREEN, "Killing existing processes and waiting...")
        subprocess.run(['killall', '-w', '-KILL', 'gzserver'])
        subprocess.run(['killall', '-w', '-KILL', 'gzclient'])
        # subprocess.run(['killall', '--process-group', '-w', '-KILL', 'ros2'])

        sleep(2)

        print("Launching scenario")
        # Pass the goals file and config file to the launch file
        proc = subprocess.Popen(['ros2', 'launch', 'validate', validate_launch_file, 'goals_file:=' + goals_file, 'configuration_file:=' + config_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            monitor_scenario_completion(proc, evaluation_timeout_timer, timeout_time)
        except Exception as e:
            print(Fore.RED, "Error: ", e)
            print(Fore.RED, "Killing...")
            proc.terminate()
            proc.wait()  # Wait for the process to terminate

def monitor_scenario_completion(proc, evaluation_timeout_timer, timeout_time):
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
                break

        line = line.decode('utf-8').strip()
        print(line)

        if 'Calling evaluation service...' in line:
            print('Waiting for evaluation to finish...')
            evaluation_timeout_timer = time()

        elif 'Scenario complete, shutting down...' in line:
            sleep(1)
            print('Killing...')
            terminate_process(proc)
            break

        if evaluation_timeout_timer > 0 and time() - evaluation_timeout_timer > timeout_time:
            print(Fore.YELLOW, "Timeout, evaluation service likely crashed.")
            print(Fore.YELLOW, "Killing...")

            # Should relaunch with same scenario
            terminate_process(proc)
            break

def terminate_process(proc):
    shutdown_timeout_timer = time()
    shutdown_timeout_time = 10

    print(Fore.RED, "Killing...")
    proc.send_signal(subprocess.signal.SIGINT)
    while proc.poll() is None:
        sleep(1)
        proc.send_signal(subprocess.signal.SIGINT)
        if time() - shutdown_timeout_timer > shutdown_timeout_time:
            print(Fore.RED, "Failed to shutdown, killing...")
            proc.send_signal(subprocess.signal.SIGTERM)
            break

if __name__ == '__main__':
    monitor_and_relaunch()