from blelog.Configuration import Configuration, Characteristic
config = Configuration(
    # ================== Scanner Settings ======================
    # Time, in seconds, a scan should last:
    # Very low scan times (even less than 1 or 2 seonds) work well under linux
    # Needs to be much higher under windows (30+)
    scan_duration=2,

    # Time, in seconds, to pause between scans:
    scan_cooldown=2,

    # Last-seen timeout:
    # Time (in seconds) that a device will be marked as 'recently_seen'
    # after being picked up by the scanner
    seen_timeout=5,

    # ================ Connection Settings =====================

    # Maximum time a connection can take before being aborted:
    connection_timeout_hard=30,

    # Maximum time the scan done during a connection can take before
    # being aborted (bleak parameter, not that well specified?)
    connection_timeout_scan=20,

    # Maximum number of simultaneous Connections:
    max_active_connections=4,

    # Maximum number of connections that can be established at the
    # same time:
    max_simulatneous_connection_attempts=1,

    # Connect device name:
    # A list of regexes that a device name can match.
    connect_device_name_regexes=[
        # r'SmartPatch'
    ],

    # Connect via address:
    connect_device_adrs=[
        'E3:11:20:62:5D:3F',
        'EB:E5:31:BF:2E:B5',
    ],

    # Device nicknames:
    # An (optional) alias to identify a given address by.
    device_aliases={
        'EB:E5:31:BF:2E:B5': 'SP-Case',
        'E3:11:20:62:5D:3F': 'SP-Naked'
    },

    # Characterisitics:
    # The list of characterisitics that should be subscribed to.
    characteristics=[
        Characteristic(
            # A nickname to identify the characteristics by:
            name='ppg_red',

            # UUID:
            uuid='182281a8-153a-11ec-82a8-0242ac130001',

            # Timeout in seconds for this characteristics.:
            # Set to 'None' to disable.
            timeout=5,

            # The data decoder function.
            # Produces a list of values from the received bytearry
            data_decoder=lambda x: x
        ),

        Characteristic(
            name='ppg_ir',
            uuid='182281a8-153a-11ec-82a8-0242ac130002',
            timeout=None,
            data_decoder=lambda x: x
        ),

        Characteristic(
            name='ppg_green',
            uuid='182281a8-153a-11ec-82a8-0242ac130003',
            timeout=None,
            data_decoder=lambda x: x
        ),

        # Characteristic(
        #     name='temp',
        #     uuid='18095c47-81d2-44e5-a350-aef131810001',
        #     timeout=None,
        #     data_decoder=lambda x: x
        # ),

        # Characteristic(
        #     name='qvar',
        #     uuid='d4eb1a81-2444-4d16-993e-4d28fe2c0001',
        #     timeout=None,
        #     data_decoder=lambda x: x
        # ),

        Characteristic(
            name='acc_x',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560001',
            timeout=None,
            data_decoder=lambda x: x
        ),
        Characteristic(
            name='acc_y',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560002',
            timeout=None,
            data_decoder=lambda x: x
        ),
        Characteristic(
            name='acc_z',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560003',
            timeout=None,
            data_decoder=lambda x: x
        ),

        Characteristic(
            name='gyro_x',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560011',
            timeout=None,
            data_decoder=lambda x: x
        ),
        Characteristic(
            name='gyro_y',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560012',
            timeout=None,
            data_decoder=lambda x: x
        ),
        Characteristic(
            name='gyro_z',
            uuid='3da22dc6-70d7-4217-9bb2-de5d79560013',
            timeout=None,
            data_decoder=lambda x: x
        )
    ],


    # Initial Characteristic Timeout:
    # An additional amount of time (in seconds) allowed in addition to the
    # Characteristic timeout for the first notification.
    initial_characterisitc_timeout=10,

    # Manager Interval:
    # Time in seconds, between connection manager running and
    # possibly attempting to create new connections
    mgr_interval=1,

    # ================== General Settings ======================

    # Text file name for status log output:
    # Set to 'None' to disable.
    log_file='log.txt',

    # Turn the TUI into plain ASCII:
    # Much less fun, much more compatible.
    plain_ascii_tui=False,

    # Tui update Interval:
    tui_interval=0.1
)
