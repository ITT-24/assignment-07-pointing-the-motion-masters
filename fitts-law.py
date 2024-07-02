#chatgpt used for some math (circle angles) and latency for cursor

#imports
import pyglet
import math
import time
import json
import sys
import csv
from collections import deque
import os

#command line parameter
if len(sys.argv) < 3:
    print("Usage: python script_name.py <participant_id> <input_device>")
    sys.exit(1)

participant_id = sys.argv[1]
input_device = sys.argv[2]

#load config
with open('config.json') as config_file:
    config = json.load(config_file)

#check latency
apply_mouse_latency = input_device.lower() == "mouselatency"

#pyglet window
window = pyglet.window.Window(config['window_width'], config['window_height'])
batch = pyglet.graphics.Batch()

#cursor hide or show
if apply_mouse_latency:
    window.set_mouse_visible(False)
else:
    window.set_mouse_visible(True)

#variables
targets = []
click_times = []
angles = []
start_time = None
trial_index = 0
num_trials = config['num_trials'] 
num_targets = config['num_targets']  
num_restarts = config['num_restarts'] 
current_restart = 0 
total_clicks = 0
missed_clicks = 0

#target properties config
radius = config['radius']  
distance = config['distance'] 
central_x = window.width // 2
central_y = window.height // 2
highlight_color = tuple(config['highlight_color'])
normal_color = tuple(config['normal_color'])       
latency = config['latency'] if apply_mouse_latency else 0  
cursor_color = tuple(config['cursor_color'])  
cursor_size = config['cursor_size']  

#csv
csv_filename = f"fittslaw_{participant_id}.csv"
csv_exists = os.path.isfile(csv_filename)
csv_file = open(csv_filename, mode='a', newline='')
csv_writer = csv.writer(csv_file)
if not csv_exists:
    csv_writer.writerow(['Participant ID', 'Input Device', 'Round', 'Radius', 'Distance', 'Total Clicks', 'Missed Clicks', 'Click Times'])

#round label
total_rounds = len(radius) * len(distance)
label = pyglet.text.Label(f'Round 1 of {total_rounds}',
                          font_name='Times New Roman',
                          font_size=24,
                          x=window.width // 2, y=window.height - 30,
                          anchor_x='center', anchor_y='center')

#circle positions in circle shape
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

    if trial_index == 0:
        current_restart += 1

    targets = generate_targets(num_targets, central_radius, target_radius)
    target_circles = [t[0] for t in targets]
    angles = [t[1] for t in targets]

#setup targets
current_radius_index = 0
current_distance_index = 0
current_radius = radius[current_radius_index]
current_distance = distance[current_distance_index]
create_targets(current_radius, current_distance)

#first target
current_target_index = 0
target_circles[current_target_index].color = highlight_color

#last target
last_clicked_index = None
previous_index = None

# latency
mouse_position_queue = deque(maxlen=int(latency * 60)) 

@window.event
def on_mouse_motion(x, y, dx, dy):
    if apply_mouse_latency:
        #latency mouse position
        mouse_position_queue.append((x, y))
    else:
        #mouse position
        process_mouse_motion(x, y)

@window.event
def on_draw():
    window.clear()
    if trial_index < num_trials:
        label.text = f'Round {current_restart} of {total_rounds}'
        label.draw()
        batch.draw()

        #latency cursor
        if apply_mouse_latency and mouse_position_queue:
            delayed_x, delayed_y = mouse_position_queue[0]
            pyglet.shapes.Circle(delayed_x, delayed_y, cursor_size, color=cursor_color).draw()
        
    else:
        if current_restart < num_restarts:
            save_data_to_csv()
            update_combination()
            restart_experiment()
        else:
            save_data_to_csv()
            #finish label
            result_label = pyglet.text.Label('Finished',
                                             font_name='Arial',
                                             font_size=24,
                                             x=window.width // 2, y=window.height // 2,
                                             anchor_x='center', anchor_y='center')
            result_label.draw()
            csv_file.close() 


@window.event
def on_mouse_press(x, y, button, modifiers):
    if apply_mouse_latency and mouse_position_queue:
        delayed_x, delayed_y = mouse_position_queue[0]
        process_mouse_press(delayed_x, delayed_y, button, modifiers)
    else:
        process_mouse_press(x, y, button, modifiers)

def process_mouse_motion(x, y):
    pass 

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

            #next target
            if previous_index is None:
                next_target_index = (current_target_index + num_targets // 2) % num_targets
            else:
                next_target_index = (previous_index - 1) % num_targets
                if next_target_index == last_clicked_index:
                    next_target_index = (next_target_index - 1) % num_targets

            #color next target
            target.color = normal_color
            current_target_index = next_target_index
            target_circles[current_target_index].color = highlight_color
            trial_index += 1

            start_time = time.time()
        else:
            missed_clicks += 1


def save_data_to_csv():
    global current_restart, current_radius, current_distance, click_times, total_clicks, missed_clicks
    if click_times:
        csv_writer.writerow([participant_id, input_device, current_restart, current_radius, current_distance, total_clicks, missed_clicks, click_times])
        #resets
        click_times = []  
        total_clicks = 0
        missed_clicks = 0

def update_combination():
    global current_radius_index, current_distance_index, current_radius, current_distance

    current_distance_index += 1
    if current_distance_index >= len(distance):
        current_distance_index = 0
        current_radius_index += 1
        if current_radius_index >= len(radius):
            current_radius_index = 0

    current_radius = radius[current_radius_index]
    current_distance = distance[current_distance_index]

def restart_experiment():
    global trial_index, current_target_index, last_clicked_index, previous_index, click_times, start_time

    trial_index = 0
    click_times = []
    last_clicked_index = None
    previous_index = None

    #resets
    create_targets(current_radius, current_distance)
    current_target_index = 0
    target_circles[current_target_index].color = highlight_color
    start_time = time.time()

#first start
start_time = time.time()

pyglet.app.run()

csv_file.close()

