import pyglet
import math
import time
import json
import random
import sys

#command line paramters
if len(sys.argv) < 3:
    print("Usage: python script_name.py <participant_id> <input_device>")
    sys.exit(1)
#parameters
participant_id = sys.argv[1]
input_device = sys.argv[2]

#open config
with open('config.json') as config_file:
    config = json.load(config_file)

# pyglet window
window = pyglet.window.Window(config['window_width'], config['window_height'])
batch = pyglet.graphics.Batch()

# variables
targets = []
click_times = []
angles = []
start_time = None
trial_index = 0
num_trials = config['num_trials']
num_targets = config['num_targets']
num_restarts = config['num_restarts']
current_restart = 0 

#target properties via config
target_radius_min = config['target_radius_min']
target_radius_max = config['target_radius_max']
central_radius_min = config['central_radius_min']
central_radius_max = config['central_radius_max']
central_x = window.width // 2
central_y = window.height // 2
highlight_color = tuple(config['highlight_color'])
normal_color = tuple(config['normal_color'])     

#labeling rounds
label = pyglet.text.Label('Round 1 of {}'.format(num_restarts + 1),
                          font_name='Times New Roman',
                          font_size=24,
                          x=window.width // 2, y=window.height - 30,
                          anchor_x='center', anchor_y='center')

# circle positions in circle
def generate_targets(num_targets, central_radius, target_radius):
    global central_x, central_y, normal_color, batch
    targets = []
    angle_step = 2 * math.pi / num_targets
    for i in range(num_targets):
        angle = i * angle_step
        x = central_x + central_radius * math.cos(angle)
        y = central_y + central_radius * math.sin(angle)
        targets.append((pyglet.shapes.Circle(x, y, target_radius, color=normal_color, batch=batch), angle))
    return targets

def create_targets():
    global targets, target_circles, angles
    targets = generate_targets(num_targets, central_radius, target_radius)
    target_circles = [t[0] for t in targets]
    angles = [t[1] for t in targets]

#random radius and distance
central_radius = random.uniform(central_radius_min, central_radius_max)
target_radius = random.uniform(target_radius_min, target_radius_max)
create_targets()

#first target
current_target_index = 0
target_circles[current_target_index].color = highlight_color

#last clicked
last_clicked_index = None
previous_index = None

@window.event
def on_draw():
    window.clear()
    if trial_index < num_trials:
        label.text = 'Round {} of {}'.format(current_restart + 1, num_restarts + 1)
        label.draw()
        batch.draw()
    else:
        if current_restart < num_restarts:
            restart_experiment()
        else:
            # Display results after all trials and restarts
            result_label = pyglet.text.Label('Experiment Complete',
                                             font_name='Times New Roman',
                                             font_size=24,
                                             x=window.width // 2, y=window.height // 2,
                                             anchor_x='center', anchor_y='center')
            result_label.draw()

@window.event
def on_mouse_press(x, y, button, modifiers):
    global start_time, trial_index, current_target_index, last_clicked_index, previous_index

    if trial_index < num_trials:
        target = target_circles[current_target_index]
        if math.hypot(target.x - x, target.y - y) <= target_radius:
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

def restart_experiment():
    global trial_index, current_restart, current_target_index, last_clicked_index, previous_index, click_times, start_time, central_radius, target_radius

    current_restart += 1
    trial_index = 0
    click_times = []
    last_clicked_index = None
    previous_index = None

    #update radius and distance
    central_radius = random.uniform(central_radius_min, central_radius_max)
    target_radius = random.uniform(target_radius_min, target_radius_max)

    #reset targets
    create_targets()

    #highlight first target
    current_target_index = 0
    target_circles[current_target_index].color = highlight_color

    #set start time for new round
    start_time = time.time()

#first start time
start_time = time.time()

pyglet.app.run()
