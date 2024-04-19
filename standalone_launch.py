import os
from pathlib import Path
import signal
from colorama import Fore
from ament_index_python.packages import get_package_share_directory
import launch
import launch.actions
import launch.events
import launch_ros
import subprocess
from time import sleep, time

scenario_count = 2

def start():
    signal.signal(signal.SIGINT, signal_handler)

    timeout_time = 6
    pkg_share = get_package_share_directory('validate')
    validate_launch_file = 'run_scenario.launch.py'
    scenario_file_name = 'scenario' + str(scenario_count) + '.yaml'
    goals_file = os.path.join(pkg_share, 'params/robot_goals/', scenario_file_name)
    config_file = os.path.join(pkg_share, 'params/agent_goals/', scenario_file_name)

    kill_all()

    run_scenarios(validate_launch_file, goals_file, config_file, timeout_time)

def run_scenarios(validate_launch_file, goals_file, config_file, timeout_time):
    while True:
        evaluation_timeout_timer = 0
        sleep(1)

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

        print(Fore.WHITE, line)

        if 'Calling evaluation service...' in line:
            print('Waiting for evaluation to finish...')
            evaluation_timeout_timer = time()

        if 'Scenario failed, shutting down...' in line:
            print(Fore.RED, "Scenario failed.")
            print(Fore.GREEN, "Launching same scenario...")
            terminate_process()
            break

        elif 'Scenario complete, shutting down...' in line:
            sleep(1)
            print('Killing...')
            end_scenario(proc)
            print(Fore.GREEN, "Scenario completed successfully.")
            print(Fore.GREEN, "Launching next scenario...")
            scenario_count += 1
            break

        if evaluation_timeout_timer > 0 and time() - evaluation_timeout_timer > timeout_time:
            print(Fore.YELLOW, "Timeout, evaluation service likely crashed.")
            print(Fore.YELLOW, "Killing...")

            # Should relaunch with same scenario
            end_scenario(proc)
            break

def end_scenario(proc):
    # Get file: safety_metrics.txt
    print(Fore.GREEN, "Getting safety metrics...")

    path = Path.cwd()
    Path(os.path.join(path, "scenario_metrics")).mkdir(parents=True, exist_ok=True)

    scenario_metrics_file = os.path.join(path, 'scenario_metrics/metrics_scenario' + str(scenario_count) + '.txt')
    print(Fore.YELLOW, f'Saving metrics for scenario {scenario_count} in {scenario_metrics_file}')

    with open(os.path.join(path, 'safety_metrics.txt'), 'r') as file:
        with open(os.path.join(path, scenario_metrics_file), 'w') as metrics_file:
            metrics_file.write(file.read())
            metrics_file.write('\n\n\n')
            metrics_file.close()
    
    terminate_process()


def terminate_process():
    shutdown_timeout_timer = time()
    shutdown_timeout_time = 15

    print(Fore.RED, "Killing...")

    kill_all()

def signal_handler(sig, frame):
    print(Fore.RED, "Ctrl+C detected, killing...")
    kill_all()
    exit(0)
    

def kill_all():
    print(Fore.GREEN, "Killing existing processes and waiting...")
    subprocess.run(['killall', '-w', '-KILL', 'gzserver'])
    subprocess.run(['killall', '--process-group', '-w', '-KILL', 'ros2'])
    subprocess.run(['killall', '-w', '-KILL', 'rviz2'])
    subprocess.run(['killall', '-w', '-KILL', 'gzclient'])
    sleep(2)


if __name__ == '__main__':
    start()