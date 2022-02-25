"""
2021 ETH Zurich, Christian Vogt
Script automatically connects to devices named "PostureSensor"
and records their caracteristics to files (one for each 
MAC address). Please use with corresponding PostureSensor
firmware.

Code is based on the blatann central with events example,
large parts of the code origin from there
(https://github.com/ThomasGerstenberg/blatann). In case of
problems with blatann and windows see the following thesis: 
https://gitlab.ethz.ch/pbl/sf2021/jackie-lim

Requires the Nordic nrf52840 dongle to work, with
firmware for the dongle in "jackie-lim-master-nrf52840_dongle.zip"
"""

import struct
from blatann import BleDevice
from blatann.gap import smp
from blatann.examples import example_utils, constants
from blatann.waitables import GenericWaitable
from blatann.nrf import nrf_events
from blatann.services import battery
import time
import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.animation as animation
import collections
from scipy import signal
import pandas as pd
import time
import sys
import os
from scipy.fft import fft, ifft

# Getting system time to name the file and store it as string
sys_time_str = str(time.strftime("%Y%m%d-%H%M%S"))

# Is used to generate file names and paths that are compatible between different OS
python_path = os.path.dirname(os.path.realpath(__file__)) # path to this file
dir_name = "smartpatch_recording_" + str(time.strftime("%Y%m%d-%H%M%S"))
dir_path = os.path.join(python_path, dir_name)


#######################################################################################################
# BLE Classes
#######################################################################################################

class results():
   def __init__(self):
        self.ppg_red = collections.deque(np.zeros(150))
        self.ppg_ir = collections.deque(np.zeros(150))
        self.ppg_green = collections.deque(np.zeros(150))
        self.acc_x = collections.deque(np.zeros(150))
        self.acc_y = collections.deque(np.zeros(150))
        self.acc_z = collections.deque(np.zeros(150))
        self.gyr_x = collections.deque(np.zeros(150))
        self.gyr_y = collections.deque(np.zeros(150))
        self.gyr_z = collections.deque(np.zeros(150))
        self.qvar = collections.deque(np.zeros(150))
        self.temperature = collections.deque(np.zeros(150))
        
        
#storing the results (just for display plotting)
res = results()

class MyPeripheralConnection(object):
    def __init__(self, peer, waitable, res):
        self.f = open(str(peer.peer_address).replace(':', '').replace(',s', '')+'.csv', 'w')
        #prepare csv file for writing
        self.writer = csv.writer(self.f)
        #prepare for plotting
        #prepare rest
        self.peer = peer
        self.waitable = waitable
        self.res = res
        self._start_db_discovery()

    def _start_db_discovery(self):
        self.peer.discover_services().then(self._on_db_discovery)
        for service in self.peer.database.services:
            logger.info(service)
            print(service)


    def _on_db_discovery(self, peer, event_args):
        logger.info("Service discovery complete! status: {}".format(event_args.status))
        # The peer's database is now current, log out the services found
        for service in peer.database.services:
            logger.info(service)

        # Find and subscribe to the characteristics     
        for uuid in smartpatch_uuids:
            char = self.peer.database.find_characteristic(uuid)
            if char:
                logger.info("Subscribing to characteristic: " + uuid)
                print("Subscribing to characteristic: " + uuid)
                char.subscribe(self._on_notification)
            else:
                logger.warning("Failed to find characteristic: " + uuid)
                print("Failed to find characteristic: " + uuid)

        print("Setting connection paramterers ...")    
        # Stop the main waitable so the code in main can continue
        self.waitable.notify()

        # # Initiate the pairing process
        # self._start_pairing()

    def _start_pairing(self):
        self.peer.security.set_security_params(passcode_pairing=True, io_capabilities=smp.IoCapabilities.KEYBOARD_DISPLAY,
                                               bond=True, out_of_band=False)
        self.peer.security.on_passkey_required.register(self._on_passkey_entry)
        self.peer.security.pair().then(self._start_db_discovery)


    def _on_passkey_entry(self, peer, event_args):
        passkey = input("Enter peripheral passkey: ")
        event_args.resolve(passkey)

    def _on_pair_complete(self, peer, event_args):
        hex_convert_char = self.peer.database.find_characteristic(constants.HEX_CONVERT_CHAR_UUID)

        
    def _on_notification(self, characteristic, event_args):
        characteristic_name = smartpatch_uuids[str(characteristic.uuid)]
        address_name = str(self.peer.peer_address).replace(':', '').replace(',s', '')
        global smartpatch_data
        unsaved_data = []
        byte_counter = 0        

        if ((characteristic_name == 'ppg_red') or (characteristic_name == 'ppg_ir') or (characteristic_name == 'ppg_green')):
            
            for i in range(0, 51):
                if(i != 50):
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1], characteristic.value[byte_counter+2], characteristic.value[byte_counter+3]]
                    data_as_int = int.from_bytes(temp_data, byteorder='little', signed=True)
                    byte_counter += 4 

                    if (characteristic_name == 'ppg_red'):
                        self.res.ppg_red.append(data_as_int) 
                        self.res.ppg_red.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'ppg_ir'):
                        self.res.ppg_ir.append(data_as_int) 
                        self.res.ppg_ir.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'ppg_green'):
                        self.res.ppg_green.append(data_as_int) 
                        self.res.ppg_green.popleft()
                        unsaved_data.append(data_as_int)
                else:
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1], characteristic.value[byte_counter+2], characteristic.value[byte_counter+3]]
                    index_counter = int.from_bytes(temp_data, byteorder='little', signed=True)
                    index_array = []
                    for j in range(0,50):
                        index_array.append(index_counter)
               
            if(characteristic_name == 'ppg_red'):
                file_name = address_name + "_ppg_red.csv"
            elif(characteristic_name == 'ppg_ir'):
                file_name = address_name + "_ppg_ir.csv"
            elif(characteristic_name == 'ppg_green'):     
                file_name = address_name + "_ppg_green.csv"
            else:
                file_name = address_name + "_ppg_error.csv"


            file_path = os.path.join(dir_name, file_name)
            tmp_export_indx = pd.DataFrame(index_array)
            tmp_export_data = pd.DataFrame(unsaved_data)
            tmp_export_indx.transpose()
            tmp_export_data.transpose()
            tmp_export = pd.concat([tmp_export_indx, tmp_export_data], axis=1)
            tmp_export.to_csv(file_path, mode='a', header=not os.path.exists(file_path))


        elif ((characteristic_name == 'acc_x') or (characteristic_name == 'acc_y') or (characteristic_name == 'acc_z') or (characteristic_name == 'gyro_x') or (characteristic_name == 'gyro_y') or (characteristic_name == 'gyro_z') or (characteristic_name == 'qvar')):            
            for i in range(0, 121):
                if(i != 120):
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1]]
                    data_as_int = int.from_bytes(temp_data, byteorder='little', signed=True)
                    byte_counter += 2 

                    if (characteristic_name == 'acc_x'):
                        self.res.acc_x.append(data_as_int) 
                        self.res.acc_x.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'acc_y'):
                        self.res.acc_y.append(data_as_int)
                        self.res.acc_y.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'acc_z'):
                        self.res.acc_z.append(data_as_int)
                        self.res.acc_z.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'gyro_x'):
                        self.res.gyr_x.append(data_as_int)
                        self.res.gyr_x.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'gyro_y'):
                        self.res.gyr_y.append(data_as_int)
                        self.res.gyr_y.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'gyro_z'):
                        self.res.gyr_z.append(data_as_int)
                        self.res.gyr_z.popleft()
                        unsaved_data.append(data_as_int)

                    elif (characteristic_name == 'qvar'):
                        self.res.qvar.append(data_as_int)
                        self.res.qvar.popleft()
                        unsaved_data.append(data_as_int)

                else:
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1], characteristic.value[byte_counter+2], characteristic.value[byte_counter+3]]
                    index_counter = int.from_bytes(temp_data, byteorder='little', signed=True)
                    index_array = []
                    for j in range(0,120):
                        index_array.append(index_counter)

            if(characteristic_name == 'acc_x'):
                file_name = address_name + "_acc_x.csv"
            elif(characteristic_name == 'acc_y'):
                file_name = address_name + "_acc_y.csv"
            elif(characteristic_name == 'acc_z'):     
                file_name = address_name + "_acc_z.csv"
            elif(characteristic_name == 'gyro_x'):     
                file_name = address_name + "_gyro_x.csv"
            elif(characteristic_name == 'gyro_y'):     
                file_name = address_name + "_gyro_y.csv"
            elif(characteristic_name == 'gyro_z'):     
                file_name = address_name + "_gyro_z.csv"
            elif(characteristic_name == 'qvar'):     
                file_name = address_name + "_qvar.csv"
            else:
                file_name = address_name + "_imu_error.csv"

            file_path = os.path.join(dir_name, file_name)
            tmp_export_indx = pd.DataFrame(index_array)
            tmp_export_data = pd.DataFrame(unsaved_data)
            tmp_export_indx.transpose()
            tmp_export_data.transpose()
            tmp_export = pd.concat([tmp_export_indx, tmp_export_data], axis=1)
            tmp_export.to_csv(file_path, mode='a', header=not os.path.exists(file_path))


        elif (characteristic_name == 'temp'):            
            for i in range(0, 31):   
                if(i != 30):
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1]]
                    data_as_int = int.from_bytes(temp_data, byteorder='little', signed=True)
                    byte_counter += 2 

                    self.res.temperature.append(data_as_int)
                    self.res.temperature.popleft()
                    unsaved_data.append(data_as_int)

                else:
                    temp_data = [characteristic.value[byte_counter], characteristic.value[byte_counter+1], characteristic.value[byte_counter+2], characteristic.value[byte_counter+3]]
                    index_counter = int.from_bytes(temp_data, byteorder='little', signed=True)
                    index_array = []
                    for j in range(0,30):
                        index_array.append(index_counter)


            file_name = "_temperature.csv"
            file_path = os.path.join(dir_name, file_name)
            tmp_export_indx = pd.DataFrame(index_array)
            tmp_export_data = pd.DataFrame(unsaved_data)
            tmp_export_indx.transpose()
            tmp_export_data.transpose()
            tmp_export = pd.concat([tmp_export_indx, tmp_export_data], axis=1)
            tmp_export.to_csv(file_path, mode='a', header=not os.path.exists(file_path))


class ConnectionManager(object):
    def __init__(self, ble_device, exit_waitable, res, device_address):
        self.ble_device = ble_device
        self.exit_waitable = exit_waitable
        self.target_device_name = ""
        self.connection = None
        self.peer = None
        self.res = res
        self.device_address = device_address

    def _on_connect(self, peer):
        global is_connected

        if not peer:
            logger.warning("Timed out connecting to device")
            self.exit_waitable.notify()
        else:
            logger.info("Connected, conn_handle: {}".format(peer.conn_handle))
            self.peer = peer
            # Connect the disconnect event to the exit waitable, so if
            # the peripheral disconnects from us unexpectedly the program terminates
            peer.on_disconnect.register(self.exit_waitable.notify)
            # Create the connection
            print("Connected to "+str(peer.peer_address))
           
            is_connected = True
            self.peer.exchange_mtu(247).then(self._on_mtu_exchange_complete)
            
    def _on_mtu_exchange_complete(self, peer, event_args):
        self.connection = MyPeripheralConnection(peer, self.exit_waitable, self.res)

    def _on_scan_report(self, scan_report):
        for report in scan_report.advertising_peers_found:
            if report.advertise_data.local_name == self.target_device_name:
                print("Found " + str(self.target_device_name) + " with MAC " + str(report.peer_address).replace(':', '').replace(',s', '') + " and RSSI: " + str(report.rssi))
                logger.info("Found match: connecting to address {}".format(report.peer_address))

                #only connect if address is correct
                if((str(report.peer_address).replace(',s', '')) == self.device_address):
                    self.ble_device.connect(report.peer_address).then(self._on_connect)
                    return
                else:
                    print("device found with wrong address")
                    print("Address found: " + str(report.peer_address).replace(',s', ''))

        logger.info("Did not find target peripheral")
        self.exit_waitable.notify()

    def scan_and_connect(self, name, timeout=10):
        logger.info("Scanning for '{}'".format(name))
        self.target_device_name = name
        self.ble_device.scanner.set_default_scan_params(timeout_seconds=timeout)
        self.ble_device.scanner.start_scan().then(self._on_scan_report)

#######################################################################################################
# Init BLE Module and Classes
#######################################################################################################

# logger = example_utils.setup_logger(level="WARNING")
logger = example_utils.setup_logger(level="DEBUG")
plt.set_loglevel("ERROR")
# logger = example_utils.setup_logger(level="INFO")

serial_port = "COM9" # COM Port of nRF-Dongle

smartpatch_name = 'SmartPatch'
smartpatch_address = 'FA:FB:C6:90:20:4A'
smartpatch_uuids = {
    '3da22dc6-70d7-4217-9bb2-de5d79560001' : 'acc_x',
    '3da22dc6-70d7-4217-9bb2-de5d79560002' : 'acc_y',
    '3da22dc6-70d7-4217-9bb2-de5d79560003' : 'acc_z',
    '3da22dc6-70d7-4217-9bb2-de5d79560011' : 'gyro_x',
    '3da22dc6-70d7-4217-9bb2-de5d79560012' : 'gyro_y',
    '3da22dc6-70d7-4217-9bb2-de5d79560013' : 'gyro_z',
    'd4eb1a81-2444-4d16-993e-4d28fe2c0001' : 'qvar',
    '182281a8-153a-11ec-82a8-0242ac130001' : 'ppg_red',
    '182281a8-153a-11ec-82a8-0242ac130002' : 'ppg_ir',
    '182281a8-153a-11ec-82a8-0242ac130003' : 'ppg_green',
    '18095c47-81d2-44e5-a350-aef131810001' : 'temp',
}

# Create a waitable that will block the main thread until notified by one of the classes above
main_thread_waitable = GenericWaitable()

# Create and open the BLE device (and suppress spammy logs)
ble_device = BleDevice(serial_port, notification_hw_queue_size = 4, write_command_hw_queue_size = 4)
ble_device.configure(vendor_specific_uuid_count = 20, max_connected_peripherals = 8, max_connected_clients = 1, attribute_table_size= 4096)
ble_device.event_logger.suppress(nrf_events.GapEvtAdvReport)
ble_device.open()

# Create the connection manager and start the scanning process
sp_device = ConnectionManager(ble_device, main_thread_waitable, res, smartpatch_address)


#######################################################################################################
# Animation
#######################################################################################################

fig1, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(5)

def animate(i):

    # This is an ugly fix, until the smartpatch firmware is updated
    try:
        # Find the battery service within the peer's database
        battery_service = battery.find_battery_service(sp_device.peer.database)
        if not battery_service:
            print("Failed to find Battery Service in peripheral database")

        # Read out the battery level
        print("Reading battery level...")
        _, event_args = battery_service.read().wait(timeout=1, exception_on_timeout=False)
        battery_percent = event_args.value
        print("")
        print("BATTERY: {}%".format(battery_percent))
        print("")
    except:
        print("no connection")
        pass


    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()
    ax5.clear()

    ax1.set_title("PPG")
    ax2.set_title("Accelerometer") 
    ax3.set_title("Gyro") 
    ax4.set_title("QVAR") 
    ax5.set_title("Temperature") 

    ax1.plot(sp_device.res.ppg_red, linewidth=0.5, label="red")
    # ax1.plot(sp_device.res.ppg_ir, linewidth=0.5, label="ir")
    # ax1.plot(sp_device.res.ppg_green, linewidth=0.5, label="green")
    ax1.legend(loc="upper left")

    ax2.plot(sp_device.res.acc_x, linewidth=0.5, label="x")
    ax2.plot(sp_device.res.acc_y, linewidth=0.5, label="y")
    ax2.plot(sp_device.res.acc_z, linewidth=0.5, label="z")
    ax2.legend(loc="upper left")
    
    ax3.plot(sp_device.res.gyr_x, linewidth=0.5, label="x")
    ax3.plot(sp_device.res.gyr_y, linewidth=0.5, label="y")
    ax3.plot(sp_device.res.gyr_z, linewidth=0.5, label="z")
    ax3.legend(loc="upper left")

    ax4.plot(sp_device.res.qvar, linewidth=0.5)

    ax5.plot(sp_device.res.temperature, linewidth=0.5)
    # fig1.tight_layout()

#######################################################################################################
# Main
#######################################################################################################

#######################################################################################################
#   To Do
#   - Increase connection timeout to 20s
#   - Make error debug messages apear
#   - Auto reconnect if connection is lost
#######################################################################################################

def main():

    target_device_name = smartpatch_name

    ###### Maybe pack this into a while loop ######
    os.mkdir(dir_path)
    sp_device.scan_and_connect(target_device_name)
    print("Connecting to device ...")
    main_thread_waitable.wait()

            # self.peer.set_connection_parameters(min_connection_interval_ms=7.5, max_connection_interval_ms=200, connection_timeout_ms=20000, slave_latency=0) 
    print("Updating connection paramterers ...")   
    if sp_device.peer:
        sp_device.peer.set_connection_parameters(min_connection_interval_ms=7.5, max_connection_interval_ms=20, connection_timeout_ms=20000, slave_latency=0)

    print("Starting animation & recording data ...")
    ani = animation.FuncAnimation(fig1, animate, interval=100) # Refresh window every second
    plt.show()
    print("window closed")
    # main_thread_waitable.wait()

    # This part will be triggered if the gui window is closed
    # Disconnect the device
    if sp_device.peer:
        print("Disconnecting ...")
        sp_device.peer.disconnect().wait()
    ble_device.close()

if __name__ == '__main__':
    main()
