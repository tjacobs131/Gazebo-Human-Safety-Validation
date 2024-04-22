import pandas as pd
import matplotlib.pyplot as plt

# Read the data
data = pd.read_csv('metrics_steps_1.txt', delimiter='\t')
time_stamps = data['time_stamps']
avg_distance_to_closest_person = data['avg_distance_to_closest_person']
avg_robot_linear_speed = data['avg_robot_linear_speed']

fig, ax1 = plt.subplots()

# Plot the average distance to the closest person
ax1.plot(time_stamps, avg_distance_to_closest_person, color='blue', label='Average Distance to Closest Person')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Distance (m)', color='blue')
ax1.tick_params('y', colors='blue')

# Create second y-axis for the robot's speed
ax2 = ax1.twinx()
ax2.plot(time_stamps, avg_robot_linear_speed, color='red', label='Average Robot Linear Speed')
ax2.set_ylabel('Speed (m/s)', color='red')
ax2.tick_params('y', colors='red')

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
lines = lines1 + lines2
labels = labels1 + labels2
ax1.legend(lines, labels, loc='upper left')

plt.show()