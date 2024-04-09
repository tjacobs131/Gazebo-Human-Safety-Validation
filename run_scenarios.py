import os
import unittest
import ament_index_python
import launch
import launch.actions
import launch_testing
import launch_testing.actions
from launch_testing.asserts import assertSequentialStdout
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import pytest

@pytest.mark.launch_test
def generate_test_description():
    # Define the list of parameter dictionaries
    param_sets = [
        {'goals': '/path/to/goals1.yaml', 'configuration_file': 'agents1.yaml'},
        {'goals': '/path/to/goals2.yaml', 'configuration_file': 'agents2.yaml'},
        # Add more parameter sets as needed
    ]

    launch_descriptions = []
    for params in param_sets:
        pkg_share = ament_index_python.get_package_share_directory('validate')

        validate = IncludeLaunchDescription(
            PythonLaunchDescriptionSource([pkg_share, '/launch/validate.launch.py']),
            launch_arguments=[('goals', params['goals']), ('configuration_file', params['configuration_file'])],
        )

        launch_descriptions.append(launch_testing.actions.ReadyToTest())

        launch_descriptions.append(validate)


    ld = LaunchDescription(launch_descriptions)
    return ld, {}

class TestValidate(unittest.TestCase):
    def test_validate(self, proc_output, dut_process):
        with assertSequentialStdout(proc_output, dut_process) as cm:
            cm.assertInStdout('Shutting down...')

        launch_testing.actions.Shutdown()
