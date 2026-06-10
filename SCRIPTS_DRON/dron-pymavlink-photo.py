import sys
import os
import time
import json
import math
import socket
import threading

import msvcrt

from pymavlink import mavutil
from datetime import datetime

# To be executed in the PC

# Thread to intercept the 'c' key to stop ordering photos
def key_capture_thread(key_press_lst):

    global stop_thread

    char = None

    while char != 'c' and not stop_thread:
        # time.sleep(0.05)
        char = msvcrt.getch().decode("utf-8")
        key_press_lst.clear()
        key_press_lst.append(char)

    if char == 'c':
        print("Key 'c' pressed... stopping loop and repeating procedure")
        print("")

# Convert decimal degrees into degrees, minutes and seconds
# e.g. 36.7151909 -> (36.0, 42.0, 54.68724000001146)
#      -4.4778886 -> (4.0, 28.0, 40.39895999999999)
def decimal_to_dms(decimal):
    remainder, degrees = math.modf(abs(decimal))
    remainder, minutes = math.modf(remainder * 60)
    seconds = remainder * 60

    return degrees, minutes, seconds

# Send to the dron a MAV_CMD_REQUEST_MESSAGE command to request a message
def send_request_mavlink_msg(mavlink_msg_id, mavlink_msg_des, mavlink_msg_type):

    cmd = c_server.mav.command_long_encode(        
            c_server.target_system,  # Target system ID        
            c_server.target_component,  # Target component ID        
            mavutil.mavlink.MAV_CMD_REQUEST_MESSAGE,  # ID of the command to send        
            0,  # Confirmation        
            mavlink_msg_id,  # Parameter 1: Message ID to be streamed        
            0, 0, 0, 0, 0, 0  # Parameters 2-7 (unused)
            )
    
    # Send 'REQUEST_MESSAGE' command
    print("- Sending 'MAV_CMD_REQUEST_MESSAGE' command to dron")
    print("- Requested '" + mavlink_msg_des + "' message")
    
    c_server.mav.send(cmd)
        
    # Receive requested message
    print("- Waiting for '" + mavlink_msg_des + "' message from dron")
    
    msg = c_server.recv_match(type=mavlink_msg_type)
    
    print("- Received '" + mavlink_msg_des + "' message from dron:")
    print("")

    return msg

print(sys.executable)
print(os.getcwd())

ver  = "2.1"

print("==============================")
print("Order photos + Query geolocation :: version " + ver)
print("==============================")
print("")
print("Libraries used:")
print(" - PC: pymavlink, mavutil, socket, json, exiftool")
print(" - Raspberry: socket, fswebcam")
print("------------------------------")
print("")

# =========================================
# Port configuration
# =========================================

port_server_dron = 1006  # UDP server at Raspberry side must be initiated with this same port
port_server_pc = 14556  # MAVproxy at Raspberry side must be initiated with this same port

# =========================================
# Create UDP server (to connect to MAVproxy)
# =========================================

# UDP server address = local machine IP:port
host_server_pc = '10.42.0.245'

# Start a UDP server (UDP socket listening on some IP:port address)
c_server = mavutil.mavlink_connection('udpin:' + host_server_pc + ':' + str(port_server_pc))

print("UDP server created (" + host_server_pc + ":" + str(port_server_pc) + ")")
print(type(c_server))
print("")

# Wait for the first heartbeat from the Ardupilot

# This sets the system and component ID of remote system for the link

print("Waiting for heartbeat from some client ... ")
c_server.wait_heartbeat()

print("Heartbeat received from " + str(list(c_server.clients)[0][0]) + ":" + str(list(c_server.clients)[0][1]))
print("")

print("- Target system: " + str(c_server.target_system))
print("- Target component: " + str(c_server.target_component))
print("- UDP server: " + str(c_server.udp_server))
print("- IP dron: " + str(list(c_server.clients)[0][0]))
print("- Port dron: " + str(list(c_server.clients)[0][1]))
print("- Clients: " + str(len(c_server.clients)))

for i, c in enumerate(list(c_server.clients)):
    print("  · #" + str(i+1) + ": " + str(c[0]) + ":" + str(c[1])) 

print("")

c = list(c_server.clients)[0]
ip_dron = str(c[0])
print("IP dron: " + ip_dron)
print("")

# =========================================
# Create UDP client (to connect to the Raspberry and order photos)
# =========================================

host_server_dron = ip_dron  # Obtain this address from c_server.clients

UDP_client_time_out = 1

# Start a UDP client
c_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
c_client.settimeout(UDP_client_time_out)

print("UDP client created with timeout = " + str(UDP_client_time_out))
print(type(c_client))
print("")

print("Connecting to server (" + host_server_dron + ":" + str(port_server_dron) + ") ... ")
c_client.connect((host_server_dron, port_server_dron))

# =========================================
# Order photos and read parameters
# =========================================

photos_period = 5  # Time between photo orders
num_photos = -1  # Total number of photos to take: -1 = No limit
total_time = 60  # Total time ordering photos [seconds]: -1 = No limit

stop_terminate = False

while not stop_terminate:

    print("- Time between photos: " + str(photos_period) + " seconds")

    if num_photos != -1:
        print("- Maximum number of photos to take: " + str(num_photos) + " photos")

    if total_time != -1:
        print("- Maximum time taking photos: " + str(total_time) + " seconds")

    print("")

    while True:
        print("Write 'do' to begin taking photos or 'exit' to terminate the program")

        a = input()

        if a == 'do':
            break

        if a == 'exit':
            stop_terminate = True
            break

    print("")

    if stop_terminate:
        break

    key_press_list = []

    stop_thread = False

    key_thread = threading.Thread(target=key_capture_thread, args=[key_press_list],
                                  name='key_capture_thread', daemon=False)
    key_thread.start()

    print("Press the 'c' key at any time to stop taking photos and repeat the procedure")
    print("")

    end_condition = False

    photos_taken = 0

    t_offset = time.monotonic() % photos_period

    elapsed = 0

    t = time.monotonic_ns()

    stop_photos = False

    while not end_condition and not stop_photos:

        print("==========================")
        print("File " + str(photos_taken + 1) + " (Time elapsed = " + str(elapsed) + "s):")
        print("==========================")
        print("")

        # File name for .jpg and .json files
        d = datetime.now()
        file_name = 'dron_' + d.strftime('%Y%m%d_%H%M%S')

        print("- Image file name: " + file_name + '.jpg')
        print("- Data file name: " + file_name + '.json')
        print("")

        # -----------------------------
        # [1] Request and read some parameters from the dron: latitude, longitude, pitch, roll, yaw
        # -----------------------------

        msg_gps = send_request_mavlink_msg(
                mavlink_msg_id=mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
                mavlink_msg_des='MAVLINK_MSG_ID_GLOBAL_POSITION_INT',
                mavlink_msg_type='GLOBAL_POSITION_INT')

        print(msg_gps)
        print("")

        msg_att = send_request_mavlink_msg(
                mavlink_msg_id=mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE,
                mavlink_msg_des='MAVLINK_MSG_ID_ATTITUDE',
                mavlink_msg_type='ATTITUDE')

        print(msg_att)
        print("")

        # Save parameters
        dron_lat = msg_gps.lat / pow(10, 7)
        dron_lon = msg_gps.lon / pow(10, 7)
        dron_pitch = msg_att.pitch
        dron_roll = msg_att.roll
        dron_yaw = msg_att.yaw

        # Print parameters
        print("Latitude:", dron_lat)
        print("Longitude:", dron_lon)
        print("Pitch:", dron_pitch)
        print("Roll:", dron_roll)
        print("Yaw:", dron_yaw)
        print("")

        # -----------------------------
        # [2] Order the dron to make a photo with the webcam connected to the Raspberry pi
        # -----------------------------

        command = "Do photo:" + file_name + ":" + str(photos_taken + 1)
        
        no_response = True
        
        while no_response:        

            print("Send UDP command to Raspberry:", command)
            c_client.send(command.encode())
        
            # Receive data from UDP socket        
            try:        

                data = c_client.recv(1024)
                
            # If no message is received for 1 second
            except:
            
                print("UDP command not acknowledged from Raspberry: resending ...")
                                
            # If some message is received
            else:            
                                      
                print("Received UDP message:", data.decode())
                print("")
                no_response = False
                
        photos_taken += 1

        # -----------------------------
        # [3] Save the dron parameters into a JSON file for subsequent processing
        # -----------------------------

        # Convert latitude and longitude to dms (degrees, minutes, seconds) in absolute value
        # plus 'N', 'S', 'W', 'E' in order to insert data into the GPS EXIF fields
        dms_lat = decimal_to_dms(dron_lat)
        dms_lon = decimal_to_dms(dron_lon)
        dms_lat_ref = 'N' if dron_lat > 0 else 'S'
        dms_lon_ref = 'E' if dron_lon > 0 else 'W'

        # Convert to string format the dms values in order to create the JSON structure
        dms_lat_str = str(int(dms_lat[0])) + ' ' + str(int(dms_lat[1])) + ' ' + str(round(dms_lat[2], 8))
        dms_lon_str = str(int(dms_lon[0])) + ' ' + str(int(dms_lon[1])) + ' ' + str(round(dms_lon[2], 8))

        print('lat dms:', dms_lat_str)
        print('lon dms:', dms_lon_str)
        print('lat ref:', dms_lat_ref)
        print('lon ref:', dms_lon_ref)
        print("")

        # Create a dictionary containing the parameters (original and dms)
        data = {'lat': dron_lat,
                'lon': dron_lon,
                'pitch': dron_pitch,
                'roll': dron_roll,
                'yaw': dron_yaw,
                'lat_dms': dms_lat_str,
                'lon_dms': dms_lon_str,
                'lat_ref': dms_lat_ref,
                'lon_ref': dms_lon_ref}

        # Convert the dictionary to JSON
        text = json.dumps(data)
        comm = json.loads(text)

        print("JSON:")
        print(comm)
        print("")

        # Save the JSON file
        with open('.\\JSON\\' + file_name + '.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        end_condition = (photos_taken == num_photos and num_photos != -1) or \
                        (elapsed >= total_time != -1)

        stop_photos = key_press_list == ['c']

        key_press_list.clear()

        if not end_condition and not stop_photos:
            time.sleep(photos_period - (time.monotonic() - t_offset) % photos_period)
            elapsed = round((time.monotonic_ns() - t) / 1000000000, 2)

        if end_condition:
            print("The photo sequence has ended")
            print("")
            print("Press 'Enter' to continue")
            print("")
            stop_thread = True
            key_thread.join()

while True:
    print("· Write 'terminate' to terminate the photos dron service")
    print("· Write 'exit' to exit the program without terminating the photos dron service")

    a = input()

    if a == 'terminate' or a == 'exit':
        break

print("")

if a == 'terminate':

    # Terminate UDP server in Raspberry

    command = "End photos"

    c_client.send(command.encode())
    print("Send UDP command to Raspberry:", command)

    data = c_client.recv(1024)

    print("Received UDP message:", data.decode())
    print("")

print("End of program")
