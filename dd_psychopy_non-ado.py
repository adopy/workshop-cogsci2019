#!/usr/bin/env python3
"""
Delay discounting task implementation using staircase designs
=============================================================

This is the PsychoPy-based implementation of the delay discounting task using
ADOpy. Delay discounting (DD) task is one of the widely used psychological
tasks that measures individual differences in temporal impulsivity
(e.g., Green & Myerson, 2004; Vincent, 2016). In a typical DD task,
a participant is asked to indicate his/her preference between two options,
a smaller-sooner (SS) option or stimulus (e.g., 8 dollars now) and
a larger-later (LL) option (e.g., 50 dollars in a month).
The DD task contains four design variables: `t_ss` (delay for SS option),
`t_ll` (delay for LL option), `r_ss` (reward for SS option), and `r_ll`
(reward for LL option). By the definition, `t_ss` should be sooner than `t_ll`,
while `r_ss` should be smaller than `r_ll`.
To make the task design simpler, `t_ss` and `r_ll` are fixed to 0 (right now)
and $800, respectively; only two design variables (`r_ss` and `t_ll`) vary
throughout this implementation.

For each trial, given two options, a participant should choose one option;
the response is coded as `0` for choosing SS option and `1` for choosing LL
option. In this implementation, hyperbolic model is used to estimate the
discounting rate underlying participants' behaviors. The model contains two
parameters: `k` (discounting rate) and `tau` (choice sensitivity).

This code utilizes the staircase method that manipulates a design variable
up and down based on the participant's responses. In this implementation,
it manipulates `r_ss` up and down for six unique values of `t_ll`.
Only in order to estimate model parameters, ADOpy is used to obtain mean and
standard deviation of the posterior distribution for each parameter in every
trial. Trial-by-trial information throughout the task will be saved to the
subdirectory `task` of the current working directory.

Prerequisites
-------------
* Python 3.5 or above
* Numpy
* Pandas
* PsychoPy
* Piglet 1.3.2
* ADOpy 0.3.1
"""

###############################################################################
# Load depandancies
###############################################################################

# To handle paths for files and directories
from pathlib import Path

# Fundamental packages for handling vectors, matrices, and dataframes
import numpy as np
import pandas as pd

# An open-source Python package for experiments in neuroscience & psychology
from psychopy import core, visual, event, data, gui

# Import the basic Engine class of the ADOpy package and pre-implemented
# Task and Model classes for the delay discounting task.
from adopy import Engine
from adopy.tasks.dd import TaskDD, ModelHyp

###############################################################################
# Global variables
###############################################################################

# Path to save the output data. Currently set to the subdirectory `data` of the
# current working directory.
PATH_DATA = Path('./data')

# Variables for sizes and position of an option box in which a reward and a
# delay are shown. BOX_W means the width of a box; BOX_H means the height of
# a box; DIST_BTWN means the distance between two boxes.
BOX_W = 6
BOX_H = 6
DIST_BTWN = 8

# Configurations for text. TEXT_FONT means a font to use on text; TEXT_SIZE
# means the size of text.
TEXT_FONT = 'Arial'
TEXT_SIZE = 2

# Keys for response. KEYS_LEFT and KEYS_RIGHT contains a list of keys to
# indicate that a participant wants to choose the left or right option.
# KEYS_CONT represents a list of keys to continue to the next screen.
KEYS_LEFT = ['left', 'z', 'f']
KEYS_RIGHT = ['right', 'slash', 'j']
KEYS_CONT = ['space']

# Instruction strings. Each string indicates a script to show for each screen.
INSTRUCTION = [
    # 0 - intro
    """
This task is the delay discounting task.

On every trial, two options will be presented on the screen.

Each option has a possible reward you can earn and

a delay to obtain the reward.


Press <space> to proceed.
""",
    # 1 - intro
    """
You should choose what you prefer between two options

by pressing <f> (left option) or <j> (right option).


Press <space> to proceed.
""",
    # 2 - intro
    """
Let's do some practices to check if you understand the task.


Press <space> to start practices.
""",
    # 3 - intermission
    """
Great job. Now, Let's get into the main task.

Press <space> to start a main game.
""",
    # 4 - last
    """
You completed all the game.

Thanks for your participation.


Press <space> to end.
""",
]


###############################################################################
# Functions for the delay discounting task
###############################################################################


def convert_delay_to_str(delay):
    """Convert a delay value in a weekly unit into a human-readable string."""
    tbl_conv = {
        0: 'Now',
        0.43: 'In 3 days',
        0.714: 'In 5 days',
        1: 'In 1 week',
        2: 'In 2 weeks',
        3: 'In 3 weeks',
        4.3: 'In 1 month',
        6.44: 'In 6 weeks',
        8.6: 'In 2 months',
        10.8: 'In 10 weeks',
        12.9: 'In 3 months',
        17.2: 'In 4 months',
        21.5: 'In 5 months',
        26: 'In 6 months',
        52: 'In 1 year',
        104: 'In 2 years',
        156: 'In 3 years',
        260: 'In 5 years',
        520: 'In 10 years'
    }
    mv, ms = None, None
    for (v, s) in tbl_conv.items():
        if mv is None or np.square(delay - mv) > np.square(delay - v):
            mv, ms = v, s
    return ms


def show_instruction(inst):
    """
    Show a given instruction text to the screen and wait until the
    participant presses any key in KEYS_CONT.
    """
    global window

    text = visual.TextStim(window, inst, font=TEXT_FONT,
                           pos=(0, 0), bold=True, height=0.7, wrapWidth=30)
    text.draw()
    window.flip()

    _ = event.waitKeys(keyList=KEYS_CONT)


def show_countdown():
    """Count three before starting the main task."""
    global window

    text1 = visual.TextStim(window, text='1', pos=(0., 0.), height=2)
    text2 = visual.TextStim(window, text='2', pos=(0., 0.), height=2)
    text3 = visual.TextStim(window, text='3', pos=(0., 0.), height=2)

    text3.draw()
    window.flip()
    core.wait(1)

    text2.draw()
    window.flip()
    core.wait(1)

    text1.draw()
    window.flip()
    core.wait(1)


def draw_option(delay, reward, direction, chosen=False):
    """Draw an option with given delay and reward value."""
    global window

    pos_x_center = direction * DIST_BTWN
    pos_x_left = pos_x_center - BOX_W
    pos_x_right = pos_x_center + BOX_W
    pos_y_top = BOX_H / 2
    pos_y_bottom = -BOX_H / 2

    fill_color = 'darkgreen' if chosen else None

    # Show the option box
    box = visual.ShapeStim(window,
                           lineWidth=8,
                           lineColor='white',
                           fillColor=fill_color,
                           vertices=((pos_x_left, pos_y_top),
                                     (pos_x_right, pos_y_top),
                                     (pos_x_right, pos_y_bottom),
                                     (pos_x_left, pos_y_bottom)))
    box.draw()

    # Show the reward
    text_a = visual.TextStim(window,
                             '${:,.0f}'.format(reward),
                             font=TEXT_FONT,
                             pos=(pos_x_center, 1))
    text_a.size = TEXT_SIZE
    text_a.draw()

    # Show the delay
    text_d = visual.TextStim(window,
                             convert_delay_to_str(delay),
                             font=TEXT_FONT,
                             pos=(pos_x_center, -1))
    text_d.size = TEXT_SIZE
    text_d.draw()


def run_trial(design):
    """Run one trial for the delay discounting task using PsychoPy."""
    # Use the PsychoPy window object defined in a global scope.
    global window

    # Direction: -1 (Left - LL / Right - SS) or
    #            +1 (Left - SS / Right - LL)
    direction = np.random.randint(0, 2) * 2 - 1  # Return -1 or 1
    is_ll_on_left = int(direction == -1)

    # Draw SS and LL options using the predefined function `draw_option`.
    draw_option(design['t_ss'], design['r_ss'], -1 * direction)
    draw_option(design['t_ll'], design['r_ll'], 1 * direction)
    window.flip()

    # Wait until the participant responds and get the response time.
    timer = core.Clock()
    keys = event.waitKeys(keyList=KEYS_LEFT + KEYS_RIGHT)
    rt = timer.getTime()

    # Check if the pressed key is for the left option.
    key_left = int(keys[0] in KEYS_LEFT)

    # Check if the obtained response is for SS option (0) or LL option (1).
    response = int((key_left and is_ll_on_left) or
                   (not key_left and not is_ll_on_left))  # LL option

    # Draw two options while highlighting the chosen one.
    draw_option(design['t_ss'], design['r_ss'], -1 * direction, response == 0)
    draw_option(design['t_ll'], design['r_ll'], 1 * direction, response == 1)
    window.flip()
    core.wait(1)

    # Show an empty screen for one second.
    window.flip()
    core.wait(1)

    return is_ll_on_left, key_left, response, rt


###############################################################################
# PsychoPy configurations
###############################################################################

# Show an information dialog for task settings. You can set default values for
# number of practices or trials in the main task in the `info` object.
info = {
    'Number of practices': 5,
    'Number of trials': 20,
}
dialog = gui.DlgFromDict(info, title='Task settings')
if not dialog.OK:
    core.quit()

# Process the given information from the dialog.
n_trial = int(info['Number of trials'])
n_prac = int(info['Number of practices'])

# Timestamp for the current task session, e.g. 202001011200.
timestamp = data.getDateStr('%Y%m%d%H%M')

# Make a filename for the output data.
filename_output = 'ddt_{}.csv'.format(timestamp)

# Create the directory to save output data and store the path as path_output
PATH_DATA.mkdir(exist_ok=True)
path_output = PATH_DATA / filename_output

# Open a PsychoPy window to show the task.
window = visual.Window(size=[1440, 900], units='deg', monitor='testMonitor',
                       color='#333', screen=0, allowGUI=True, fullscr=False)

# Assign the escape key for a shutdown of the task
event.globalKeys.add(key='escape', func=core.quit, name='shutdown')

###############################################################################
# ADOpy Initialization (only for parameter estimation)
###############################################################################

# Create Task and Model for the delay discounting task.
task = TaskDD()
model = ModelHyp()

# Define a grid for 4 design variables of the delay discounting task:
#   `t_ss`, `t_ll`, `r_ss`, and `r_ll`.
# `t_ss` and `r_ll` are fixed to 'right now' (0) and $800.
# `t_ll` can vary from 3 days (0.43) to 10 years (520).
# `r_ss` can vary from $12.5 to $787.5 with an increment of $12.5.
# All the delay values are converted in a weekly unit.
grid_design = {
    't_ss': [0],
    't_ll': [0.43, 0.714, 1, 2, 3, 4.3, 6.44, 8.6, 10.8, 12.9,
             17.2, 21.5, 26, 52, 104, 156, 260, 520],
    'r_ss': np.arange(12.5, 800, 12.5),  # [12.5, 25, ..., 787.5]
    'r_ll': [800]
}

# Define a grid for 2 model parameters of the hyperbolic model:
#   `k` and `tau`.
# `k` is chosen as 50 grid points between 10^-5 and 1 in a log scale.
# `tau` is chosen as 50 grid points between 0 and 5 in a linear scale.
grid_param = {
    'k': np.logspace(-5, 0, 50),
    'tau': np.linspace(0, 5, 50)
}

# Initialize the ADOpy engine with the task, model, and grids defined above.
engine = Engine(task, model, grid_design, grid_param)

###############################################################################
# Prepare designs for the staircase method
###############################################################################

# Unique values to use for `d_ll`. For each value, the staircase method runs
# six trials with varying `r_ss` based on the participant's responses.
delays = [1, 2, 4.3, 26, 52, 156, 520]

# Amount of a change on `r_ss` to update for each trial. For trials using the
# same `d_ll` value as in the previous trial, it gets decreased into a half.
# When the new `d_ll` value is used, this `delta` value gets back to 200.
delta = 200

###############################################################################
# Main codes
###############################################################################

# Make an empty DataFrame `df_data` to store trial-by-trial information,
# with given column labels as the `columns` object.
columns = [
    'block', 'trial',
    't_ss', 't_ll', 'r_ss', 'r_ll',
    'is_ll_on_left', 'key_left', 'response', 'rt',
    'mean_k', 'mean_tau'
]
df_data = pd.DataFrame(None, columns=columns)

# -----------------------------------------------------------------------------
# Practice block (using randomly chosen designs)
# -----------------------------------------------------------------------------

# Show instruction screens (0 - 2)
show_instruction(INSTRUCTION[0])
show_instruction(INSTRUCTION[1])
show_instruction(INSTRUCTION[2])

# Show countdowns for the practice block
show_countdown()

# Run practices
for trial in range(n_prac):
    # Get a randomly chosen design for the practice block
    design = engine.get_design('random')

    # Run a trial using the design
    is_ll_on_left, key_left, response, rt = run_trial(design)

    # Append the current trial into the DataFrame
    df_data = df_data.append(pd.Series({
        'block': 'prac',
        'trial': trial + 1,
        't_ss': design['t_ss'],
        't_ll': design['t_ll'],
        'r_ss': design['r_ss'],
        'r_ll': design['r_ll'],
        'is_ll_on_left': is_ll_on_left,
        'key_left': key_left,
        'response': response,
        'rt': rt,
    }), ignore_index=True)

    # Save the current data into a file
    df_data.to_csv(path_output, index=False)

# -----------------------------------------------------------------------------
# Main block (using staircase designs)
# -----------------------------------------------------------------------------

# Show an instruction screen (3)
show_instruction(INSTRUCTION[3])

# Show countdowns for the main block
show_countdown()

# Run the main task
for trial in range(n_trial):
    if trial % 6 == 0:  # Use new `t_ll` value on every 6 trials
        # Define new design set with the new `t_ll` value.
        design = {
            't_ss': 0,
            't_ll': delays[trial // 6],
            'r_ss': 400,
            'r_ll': 800
        }
        # Reset the `delta` to 200.
        delta = 200
    else:  # Adjust `r_ss` based on the previous response
        # If a participant chose the LL option, increase `r_ss` by `delta`;
        # Otherwise, decrease `r_ss` by `delta`.
        if response == 1:
            design['r_ss'] = design['r_ss'] + delta
        else:
            design['r_ss'] = design['r_ss'] - delta
        # Cut the `delta` into half.
        delta = delta / 2

    # Run a trial using the design
    is_ll_on_left, key_left, response, rt = run_trial(design)

    # Update the engine just for parameter estimation.
    engine.update(design, response)

    # Append the current trial into the DataFrame
    df_data = df_data.append(pd.Series({
        'block': 'main',
        'trial': trial + 1,
        't_ss': design['t_ss'],
        't_ll': design['t_ll'],
        'r_ss': design['r_ss'],
        'r_ll': design['r_ll'],
        'is_ll_on_left': is_ll_on_left,
        'key_left': key_left,
        'response': response,
        'rt': rt,
        'mean_k': engine.post_mean[0],
        'mean_tau': engine.post_mean[1],
        'sd_k': engine.post_sd[0],
        'sd_tau': engine.post_sd[1],
    }), ignore_index=True)

    # Save the current data into a file
    df_data.to_csv(path_output, index=False)

# Show the last instruction screen (4)
show_instruction(INSTRUCTION[4])

# Close the PsychoPy window
window.close()
