from setuptools import find_packages, setup
from glob import glob

package_name = 'validate'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/params/agent_goals', glob('params/agent_goals/*')),
        ('share/' + package_name + '/params/robot_goals', glob('params/robot_goals/*')),
        ('share/' + package_name + '/launch', glob('launch/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gtl',
    maintainer_email='t.jacobs-ab@student.fontys.nl',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
