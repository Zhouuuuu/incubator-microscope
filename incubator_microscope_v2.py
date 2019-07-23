import serial
import time
import datetime
import pypylon
from pypylon import pylon
from pypylon import genicam
import os
import numpy as np
import cv2

plate_dict = {
    "Home": [0,0,0],
    "A1": [5,5,0],
    "B1": [10,10,0],
    "C1": [5,5,-5]
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
[zMin, zMax] = [0.0, -15.0]

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
        print("Saving image...")
        ipo = pylon.ImagePersistenceOptions()
        ipo.SetQuality(100)
        filename = "test_file"
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
    
    def night_cycle(self):
        #home machine
        #how many wells
        #how long
        pass

class CNC:
    def __init__(self):
        self.axes = serial.Serial("COM4", baudrate = 115200, timeout = 1)
        time.sleep(5)
        #self.LED = serial.Serial #initialize LED
        print("Homing device...")
        #self.axes.write("$22 = 1\n".encode())
        self.axes.write("$x\n".encode())
        #self.axes.write("$h\n".encode())

    #def home_device(self):
    #    self.axes.write("$h\n".encode())
    #    return True

    def well_move(self, plate, position):
        well = input("Which well (ex. A1)?")
        print("Type 'esc' to go back.")
        print(">> ")
        if well in plate and position == plate[well]:
            print("Already at", well)
        elif well in plate and position != plate[well]:
            well_x = str(plate[well][0])
            well_y = str(plate[well][1])
            well_z = str(plate[well][2])
            gcode_command = f"G0 X{well_x} Y{well_y} Z{well_z}\n"
            self.axes.write(gcode_command.encode())
            position = plate[well]
            print("Current position:", position)
            return position
        elif well == "esc":
            print("Exited")
        else:
            print("Invalid input. Please try again.")
        return position
    
    def jog(self, jog_increment, jog_dict, position, xMin, xMax, yMin, yMax, zMin, zMax):
        while True:
            jog_input = input("Use the 'wasd' keys to jog the X and Y axes. Use the q and e keys to jog the Z axis.\n>> ")
            print("Type 'esc' to exit.")
            if jog_input in jog_dict:
                x = round(self.position[0] + jog_dict[jog_input][0], 5)
                y = round(self.position[1] + jog_dict[jog_input][1], 5)
                z = round(self.position[2] + jog_dict[jog_input][2], 5)
                if x < xMin or x > xMax or y < yMin or y > yMax or z < zMin or z > zMax:
                    print("Beyond axis limit.")
                else:
                    gcode_command = "G91 X{jog_dict[jog_input][0]} Y{jog_dict[jog_input][1]} Z{jog_dict[jog_input][2]}\n"
                    self.axes.write(gcode_command.encode())
                    position = [x,y,z]
                    print("Current position:", self.position)
            elif jog_input == "esc":
                print("Current position:", self.position)
                return position
            else:
                print("Invalid input. Please try again.")

def main():
    camera = Camera()
    machine = CNC()
    machine.position = [0,0,0]
    while True:
        print(machine.position)
        print("Enter a to move to a well. Enter b to jog the axes. Enter p to take a picture.")
        main_input = input(">> ")
        if main_input == "a":
            machine.position = machine.well_move(plate_dict, machine.position)
        elif main_input == "b":
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
                    machine.position = machine.jog(jog_increment, jog_dict, machine.position, xMin, xMax, yMin, yMax, zMin, zMax)
            except ValueError as error:
                print(error)
                print("Input must be number greater than zero.")
        elif main_input == "p":
            camera.acquire_image()
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()
