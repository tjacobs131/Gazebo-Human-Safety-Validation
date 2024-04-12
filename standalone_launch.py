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
    evaluation_timeout_timer = 0
    shutdown_timeout_timer = 0
    timeout_time = 3

    pkg_share = get_package_share_directory('validate')
    validate_launch_file = 'run_scenario.launch.py'
    goals_file = os.path.join(pkg_share, 'params/goals.yaml')
    config_file = os.path.join(pkg_share, 'params/scenario1.yaml')

    while True:
        # Kill any existing gzserver and gzclient
        print(Fore.RED, "Killing existing processes and waiting...")
        subprocess.run(['killall', '-w', '-KILL', 'gzserver'])
        subprocess.run(['killall', '-w', '-KILL', 'gzclient'])
        subprocess.run(['killall', '-w', '-KILL', 'ros2'])
        
        sleep(2)

        print("Launching scenario")

        # Pass the goals file and config file to the launch file
        proc = subprocess.Popen(['ros2', 'launch', 'validate', validate_launch_file, 'goals_file:=' + goals_file, 'configuration_file:=' + config_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            while True:
                if evaluation_timeout_timer > 0 and time() - evaluation_timeout_timer > timeout_time:
                    print(Fore.RED, "Timeout, evaluation service likely crashed.")
                    print(Fore.RED, "Killing...")
                    proc.send_signal(subprocess.signal.SIGINT)
                    break

                line = proc.stdout.readline()
                print(line.decode('utf-8').strip())
                if not line:
                    break
                if b'Calling evaluation service...' in line:
                    print('Waiting for evaluation to finish...')
                    evaluation_timeout_timer = time()
                if b'Scenario complete, shutting down...' in line:
                    print('Killing...')
                    while(proc.poll() is None and time() - shutdown_timeout_timer < timeout_time):
                        shutdown_timeout_timer = time()
                        proc.send_signal(subprocess.signal.SIGINT)
                    continue

        except Exception as e:
            shutdown_timeout_timer = 0
            print(Fore.RED, "Error: ", e)
            print(Fore.RED, "Killing...")

            proc.send_signal(subprocess.signal.SIGKILL)
            
        sleep(2)

if __name__ == '__main__':
    monitor_and_relaunch()