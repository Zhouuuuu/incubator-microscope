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
from plate_dict import plate_6
import keyboard
import threading

plate_list = {"6": plate_6,
              "12": "plate_12",
              "24": "plate_24",
              "48": "plate_48",
              "96": "plate_96"
              }
cycle_dict = {

    }

jog_dict = {
    "w": None,
    "a": None,
    "s": None,
    "d": None,
    "q": None,
    "e": None
    }

[xMin, xMax] = [0.0,120.0]
[yMin, yMax] = [0.0, 120.0]
[zMin, zMax] = [-56.0, 50.0]

class Camera:
    def __init__(self): #initialize Camera object
        
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice()) #create instance of Camera

        #Open camera
        self.camera.Open()
        print("Using device:", self.camera.GetDeviceInfo().GetModelName())
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

        #Set Auto-Gain and Auto-Exposure to be OFF
        self.camera.ExposureAuto.SetValue("Off")
        self.camera.GainAuto.SetValue("Off")

        #Create an image window
        self.imageWindow = pylon.PylonImageWindow()
        self.imageWindow.Create(1)

        #Change save directory
        os.chdir("C:\\Users\\Wyss User\\Pictures\\Basler Test")
        print("Current working directory (save location):", os.getcwd())
        
        print("Camera initialized.")

    def save_image(self, grabResult): #Method for saving images

        #Set saved image title format: Time-Date.jpeg
        now = datetime.datetime.now()
        nowstr = now.strftime("%H%M%f-%m_%d_%y")
        print("Saving image...")
        ipo = pylon.ImagePersistenceOptions()
        ipo.SetQuality(100)
        filename = nowstr + ".jpeg"

        #Save using cv2
        try:
            image = self.converter.Convert(grabResult)
            img = image.GetArray()
            cv2.imwrite(filename, img)
            grabResult.Release() #Release the grab result so that a new image can be grabbed
            print("Image successfully saved as", filename)
        except Exception as error:
            print("Error saving image:", error)
            return False
        return True

    def acquire_image(self): #Method for grabbing and saving one image
        
        print("Grabbing image...")
        if not self.camera.IsGrabbing():
            self.camera.StartGrabbing(1)
            
        while self.camera.IsGrabbing():
            grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grabResult.GrabSucceeded():
                print("Image successfully grabbed...")
                self.save_image(grabResult) #Call save_image method
                break
            else:
                print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                return False
        #self.camera.StopGrabbing()
        #self.camera.Close()
        return True

    def change_parameters(self): #Method for changing the exposure and gain of the camera

        #Get current gain and exposure values
        gain = self.camera.Gain.GetValue()
        exposure = self.camera.ExposureTime.GetValue()
        print("Current gain: ", gain)
        print("Current exposure: ", exposure)
        print("Use the up and down arrows to change the gain.")
        print("Use the left and right arrows to change the exposure time.")
        while True:

            #Arrow keys used to change parameters
            try:
                if keyboard.is_pressed("up"):
                    gain = round((gain + 0.20), 2)  #Gain changed with up and down arrows by increments of 0.20db
                    self.camera.Gain.SetValue(gain)
                    print("Gain (db): ",gain)
                    time.sleep(0.1)                 #Sleep time of 0.1 seconds
                elif keyboard.is_pressed("down"):
                    gain = round((gain - 0.20), 2)
                    self.camera.Gain.SetValue(gain)
                    print("Gain (db): ",gain)
                    time.sleep(0.1)
                elif keyboard.is_pressed("right"):  #Exposure changed with left and right arrows keys
                    exposure = exposure + 20        #Changed by increments of 20
                    self.camera.ExposureTime.SetValue(exposure)
                    print("Exposure (us): ", exposure)
                    time.sleep(0.01)                #Sleep time of 1 ms
                elif keyboard.is_pressed("left"):
                    exposure = exposure - 20
                    self.camera.ExposureTime.SetValue(exposure)
                    print("Exposure (us): ", exposure)
                    time.sleep(0.02)
                elif keyboard.is_pressed("Esc"):    #Escape key used to exit method
                    return gain
            except:
                print("Gain cannot be lower than zero.")
                break
                    
class CNC(Camera): #Class for motor control which inherits Camera class for image save functionality.
    def __init__(self): #Initialize instance of CNC
        self.axes = serial.Serial("COM4", baudrate = 115200, timeout = 1) #Open serial port connected to Arduino/GRBL
        #self.LED = serial.Serial #initialize LED
        time.sleep(2)

        #Home the device on start up
        time.sleep(1)
        self.axes.write("$110 = 200\n".encode())
        time.sleep(1)
        self.axes.write("$111 = 200\n".encode())
        time.sleep(1)
        print("Homing device...")
        self.axes.write("$22 = 1\n".encode())
        self.axes.write("$x\n".encode())
        self.axes.write("$h\n".encode()) #start
        self.axes.flushInput()
        self.axes.flushOutput()
        for i in range(7):
            grbl_out = self.axes.readline()
            time.sleep(1)
        while grbl_out != b'ok\r\n':          #Wait until homing has finished
            grbl_out = self.axes.readline()
            print("Homing...")
            time.sleep(1) #finish
        
        print("Device initialized.")

    def configure_settings(self): #Method for writing directly to GRBL
        setting = input("\nEnter grbl setting to be changed: ")
        setting = setting + "\n"
        self.axes.write(setting.encode())
        return setting

    def home_cycle(self, position): #Method for homing the machine
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
        return position     #Position must be returned with every move so that the program knows where the machine

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
        print("Enter nothing to go back.")
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
        elif well == "":
            print("Exited.")
            return position
        else:
            print("Invalid input. Please try again.")
        return position
    
    def jog(self, camera, position, xMin, xMax, yMin, yMax, zMin, zMax):
        jog_increment = 0.005
        sleep_time = 0.25
        self.axes.write("$110 = 500\n".encode())
        self.axes.write("$111 = 500\n".encode())
        self.axes.write("$112 = 300\n".encode())
        print("Use the arrow keys to jog the X and Y axes.")
        print("Use the page up and page down keys to jog the Z axis.")
        print("Use ctrl and alt to change the jog increment.")
        print("Press p to take a picture.")
        print("Press 'esc' to exit.")
        print("Current position: ", position)
        print("Jog increment: ", jog_increment)
        while True:
            try:
                if keyboard.is_pressed("right") and xMin <= position[0] + jog_increment <= xMax:
                    gcode_command = f"G91 X{jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[0] = round(position[0] + jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("left") and xMin <= position[0] - jog_increment <= xMax:
                    gcode_command = f"G91 X{-jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[0] = round(position[0] - jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("up") and yMin <= position[1] + jog_increment <= yMax:
                    gcode_command = f"G91 Y{jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[1] = round(position[1] + jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("down") and yMin <= position[1] - jog_increment <= yMax:
                    gcode_command = f"G91 Y{-jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[1] = round(position[1] - jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("page_down") and zMin <= position[2] + jog_increment <= zMax:
                    gcode_command = f"G91 Z{jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[2] = round(position[2] + jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("page_up") and zMin <= position[2] - jog_increment <= zMax:
                    gcode_command = f"G91 Z{-jog_increment}\n"
                    self.axes.write(gcode_command.encode())
                    position[2] = round(position[2] - jog_increment, 5)
                    print("Current position: ", position)
                    time.sleep(sleep_time)
                elif keyboard.is_pressed("alt"):
                    jog_increment = round(jog_increment + 0.01, 4)
                    print("Jog increment: ", jog_increment)
                    sleep_time = 0.25
                    time.sleep(0.05)
                elif keyboard.is_pressed("x"):
                    jog_increment = round(jog_increment + 0.001, 4)
                    print("Jog increment: ", jog_increment)
                    sleep_time = 0.25
                    time.sleep(0.05)
                elif keyboard.is_pressed("ctrl"):
                    jog_increment = round(jog_increment - 0.01, 4)
                    if jog_increment < 0.005:
                        jog_increment = 0.001
                        print("Jog increment must be greater than 0.005mm.")
                    print("Jog increment: ", jog_increment)
                    sleep_time = 0.25
                    time.sleep(0.05)
                elif keyboard.is_pressed("z"):
                    jog_increment = round(jog_increment - 0.001, 4)
                    if jog_increment < 0.005:
                        jog_increment = 0.005
                        print("Jog increment must be greater than 0.005mm.")
                    print("Jog increment: ", jog_increment)
                    sleep_time = 0.25
                    time.sleep(0.05)
                elif keyboard.is_pressed("p"):
                    Camera.acquire_image(camera)
                    time.sleep(1)
                elif keyboard.is_pressed("Esc"):
                    time.sleep(0.5)
                    return position
    
            except Exception as error:
                print(error)

    def night_cycle(self, plate_dict, camera, position, camera, cycle_dict):
      
        num_positions = input("Number of positions?")
        num_positions = int(num_positions)
        print("Jog axes to position to be imaged. Press enter to save the position.")
        
        count = 0
        while count < num_positions:
            while not keyboard.is_pressed("Enter"):
                self.jog(camera, position,xMin, xMax, yMin, yMax, zMin, zMax)
            cycle_dict[i] = position
            count = count + 1
        
        while self.home_cycle(position):
            break
        time.sleep(1)
        self.axes.flushInput()
        self.axes.flushOutput()
        print("Begin cycle.")
        position = [0,0,0]
        start = datetime.datetime.now()
        current = datetime.datetime.now()
        diff = (current - start).seconds
        
        while diff < 60:
            for well in cycle_dict: #program will always finish last cycle through dictionary even if diff>30

                x_move = str(cycle_dict[well][0] - position[0])
                y_move = str(cycle_dict[well][1] - position[1])
                z_move = str(cycle_dict[well][2] - position[2])
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
    
def show_video(c):
    if not c.camera.IsGrabbing():
        c.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)            
    while c.camera.IsGrabbing():
        grabResult = c.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            c.imageWindow.SetImage(grabResult)
            if not c.imageWindow.IsVisible():
                c.imageWindow.Show()
        else:
            print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
            return False
        grabResult.Release()
        time.sleep(0.05)
        
 
def main(camera):

    machine = CNC()
    machine.position = [0,0,0]
    plate_num = machine.wellplate(plate_list)

    while True:
    
        print("\nCurrent position: ", machine.position)
        print("Enter a to move to a well. Enter b to jog the axes.")
        print("Enter p to take a picture.")
        print("Enter z for cycle")
        print("Enter h to home the machine")
        print("Enter n to change the well plate number.")
        print("Enter u to change camera parameters.")
        print("Enter c to enter a custom GRBL command. (CAUTION)")
        print("To stop the program, enter 'exit'.")

        main_input = input(">> ")
        if main_input == "a":
            machine.position = machine.well_move(plate_num, machine.position)
        elif main_input == "b":
            machine.position = machine.jog(camera, machine.position, xMin, xMax, yMin, yMax, zMin, zMax)
        elif main_input == "p":
            camera.acquire_image()
        elif main_input == "n":
            plate_num = machine.wellplate(plate_list)
        elif main_input == "z":
            machine.night_cycle(plate_96, camera, machine.position, camera)
        elif main_input == "h":
            machine.position = machine.home_cycle(machine.position)
        elif main_input == "c":
            setting = machine.configure_settings()
            machine.axes.write(setting.encode())
        elif main_input == "u":
            gain = camera.change_parameters()
        elif main_input == "exit":
            camera.imageWindow.Close()
            camera.camera.Close()
            sys.exit()
        else:
            print("Invalid input. Please try again.")
    print("ALARM(1): Reset to continue.")
    return False
    
if __name__ == "__main__":
    camera = Camera()
    t1 = threading.Thread(target = main, args = (camera,))
    t2 = threading.Thread(target = show_video, args = (camera,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()


