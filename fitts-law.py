import pyglet
import math
import time

#pyglet window
window = pyglet.window.Window(1440, 960)
batch = pyglet.graphics.Batch()

#variables
targets = []
click_times = []
angles = []
start_time = None
trial_index = 0
num_trials = 14
    #number of circles need to be clicked
num_targets = 12    #number of circles

# Define target properties
target_radius = 20
central_radius = 150
central_x = window.width // 2
central_y = window.height // 2
highlight_color = (0, 255, 0)  #highlight color
normal_color = (255, 0, 0)     #color circle

#label on top
label = pyglet.text.Label('Click on the highlighted target',
                          font_name='Times New Roman',
                          font_size=24,
                          x=window.width // 2, y=window.height -30,
                          anchor_x='center', anchor_y='center')

#circle positions in circle shape
def generate_targets(num_targets):
    global central_radius, target_radius, window
    targets = []
    angle_step = 2 * math.pi / num_targets
    for i in range(num_targets):
        angle = i * angle_step
        x = central_x + central_radius * math.cos(angle)
        y = central_y + central_radius * math.sin(angle)
        targets.append((pyglet.shapes.Circle(x, y, target_radius, color=normal_color, batch=batch), angle))
    return targets

#create targets
targets = generate_targets(num_targets)
target_circles = [t[0] for t in targets]
angles = [t[1] for t in targets]

# Highlight the first target
current_target_index = 0
target_circles[current_target_index].color = highlight_color

# Track the last clicked target indices
last_clicked_index = None
previous_index = None

@window.event
def on_draw():
    window.clear()
    if trial_index < num_trials:
        label.draw()
        batch.draw()
    else:
        # Display results after all trials
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

            #next target
            if previous_index is None:
                next_target_index = (current_target_index + num_targets // 2) % num_targets
            else:
                next_target_index = (previous_index - 1) % num_targets
                if next_target_index == last_clicked_index:
                    next_target_index = (next_target_index - 1) % num_targets

            #set color next target
            target.color = normal_color
            current_target_index = next_target_index
            target_circles[current_target_index].color = highlight_color
            trial_index += 1

            #set start time
            start_time = time.time()

#set start time before first click
start_time = time.time()

pyglet.app.run()


