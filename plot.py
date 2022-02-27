"""
plot.py
The matplotlib plotting script to render the live data display.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------

The function plot(...) defined below is called by BLELog to display a live
graph of the data received.

If the data you want to plot changes, you will have to update this file.

The address of the device whose data should be plotted is also defined here.

A basic overview:

Data arrives via the process-safe and thread-safe queue 'data_queue' in the 
form of NotifData objects:

    @dataclass
    class NotifData:
        device_adr: str                  # Bluetooth address
        device_name_repr: str            # Alias, Device Name, or address
        characteristic: Characteristic   # The characteristic that received this
                                         # data (as defined in config.py)
        data: List[List[Any]]            # The output of the decoder function
                                         # (as defined in char_decoders.py and
                                         # set in config.py)

This function then does the following:
    
    - Set up a matplotlib plot
    - Set up some deques to hold the most recent data
    - Set up a matplotlib plot
    - define the function 'animate', which gets called by
      matplotlib repeatedly to update the plot.

animate(_) in turn does the following:

    - Get data from data_queue, and send it to the correct deque
    - Clear the plot
    - Re-draw the plot with the most recent data.

An important note:
Multi-threading in python is a whole can of worms.
(See 'https://en.wikipedia.org/wiki/Global_interpreter_lock')

Matplotlib cannot run in any thread but the main one - and even
if it could, the GIL-related limitations of python would likely cause
it to interfere with reliable data reception.

To get around this, BLELog runs this function (and hence matplotlib) in
a *completely separate* python interpreter. This means that this function
*cannot* directly access any of the internal state of BLELog.

It's only means of communication are:

    data_queue: A process- and thread-safe queue where data arrives.

    getLogger('log'): A logger that can be used for debug output - It too
    gets re-routed back to the main BLELog process using a queue.

This keeps things separate, allows matplotlib to run in its own process,
and avoids it from interfering with data logging.
"""

import logging
import multiprocessing as mp
import queue
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from blelog.ConsumerMgr import NotifData
from blelog.Util import normalise_adr


def plot(data_queue: mp.Queue):
    # If you want to print anything, don't use print(..) -
    # Use the logger:
    # log = logging.getLogger('log')
    # log.info('Helllooooooo wooooorld!')

    # To keep things simple, let's only plot data from a specific device
    # Note: normalise_adr makes sure the address is in the same format
    # used in blelog
    device_adr = normalise_adr('EB:E5:31:BF:2E:B5')

    # Setup plot with 5 subplots:
    fig1, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5)
    axs = [ax1, ax2, ax3, ax4, ax5]

    # Setup deques to hold data for each characteristic:
    # 'maxlen' controls the maximum number of data points shown.
    data_dqs = {
        'ppg_red': deque(maxlen=300),
        'ppg_ir': deque(maxlen=300),
        'ppg_green': deque(maxlen=300),

        'temp': deque(maxlen=300),
        'qvar': deque(maxlen=300),

        'acc_x': deque(maxlen=300),
        'acc_y': deque(maxlen=300),
        'acc_z': deque(maxlen=300),

        'gyro_x': deque(maxlen=300),
        'gyro_y': deque(maxlen=300),
        'gyro_z': deque(maxlen=300)
    }

    # Animation function called repeatedly by matplotlib.
    # Grabs data from the input queues and pushes it to the correct
    # deque before updating the plot.
    def animate(_):
        # Grab as much data from the input queue as possible:
        while True:
            try:
                # Get a NotifData object:
                notif_data = data_queue.get_nowait()  # type: NotifData

                if notif_data.device_adr != device_adr:
                    continue

                # Put it into the correct deque:
                # Note: this relies on the queue key in data_dqs above
                # to be the same as the characteristic name in config.py
                dq = data_dqs.get(notif_data.characteristic.name, None)
                if dq is not None:
                    for entry in notif_data.data:
                        dq.append(entry[1])

            except queue.Empty:
                break

        # Clear
        for ax in axs:
            ax.clear()

        ax1.set_title("PPG")
        ax2.set_title("Accelerometer")
        ax3.set_title("Gyro")
        ax4.set_title("QVAR")
        ax5.set_title("Temperature")

        # set data
        ax1.plot(data_dqs['ppg_red'], linewidth=0.5, label="red")
        # ax1.plot(data_dqs['ppg_ir'], linewidth=0.5, label="ir")
        # ax1.plot(data_dqs['ppg_green'], linewidth=0.5, label="green")
        ax1.legend(loc="upper left")

        ax2.plot(data_dqs['acc_x'], linewidth=0.5, label="x")
        ax2.plot(data_dqs['acc_y'], linewidth=0.5, label="y")
        ax2.plot(data_dqs['acc_z'], linewidth=0.5, label="z")
        ax2.legend(loc="upper left")

        ax3.plot(data_dqs['gyro_x'], linewidth=0.5, label="x")
        ax3.plot(data_dqs['gyro_y'], linewidth=0.5, label="y")
        ax3.plot(data_dqs['gyro_z'], linewidth=0.5, label="z")
        ax3.legend(loc="upper left")

        ax4.plot(data_dqs['qvar'], linewidth=0.5)

        ax5.plot(data_dqs['temp'], linewidth=0.5)

        fig1.tight_layout()

    # Start plot
    _ = FuncAnimation(fig1, animate)
    plt.show()
