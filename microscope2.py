#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 17 11:23:02 2019

@author: SamZhou
"""

import serial
import time

ser = serial.Serial('/dev/cu.usbmodem14201', baudrate = 115200, timeout = 1)

time.sleep(1)

print('hello')


xNeg = 'G91 X-1\n'
xPos = 'G91 X1\n'
yNeg = 'G91 Y-1\n'
yPos = 'G91 Y1\n'



"""def calc_position(xin, yin, zin, current_position):
    x = current_position[0] + xin
    y = current_position[1] + yin
    z = current_position[2] + zin
    return x, y, z"""

def move_well(user_input, position, plateDict, XYjogDict):
    #if user_input in plateDict:
    wellIntX = plateDict[user_input][0]
    wellIntY = plateDict[user_input][1]
    
    #In case machine is "memoryless", uncomment and fix variables
    xInt = wellIntX - position[0]
    yInt = wellIntY - position[1] 
        
    xStr = str(xInt)
    yStr = str(yInt)
        
    gCodePos = f'G91 X{xStr} Y{yStr}\n'
    ser.write(gCodePos.encode())
    """elif user_input in XYjogDict:
        xInt = XYjogDict[user_input][0]
        yInt = XYjogDict[user_input][1]
    
        xStr = str(xInt)
        yStr = str(yInt)
    
        XYjog = f'G91 X{xStr} Y{yStr}\n'
        ser.write(XYjog.encode())
        """
def jog_xy(jogIn):
    xInt = XYjogDict[jogIn][0]
    yInt = XYjogDict[jogIn][1]
    
    xStr = str(xInt)
    yStr = str(yInt)
    
    XYjog = f'G91 X{xStr} Y{yStr}\n'
    ser.write(XYjog.encode())
    
def jog_z(zJogIn):
    zInt = ZjogDict[zJogIn][2]
    zStr = str(zInt)
    Zjog = f'G91 Z{zStr}\n'
    ser.write(Zjog.encode())
    
def custom(gcode_prefix, custom_x, custom_y):
    custom_command = f'{gcode_prefix} X{custom_x} Y{custom_y}\n'
    ser.write(custom_command.encode())
    """gcode_input = input('Enter a Gcode prefix: ')
    if gcode_input == 'G0' or gcode_input == 'G91':
        x = input('Input a value for x: ')"""
        
    

plateDict = {
            'Home': [0,0,0],
            'H1': [9.0, 5.0, 0.0],
            'H2': [18.25, 5.25, 0.0],
            'G1': [9.0, 14.25, 0.0],
            'C8': [71.0, 49.75, 0.0]
            }

XYjogDict = {
            'a': [-1.0,0,0],
            'd': [1.0,0,0],
            'w': [0,1.0,0],
            's': [0,-1.0,0]
            }

ZjogDict = {
            'e': [0,0,1.0],
            'q': [0,0,-1.0]
            }    

gcode_dictionary = {
            'G0',
            'G28',
            'G91'
            }
custom_jog = {
            'w': None,
            'a': None,
            's': None,
            'd': None
            }



while True:
    #ser.write('$22 = 1'.encode())
    #ser.write('$3 = 6'.encode())    #invert X and Y axis direction
    #ser.write('$h'.encode())     #home the machine
    
    Xin = 0.0
    Yin = 0.0
    Zin = 0.0
    currentPos = [Xin,Yin,Zin]
    xMax =30.0
    yMax = 30.0
    zMax = 30.0
    xMin = 0.0
    yMin = 0.0
    zMin = 0.0
    
    
    
    while True:
        
        x = currentPos[0]
        y = currentPos[1]
        z = currentPos[2]
        print('\nCurrent Position = ', currentPos)        
        print('Press a to choose a well. Press b to jog X and Y. Press z to jog Z Press p to take a picture.')
        firstChoice = input('>> ')
        if firstChoice == 'a':
    
            while True:
    
                wellPlate = input('Which well (ex. A1)?\nPress Esc to go back.\n>> ')
                if wellPlate in plateDict and currentPos != [plateDict[wellPlate][0],plateDict[wellPlate][1],z]:
                    move_well(wellPlate,currentPos, plateDict, XYjogDict)
                    currentPos = [plateDict[wellPlate][0],plateDict[wellPlate][1],z]
                    break
                #elif wellPlate in XYjogDict and currentPos != [XYjogDict[wellPlate][0],XYjogDict[wellPlate][1],z]:
                 #   move_well(wellPlate, currentPos, plateDict, XYjogDict)
                elif wellPlate in plateDict and currentPos == [plateDict[wellPlate][0],plateDict[wellPlate][1],z]:
                    print('Already at ', wellPlate)
                    break
                elif wellPlate == 'Esc':
                    break
                else:
                    print('Invalid input. Please try again.')
                    
        elif firstChoice == 'b':
        
            while True:
            
                jogInput = input('Use the "wasd" keys to jog the X and Y axes. Press p to take a picture. Press Esc to exit jogging mode.\n>> ')

                if jogInput in XYjogDict:
                    x = x + XYjogDict[jogInput][0]
                    y = y + XYjogDict[jogInput][1]
                    #z = z + plateDict[jogInput][2]
                    if xMin <= x <= xMax and yMin <= y <= yMax:# and zMin <= z <= zMax:
                        jog_xy(jogInput)
                        currentPos = [x,y,z]
                        print('\nCurrent position = ', currentPos, '\n')

                    else:
                        x = x - XYjogDict[jogInput][0]
                        y = y - XYjogDict[jogInput][1]
                        #z = z - plateDict[jogInput][2]
                        currentPos = [x,y,z]
                        print('Beyond axis limit')
                elif jogInput == 'Esc':
                    break
                else:
                    print('Invalid input. Please try again.')
                    
        # Z axis needs to be separate for testing
        # due to power supply constraints            
                    
        elif firstChoice == 'z':
            
            while True:
                
                print('\nUse q and e to move z-axis up and down. Press Esc to exit.')
                jogInputZ = input('>> ')
                
                if jogInputZ in ZjogDict:
                    z = z + ZjogDict[jogInputZ][2]
                    if zMin <= z <= zMax:
                        jog_z(jogInputZ)
                        currentPos = [x,y,z]
                        print('\nCurrent position = ', currentPos, '\n')
                    else:
                        z = z - ZjogDict[jogInputZ][2]
                        currentPos = [x,y,z]
                        print('Beyond axis limit')
                elif jogInputZ == 'Esc':
                    break
                else:
                    print('Invalid input. Please try again.')


        
        elif firstChoice == 'c':
            gcode_command = input('Input a gcode command (Ex. "G0"):  ')
            if gcode_command == 'G0':
                print('LINEAR MOVE MODE')
                print('Moves microscope to position relative to origin.')
                x_input = input('Enter x coordinate: ')
                y_input = input('Enter y coordinate: ')
                x_input_float = float(x_input)
                y_input_float = float(y_input)
                x_diff = x_input_float - x
                y_diff = y_input_float - y
                if x_diff == 0 and y_diff == 0:
                    print('Already at (%s, %s)',x_input,y_input)
                elif x_input_float < xMin or x_input_float > xMax or y_input_float < yMin or y_input_float > yMax:
                    print('Beyond axis limit')
                else:
                    exe_statement = 'Executing {} X{} Y{}...'.format(gcode_command, x_input, y_input)
                    print(exe_statement)
                    custom(gcode_command, x_diff, y_diff)
                    x = x + x_diff
                    y = y + y_diff
                    currentPos = [x,y,z]
            elif gcode_command == 'G91':
                print('JOGGING MODE')
                print('Moves microscope x mm in specified direction relative to current position.')
                jog_increment = float(input('Enter jog increment (mm): '))
                if jog_increment > 0:
                    custom_jog['w'] = [0, jog_increment, 0]
                    custom_jog['a'] = [-jog_increment, 0, 0]
                    custom_jog['s'] = [0, -jog_increment, 0]
                    custom_jog['d'] = [jog_increment, 0, 0]
                    while True:
                        custom_jogInput = input('Use the "wasd" keys to jog the x and y axes.\n>> ')
                        if custom_jogInput in custom_jog:
                            x = round(x + custom_jog[custom_jogInput][0], 5)
                            y = round(y + custom_jog[custom_jogInput][1], 5)
                            if x < xMin or x > xMax or y < yMin or y > yMax:
                                x = round(x - custom_jog[custom_jogInput][0],5)
                                y = round(y - custom_jog[custom_jogInput][1],5)
                                print('Beyond axis limit')
                            else:
                                custom(gcode_command, custom_jog[custom_jogInput][0], custom_jog[custom_jogInput][1])
                                currentPos = [x,y,z]
                                print(currentPos)
                        elif custom_jogInput == 'Esc':
                            break
                        else:
                            print('Invalid input. Please try again.')
                else:
                    print('Input must be number greater than zero. Please try again.')
            elif gcode_command =='Esc':
                break
            else:
                print('Invalid input. Please try again.')
                
        elif firstChoice == 'p':
            pass
            #code for taking picture
            
        else:
            print('Invalid input. Please try again.')
