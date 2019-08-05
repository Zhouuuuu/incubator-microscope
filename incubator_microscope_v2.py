import serial
import sys
import time
import datetime
import pypylon
from pypylon import pylon
from pypylon import genicam
import os
import numpy as np
import cv2
from collections import OrderedDict
from plate_dict import plate_96


##plate_96 = OrderedDict([
##    #("Home", [0,0,0]),
##    ("A1", [10,0,0]),
##    ("B1", [10,10,0]),
##    ("C1", [0,10,0]),
##    ("D1", [0,0,0])
##    ])

plate_list = {"6": "plate_6",
              "12": "plate_12",
              "24": "plate_24",
              "48": "plate_48",
              "96": plate_96
              }

jog_dict = {
    "w": None,
    "a": None,
    "s": None,
    "d": None,
    "q": None,
    "e": None
    }

[xMin, xMax] = [0.0,30.0]
[yMin, yMax] = [0.0, 30.0]
[zMin, zMax] = [-45.0, 0.0]

class Camera:
    def __init__(self): #initialize instance of Camera
        
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        print("Using device:", self.camera.GetDeviceInfo().GetModelName())
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.imageWindow = pylon.PylonImageWindow()
        self.imageWindow.Create(1)
        os.chdir("C:\\Users\\Wyss User\\Pictures\\Basler Test")
        print("Current working directory (save location):", os.getcwd())
        print("Camera initialized.")

    def save_image(self, grabResult):
        now = datetime.datetime.now()
        nowstr = now.strftime("%H%M%f-%m_%d_%y")
        print("Saving image...")
        ipo = pylon.ImagePersistenceOptions()
        ipo.SetQuality(100)
        filename = nowstr + ".jpeg"
        try:
            image = self.converter.Convert(grabResult)
            img = image.GetArray()
            cv2.imwrite(filename, img)
            grabResult.Release()
            print("Image successfully saved as", filename)
        except Exception as error:
            print("Error saving image:", error)
            return False
        return True

    def acquire_image(self):
        print("Grabbing image...")
        if not self.camera.IsGrabbing():
            self.camera.StartGrabbing(1)
            
        while self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                print("Image successfully grabbed...")
                self.save_image(grabResult)
                break
            else:
                print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                return False
        self.camera.StopGrabbing()
        #self.camera.Close()
        return True

    def show_video(self):
        if not self.camera.IsGrabbing():
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        try:
            while self.camera.IsGrabbing():
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    self.imageWindow.SetImage(grabResult)
                    if not self.imageWindow.IsVisible():
                        self.imageWindow.Show()
                else:
                    print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                    return False
                grabResult.Release()
                time.sleep(0.05)
        except KeyboardInterrupt:
            return False



class CNC(Camera):
    def __init__(self):
        self.axes = serial.Serial("COM4", baudrate = 115200, timeout = 1)
        #self.LED = serial.Serial #initialize LED
        time.sleep(2)
        print("Homing device...")
        self.axes.write("$22 = 1\n".encode())
        self.axes.write("$x\n".encode())
##        self.axes.write("$h\n".encode())
##        self.axes.flushInput()
##        self.axes.flushOutput()
##        for i in range(7):
##            grbl_out = self.axes.readline()
##            time.sleep(1)
##        while grbl_out != b'ok\r\n':
##            grbl_out = self.axes.readline()
##            print("Homing...")
##            time.sleep(1)
        print("Device initialized.")

    def alarm_read(self): #to be implemented later
        #alarm = b'ALARM:1\r\n'
        #grbl_output = self.axes.readline()
        #if grbl_output == alarm:
        #    return grbl_output
        #return True
        pass

    def configure_settings(self):
        setting = input("\nEnter grbl setting to be changed: ")
        setting = setting + "\n"
        return setting

    def home_cycle(self, position):
        count = 0
        self.axes.flushInput()
        self.axes.flushOutput()
        print("Homing cycle in progress...")
        self.axes.write("$h\n".encode())
        grbl_out = self.axes.readline()
        while grbl_out != b'ok\r\n':
            grbl_out = self.axes.readline()
            print("Homing...",count)
            time.sleep(1)
            count = count + 1
        print("Homing cycle completed.")
        position = [0,0,0]
        return position

    def wellplate(self, plate_list):
        while True:
            print("\nNumber of wells in well plate?")
            well_num = input(">> ")
            if well_num in plate_list:
                well_num = plate_list[well_num]
                return well_num
            print("Please enter a valid number (6, 12, 24, 48, 96).")
        

    def well_move(self, plate, position):

        print("\nWhich well (ex. A1)?")
        print("Type 'esc' to go back.")
        well = input(">> ")
        if well in plate and position == plate[well]:
            print("Already at", well)
        elif well in plate and position != plate[well]:
            x_move = str(plate[well][0] - position[0])
            y_move = str(plate[well][1] - position[1])
            z_move = str(plate[well][2] - position[2])
            gcode_command = f"G91 X{x_move} Y{y_move} Z{z_move}\n"
            self.axes.write(gcode_command.encode())
            position = plate[well]
            return position
        elif well == "esc":
            print("Exited.")
        else:
            print("Invalid input. Please try again.")
        return position
    
    def jog(self, jog_dict, position, xMin, xMax, yMin, yMax, zMin, zMax):
        while True:
            jog_increment = input("Enter a jog increment (mm): ")
            try:
                jog_increment = float(jog_increment)
                if jog_increment > 0:
                    jog_dict["w"] = [0, jog_increment, 0]
                    jog_dict["a"] = [-jog_increment, 0, 0]
                    jog_dict["s"] = [0, -jog_increment, 0]
                    jog_dict["d"] = [jog_increment, 0, 0]
                    jog_dict["q"] = [0, 0, -jog_increment]
                    jog_dict["e"] = [0, 0, jog_increment]
                    while True:
                        print("\nUse the 'wasd' keys to jog the X and Y axes.")
                        print("Use the q and e keys to jog the Z axis.")
                        print("Type 'esc' to exit. Type 'back' to change the jog increment.")
                        print("Current position:", position)
                        jog_input = input(">> ")
                        if jog_input in jog_dict:
                            x = round(position[0] + jog_dict[jog_input][0], 5)
                            y = round(position[1] + jog_dict[jog_input][1], 5)
                            z = round(position[2] + jog_dict[jog_input][2], 5)
                            if x < xMin or x > xMax or y < yMin or y > yMax or z < zMin or z > zMax:
                                print("Beyond axis limit.")
                            else:
                                jog_command = f"G91 X{jog_dict[jog_input][0]} Y{jog_dict[jog_input][1]} Z{jog_dict[jog_input][2]}\n"
                                self.axes.write(jog_command.encode())
                                position = [x,y,z]
                        elif jog_input == "back":
                            break
                        elif jog_input == "esc":
                            return position
                        else:
                            print("Invalid input. Please try again.")
                else:
                    print("Input must be a number greater than zero")
            except ValueError as error:
                print("\n",error)
                print("Input must be number greater than zero.")
                return position

    def night_cycle(self, plate_dict, camera, position):

        #while self.home_cycle(position):
        #    break
        time.sleep(1)
        self.axes.flushInput()
        self.axes.flushOutput()
        print("Begin cycle.")
        position = [0,0,0]
        start = datetime.datetime.now()
        current = datetime.datetime.now()
        diff = (current - start).seconds
        
        while diff < 60:
            for well in plate_dict: #program will always finish last cycle through dictionary even if diff>30

                x_move = str(plate_dict[well][0] - position[0])
                y_move = str(plate_dict[well][1] - position[1])
                z_move = str(plate_dict[well][2] - position[2])
                gcode_command = f"G91 X{x_move} Y{y_move} Z{z_move}\n"
                self.axes.write(gcode_command.encode())
                
                position = plate_dict[well]
                time.sleep(0.2)
                self.axes.flushInput()
                self.axes.write("?\n".encode())
                grbl_out = self.axes.readline()
                print(grbl_out)
                time.sleep(0.2)
                
                while b'Run' in grbl_out:
                    self.axes.flushInput()
                    self.axes.write("?\n".encode())
                    grbl_out = self.axes.readline()
                    print(grbl_out)
                    time.sleep(0.2)
                    
                print("At position", position)
                time.sleep(0.5)
                Camera.acquire_image(camera)
                time.sleep(1)
                current = datetime.datetime.now()
                diff = (current-start).seconds
                print(diff)
                
        return True

class LED():
    def __init__(self):
        self.led = serial.Serial("COM7", baudrate = 9600, timeout = 1)
        self.led.flushInput()
        for i in range(4):
            self.led.write(b"I\r\n")
            time.sleep(0.25)
            self.led.write(b"O\r\sn")
            time.sleep(0.25)
        print("LED initialized.")

    def on(self):
        self.led.write(b"I\r\n")
        return True
    def off(self):
        self.led.write(b"O\r\n")
        return True
    
            
def main():
    camera = Camera()
    machine = CNC()
    led = LED()
    machine.position = [0,0,0]
    plate_num = machine.wellplate(plate_list)
    
    #ser_output = machine.axes.readline()
    while True:
    
        print("\nCurrent position: ", machine.position)
        print("Enter a to move to a well. Enter b to jog the axes.")
        print("Enter p to take a picture.")
        print("Enter z for cycle")
        print("Enter c for custom grbl command.")
        print("Enter h to home the machine")
        print("To change the well plate number, enter n.")
        print("To stop the program, enter 'exit'.")

        main_input = input(">> ")
        if main_input == "a":
            machine.position = machine.well_move(plate_num, machine.position)
        elif main_input == "b":
            machine.position = machine.jog(jog_dict, machine.position, xMin, xMax, yMin, yMax, zMin, zMax)
        elif main_input == "p":
            camera.acquire_image()
        elif main_input == "n":
            plate_num = machine.wellplate(plate_list)
        elif main_input == "z":
            machine.night_cycle(plate_96, camera, machine.position)
        elif main_input == "h":
            machine.home_cycle(machine.position)
        elif main_input == "c":
            setting = machine.configure_settings()
            machine.axes.write(setting.encode())
        elif main_input == "I":
            led.on()
            camera.show_video()
        elif main_input == "O":
            led.off()
        elif main_input == "v":
            camera.show_video()
        elif main_input == "exit":
            camera.imageWindow.Close()
            camera.camera.Close()
            led.off()
            sys.exit()
        else:
            print("Invalid input. Please try again.")
    print("ALARM(1): Reset to continue.")
    return False
    
if __name__ == "__main__":
    main()
