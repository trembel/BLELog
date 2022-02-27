import logging
import multiprocessing as mp
import queue
from collections import deque

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from blelog.ConsumerMgr import NotifData
from blelog.Util import normalise_adr


def plot(data_queue: mp.Queue):
    # If you want to print anything, don't use print.
    # Use this logger:
    log = logging.getLogger('log')
    # log.info('Helllooooooo wooooorld!')

    # To keep things simple, let's only plot data from a specific device
    # Note: normalise_adr makes sure the address is in the same format
    # used in blelog
    device_adr = normalise_adr('EB:E5:31:BF:2E:B5')

    # Setup plot with 5 suplots:
    fig1, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5)
    axs = [ax1, ax2, ax3, ax4, ax5]

    # Setup deques to hold data for each characterisitc:
    # 'maxlen' controls the maximum number of datapoints shown.
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
                # to be the same as the characterisitc name in config.py
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
