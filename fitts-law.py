import pyglet
import math
import time
import json
import random
import sys
import csv
from collections import deque
import os

# Parse command line arguments using sys.argv
if len(sys.argv) < 3:
    print("Usage: python script_name.py <participant_id> <input_device>")
    sys.exit(1)

participant_id = sys.argv[1]
input_device = sys.argv[2]

# Load configuration from file
with open('config.json') as config_file:
    config = json.load(config_file)

# Determine if mouse latency should be applied
apply_mouse_latency = input_device.lower() == "mouselatency"

# pyglet window
window = pyglet.window.Window(config['window_width'], config['window_height'])
batch = pyglet.graphics.Batch()

# Hide or show the system cursor based on input device
if apply_mouse_latency:
    window.set_mouse_visible(False)
else:
    window.set_mouse_visible(True)

# Variables
targets = []
click_times = []
angles = []
start_time = None
trial_index = 0
num_trials = config['num_trials']  # Number of trials in each run
num_targets = config['num_targets']  # Number of circles
num_restarts = config['num_restarts']  # Number of times the experiment should restart
current_restart = 0  # Current restart count
total_clicks = 0
missed_clicks = 0

# Define target properties
target_radii = config['radius']  # List of target radii
central_radii = config['distance']  # List of central radii
central_x = window.width // 2
central_y = window.height // 2
highlight_color = tuple(config['highlight_color'])  # Highlight color
normal_color = tuple(config['normal_color'])        # Normal circle color
latency = config['latency'] if apply_mouse_latency else 0  # Latency in seconds (only for mouse latency)
cursor_color = tuple(config['cursor_color'])  # Cursor color
cursor_size = config['cursor_size']  # Cursor size

# CSV file setup
csv_filename = f"fittslaw_{participant_id}.csv"
csv_exists = os.path.isfile(csv_filename)

# Open the CSV file in append mode
csv_file = open(csv_filename, mode='a', newline='')
csv_writer = csv.writer(csv_file)

# Write header if the file does not exist
if not csv_exists:
    csv_writer.writerow(['Participant ID', 'Input Device', 'Round', 'Radius', 'Distance', 'Total Clicks', 'Missed Clicks', 'Click Times'])

# Label on top to display the number of rounds
total_rounds = len(target_radii) * len(central_radii)
label = pyglet.text.Label(f'Round 1 of {total_rounds}',
                          font_name='Times New Roman',
                          font_size=24,
                          x=window.width // 2, y=window.height - 30,
                          anchor_x='center', anchor_y='center')

# Circle positions in circle shape
def generate_targets(num_targets, central_radius, target_radius):
    global central_x, central_y, normal_color, batch
    targets = []
    angle_step = 2 * math.pi / num_targets
    for i in range(num_targets):
        angle = i * angle_step
        x = central_x + central_radius * math.cos(angle)
        y = central_y + central_radius * math.sin(angle)
        targets.append((pyglet.shapes.Circle(x, y, target_radius, color=normal_color, batch=batch), angle))
    print(f"Generated {len(targets)} targets with central radius {central_radius} and target radius {target_radius}")
    return targets

def create_targets(target_radius, central_radius):
    global targets, target_circles, angles, current_restart, trial_index

    # Increment the restart count when starting a new round
    if trial_index == 0:
        current_restart += 1

    targets = generate_targets(num_targets, central_radius, target_radius)
    target_circles = [t[0] for t in targets]
    angles = [t[1] for t in targets]

# Initialize target and circle setup
current_radius_index = 0
current_distance_index = 0
current_radius = target_radii[current_radius_index]
current_distance = central_radii[current_distance_index]
create_targets(current_radius, current_distance)

# Highlight the first target
current_target_index = 0
target_circles[current_target_index].color = highlight_color

# Track the last clicked target indices
last_clicked_index = None
previous_index = None

# Queue to simulate latency in mouse position
mouse_position_queue = deque(maxlen=int(latency * 60))  # Assuming 60 FPS

@window.event
def on_mouse_motion(x, y, dx, dy):
    if apply_mouse_latency:
        # Store the actual mouse position with latency
        mouse_position_queue.append((x, y))
    else:
        # Directly use the current mouse position without latency
        process_mouse_motion(x, y)

@window.event
def on_draw():
    window.clear()
    if trial_index < num_trials:
        label.text = f'Round {current_restart} of {total_rounds}'
        label.draw()
        batch.draw()

        # Draw the delayed mouse cursor if latency is applied
        if apply_mouse_latency and mouse_position_queue:
            delayed_x, delayed_y = mouse_position_queue[0]
            pyglet.shapes.Circle(delayed_x, delayed_y, cursor_size, color=cursor_color).draw()  # Custom cursor size and color
        
    else:
        if current_restart < num_restarts:
            save_data_to_csv()
            update_combination()
            restart_experiment()
        else:
            save_data_to_csv()
            # Display results after all trials and restarts
            result_label = pyglet.text.Label('Experiment Complete',
                                             font_name='Times New Roman',
                                             font_size=24,
                                             x=window.width // 2, y=window.height // 2,
                                             anchor_x='center', anchor_y='center')
            result_label.draw()
            csv_file.close()  # Close the CSV file


@window.event
def on_mouse_press(x, y, button, modifiers):
    if apply_mouse_latency and mouse_position_queue:
        delayed_x, delayed_y = mouse_position_queue[0]
        process_mouse_press(delayed_x, delayed_y, button, modifiers)
    else:
        process_mouse_press(x, y, button, modifiers)

def process_mouse_motion(x, y):
    pass  # Implement any additional mouse motion processing if needed

def process_mouse_press(x, y, button, modifiers):
    global start_time, trial_index, current_target_index, last_clicked_index, previous_index, total_clicks, missed_clicks

    total_clicks += 1

    if trial_index < num_trials:
        target = target_circles[current_target_index]
        if math.hypot(target.x - x, target.y - y) <= target.radius:
            end_time = time.time()
            click_time = end_time - start_time
            click_times.append(click_time)

            previous_index = last_clicked_index
            last_clicked_index = current_target_index

            # Next target
            if previous_index is None:
                next_target_index = (current_target_index + num_targets // 2) % num_targets
            else:
                next_target_index = (previous_index - 1) % num_targets
                if next_target_index == last_clicked_index:
                    next_target_index = (next_target_index - 1) % num_targets

            # Set color next target
            target.color = normal_color
            current_target_index = next_target_index
            target_circles[current_target_index].color = highlight_color
            trial_index += 1

            # Set start time
            start_time = time.time()
        else:
            missed_clicks += 1


def save_data_to_csv():
    global current_restart, current_radius, current_distance, click_times, total_clicks, missed_clicks
    if click_times:
        csv_writer.writerow([participant_id, input_device, current_restart, current_radius, current_distance, total_clicks, missed_clicks, click_times])
        click_times = []  # Reset click times for the next round
        total_clicks = 0
        missed_clicks = 0

def update_combination():
    global current_radius_index, current_distance_index, current_radius, current_distance

    current_distance_index += 1
    if current_distance_index >= len(central_radii):
        current_distance_index = 0
        current_radius_index += 1
        if current_radius_index >= len(target_radii):
            current_radius_index = 0

    current_radius = target_radii[current_radius_index]
    current_distance = central_radii[current_distance_index]
    print(f"Updated combination to radius: {current_radius}, distance: {current_distance}")

def restart_experiment():
    global trial_index, current_target_index, last_clicked_index, previous_index, click_times, start_time

    trial_index = 0
    click_times = []
    last_clicked_index = None
    previous_index = None

    # Reset the targets and their colors
    create_targets(current_radius, current_distance)

    # Highlight the first target
    current_target_index = 0
    target_circles[current_target_index].color = highlight_color

    # Set start time for the new experiment run
    start_time = time.time()

# Set start time before first click
start_time = time.time()

pyglet.app.run()

# After the Pyglet event loop ends, close the CSV file
csv_file.close()

# Optionally, you can print a confirmation message or perform further analysis on the data
print(f"Experiment data saved to {csv_filename}")
