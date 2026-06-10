import socket
import subprocess

from PIL import Image

# To be executed in the Raspberry Pi of the dron

ver = "2.1"

print("==============================")
print("UDP server + Do photos  :: version " + ver)
print("==============================")
print("")

# Local IP and listening port
host = '10.42.0.1'
port = 1006

socket_time_out = 2

# Create the listening UDP socket (UDP server)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(socket_time_out)
print("- Socket created (UDP) with timeout = " + str(socket_time_out) + " s")

s.bind((host, port))
print("- Socket binded to: " + host + ":" + str(port))
print("")

do_while = True

# Repeat while a "End photos" message is not received from the PC

while do_while:

    # Receive data from UDP socket        
    try:
        
        data, addr = s.recvfrom(1024)
        
    # If no message is received for 2 seconds
    except:
    
        print("- Do periodic photo") 

        cmd = ["fswebcam", "-i 0", "-r 768x432 --jpeg 85", "--no-banner", "photo_str" + ".jpg"]

        print("- subprocess run: " + ' '.join(cmd))

        subprocess.run(cmd)
        
        
    # If some message is received
    else:
    
        msg = data.decode()
        print("- Received message: " + msg + " from " + addr[0] + ":" + str(addr[1])) 

        # "Do photo" message received
        
        if msg.startswith('Do photo:'): 
                    
            file_name = msg.split(":")[1]
            pic_index = msg.split(":")[2]
            
            # Capture a picture and save with the file name provided in the "Do photo" message

            cmd = ["fswebcam", "-i 0", "-r 1920x1080 --jpeg 95", "--no-banner", ".//photos-UDP//" + file_name + ".jpg"]

            print("- subprocess run: " + ' '.join(cmd))

            subprocess.run(cmd)
            
            # Notify the remote UDP client

            response = "Photo captured successfully: " + file_name
            s.sendto(response.encode(), addr)
                    
            print("- Photo captured (" + pic_index + "): " + file_name + ".jpg")          
            
            # Resize and save a copy of the picture in order to be published in the HTTP server
                    
            img_org = Image.open(".//photos-UDP//" + file_name + ".jpg")

            img_res = img_org.resize((768, 432))

            img_res.save('photo_cap.jpg')     
            img_res.save('photo_str.jpg')     
   

        # "End photos" message received

        if msg.startswith('End photos'): 

            # Notify the remote UDP client

            response = "Photos ended successfully"
            s.sendto(response.encode(), addr)
            
            print("- Photos ended successfully")

            # Terminate loop
            
            do_while = False
    
    print("")

s.close()
