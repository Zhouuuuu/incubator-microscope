import serial
import time
import datetime
import pypylon
from pypylon import pylon
from pypylon import genicam
import os
import numpy as np
import cv2

plate_96 = {
    "Home": [0,0,0],
    "A1": [5,5,0],
    "B1": [10,10,0],
    "C1": [5,5,-5]
    }

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
[xMin, xMax] = [0.0, 30.0]
[yMin, yMax] = [0.0, 30.0]
[zMin, zMax] = [-15.0, 0.0]

class Camera:
    def __init__(self): #initialize instance of Camera
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        print("Using device:", self.camera.GetDeviceInfo().GetModelName())
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
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
        return True

    def acquire_image(self):
        print("Grabbing image...")
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
        self.camera.Close()
        return True
    
    def night_cycle(self, well_num):
        #home machine
        #how many wells
        #how long
        pass

class CNC:
    def __init__(self):
        self.axes = serial.Serial("COM4", baudrate = 115200, timeout = 1)
        #self.LED = serial.Serial #initialize LED
        time.sleep(2)
        print("Homing device...")
        #self.axes.write("$22 = 1\n".encode())
        self.axes.write("$x\n".encode())
        #self.axes.write("$h\n".encode())
        print("CNC initialized.")

    #def home_device(self):
    #    self.axes.write("$h\n".encode())
    #    return True

    def wellplate(self, plate_list):
        while True:
            print("Number of wells in well plate?")
            well_num = input(">> ")
            if num_wells in plate_list:
                well_num = plate_list[well_num]
                return well_num
            print("Please enter a valid number (6, 12, 24, 48, 96).")
        

    def well_move(self, plate, position):
        print("Which well (ex. A1)?")
        print("Type 'esc' to go back.")
        well = input(">> ")
        if well in plate and position == plate[well]:
            print("Already at", well)
        elif well in plate and position != plate[well]:
            x_move = str(plate[well][0] - position[0])
            y_move = str(plate[well][1] - position[1])
            z_move = str(plate[well][2] - position[2])
            gcode_command = f"G0 X{x_move} Y{y_move} Z{z_move}\n"
            self.axes.write(gcode_command.encode())
            position = plate[well]
            print("Current position:", position)
            return position
        elif well == "esc":
            print("Exited")
        else:
            print("Invalid input. Please try again.")
        return position
    
    def jog(self, jog_dict, position, xMin, xMax, yMin, yMax, zMin, zMax):
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
                    print("Use the 'wasd' keys to jog the X and Y axes. Use the q and e keys to jog the Z axis.\n>> ")
                    print("Type 'esc' to exit. Type 'back' to change the jog increment.")
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
                            print("Current position:", position)
                    elif jog_input == "back":
                        break
                    elif jog_input == "esc":
                        print("Current position:", position)
                        return position
                    else:
                        print("Invalid input. Please try again.")
                else:
                    print("Input must be a number greater than zero")
        except ValueError as error:
            print(error)
            print("Input must be number greater than zero.")
            return position
            

def main():
    camera = Camera()    
    machine = CNC()
    machine.position = [0,0,0]
    plate_num = machine.wellplate(plate_list)
    while True:
        print(machine.position)
        print("Enter a to move to a well. Enter b to jog the axes. Enter p to take a picture. To change the well plate number, enter c.")
        main_input = input(">> ")
        if main_input == "a":
            machine.position = machine.well_move(plate_num, machine.position)
        elif main_input == "b":
            machine.position = machine.jog(jog_dict, machine.position, xMin, xMax, yMin, yMax, zMin, zMax)
        elif main_input == "p":
            camera.acquire_image()
        elif main_input == "c":
            plate_num = machine.wellplate(plate_list)
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()
