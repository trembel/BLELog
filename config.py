"""
config.py
Configuration Options.

BLELog - Philipp Schilk, 2022
PBL, ETH Zuerich
---------------------------------
"""
from blelog.Configuration import Configuration, Characteristic, TUI_Mode
from char_decoders import *

config = Configuration(
    # ======================= Devices ============================

    # Connect via address:
    # A list of addresses that BLELog will attempt to connect to:
    connect_device_adrs=[
        # 'E3:11:20:62:5D:3F',
        'EB:E5:31:BF:2E:B5',
    ],

    # Connect via device name:
    # A list of regexes. If a device's name matches any of the
    # regexes below, BLELog will attempt to connect to it:
    connect_device_name_regexes=[
        # r'SmartPatch'
    ],


    # Device nicknames:
    # An (optional) alias to identify a given address by.
    # Used for status logging, TUI information, and file names.
    # If provided, it has to be unique.
    device_aliases={
        'EB:E5:31:BF:2E:B5': 'SP-Case',
        'E3:11:20:62:5D:3F': 'SP-NoCase'
    },

    # Characteristics:
    # The list of characteristics that BLELog should subscribe to.
    characteristics=[
        Characteristic(
            # A name to identify the characteristics by:
            # Has to be unique.
            name='ppg_red',

            # UUID:
            # Has to be unique.
            uuid='182281a8-153a-11ec-82a8-0242ac130001',

            # Timeout (in seconds) for this characteristics.:
            # If no notifications are received after this amount
            # of time, the connection is closed.
            # Set to 'None' to disable.
            timeout=3,

            # The data decoder function.
            # Produces a list data-rows from the received bytearray
            # Defined in char_decoders.py
            data_decoder=decode_ppg,

            # Column names for the information returned by
            # the decoder function:
            column_headers=['index', 'ppg red']

        ),

        Characteristic(
            name='ppg_ir',
            uuid='182281a8-153a-11ec-82a8-0242ac130002',
            timeout=3,
            column_headers=['index', 'ppg ir'],
            data_decoder=decode_ppg
        ),

        Characteristic(
            name='ppg_green',
            uuid='182281a8-153a-11ec-82a8-0242ac130003',
            timeout=3,
            column_headers=['index', 'ppg green'],
            data_decoder=decode_ppg
        ),

        Characteristic(
            name='temp',
            uuid='18095c47-81d2-44e5-a350-aef131810001',
            timeout=50,
            column_headers=['index', 'temp'],
            data_decoder=decode_temp
        ),

        Characteristic(
            name='qvar',
            uuid='d4eb1a81-2444-4d16-993e-4d28fe2c0001',
            timeout=3,
            column_headers=['index', 'qvar'],
            data_decoder=decode_acc_gyr_qvar
        ),

        Characteristic(
            name='acc_x',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560001',
            timeout=3,
            column_headers=['index', 'acc x'],
            data_decoder=decode_acc_gyr_qvar
        ),
        Characteristic(
            name='acc_y',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560002',
            timeout=3,
            column_headers=['index', 'acc y'],
            data_decoder=decode_acc_gyr_qvar
        ),
        Characteristic(
            name='acc_z',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560003',
            timeout=3,
            column_headers=['index', 'acc z'],
            data_decoder=decode_acc_gyr_qvar
        ),

        Characteristic(
            name='gyro_x',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560011',
            timeout=3,
            column_headers=['index', 'gyro x'],
            data_decoder=decode_acc_gyr_qvar
        ),
        Characteristic(
            name='gyro_y',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560012',
            timeout=3,
            column_headers=['index', 'gyro y'],
            data_decoder=decode_acc_gyr_qvar
        ),
        Characteristic(
            name='gyro_z',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560013',
            timeout=3,
            column_headers=['index', 'gyro z'],
            data_decoder=decode_acc_gyr_qvar
        )
    ],

    # ================ Connection Parameters =====================
    # Maximum number of simultaneously active connections:
    max_active_connections=2,

    # Maximum time an establishing a connection can take before being aborted:
    connection_timeout_hard=30,

    # Maximum time the scan performed during a connection can take before
    # being aborted:
    # (This is a bleak parameter, and is not documented very well. Sorry.)
    connection_timeout_scan=20,

    # Maximum number of simultaneous connection attempts:
    # Anything higher than one sometimes causes instability.
    max_simultaneous_connection_attempts=1,

    # Initial Characteristic Timeout:
    # An additional amount of time (in seconds) allowed in addition to the
    # characteristic timeout for the first notification.
    initial_characteristic_timeout=10,

    # Manager Interval:
    # Time in seconds between connection manager attempting to
    # create new connections
    mgr_interval=1,

    # ================== Scanner Parameters ======================
    # Time, in seconds, a scan should last:
    # Increasing this may help if devices are not being discovered:
    scan_duration=1.5,

    # Time, in seconds, to pause between scans:
    scan_cooldown=0.1,

    # Last-seen timeout:
    # BLElog will only attempt to connect to a device if it has been
    # recently seen by the scanner. This is the time (in seconds) that a
    # device will be marked as 'recently seen' after being seen.
    seen_timeout=20,

    # ================== Consumer Settings ======================
    # Enable/disable logging of data to CSV files:
    log2csv_enabled=True,

    # CSV output folder name:
    # IMPORTANT: Make sure this folder exists, otherwise logging will
    # fail. BLElog will *not* attempt to create it!
    log2csv_folder_name="output_csv",

    # Automatically open the data plot GUI on startup:
    # Useful in 'CONSOLE' tui mode, as the plotter cannot
    # be manually opened.
    plotter_open_by_default=True,

    # Shut down BLElog when the plot GUI is closed:
    # Not recommended. This will stop BLElog if plotting fails
    # for any reason. Useful during testing/in CONSOLE mode.
    plotter_exit_on_plot_close=False,

    # ================== General Settings ======================

    # Text file name for status log output:
    # Set to 'None' to disable.
    log_file='log.txt',

    # Turn the TUI into plain ASCII:
    # Much less fun, much more compatible.
    plain_ascii_tui=False,

    # TUI Mode:
    # CURSES: Fancy dashboard
    # CONSOLE: log-only console output
    tui_mode=TUI_Mode.CURSES,

    # CURSE TUI update interval (in seconds):
    curse_tui_interval=0.1
)
