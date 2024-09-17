#!/usr/bin/python3
import os
import time
import re
import serial
from os.path import exists

# Define constants
remoteChannel = 0
remotePin = 14

# Button definitions
ButtonsNames = ["CHANNEL1", "CHANNEL2", "CHANNEL3", "CHANNEL4", "CHANNEL5", "CHANNEL6", "CHANNEL7", "CHANNEL8", "CHANNEL9", "CHANNEL10", "CHANNEL11", "CHANNEL12"]
Buttons = [0x490b, 0x4907, 0x4903, 0x490a, 0x4906, 0x4902, 0x4909, 0x4905, 0x4901, 0x4925, 0x4926, 0x4927]

ser = None  # Serial object will be initialized in setup()
lastRemoteTime = 0.0

def Write(str):
    global ser
    string = str + "\r\n"
    arr = bytes(string, 'utf-8')
    ser.write(arr)

def Read():
    global ser
    x = ser.read(20)
    return x.decode("utf-8") 

def SendCommand(str):
    Write(str)
    # res = Read()  # Commented out as it's not used
    # return len(res) > 2  # Commented out as it's not used

def ChangeInput(input):
    cmd = str(input) + "*!"
    return SendCommand(cmd)

def restartRemoteService():
    os.system('sudo pkill ir-keytable')
    global myRemoteLogThread
    myRemoteLogThread = threading.Thread(target=prepareRemoteLog)
    myRemoteLogThread.start()

def setup():
    ReadOnly(True)
    restartRemoteService()
    #myRemoteThread = threading.Thread(target=remoteThread)
    #myRemoteThread.start()
    global ser
    ser = serial.Serial(
        port='/dev/ttyUSB0',  # Replace ttyS0 with ttyAM0 for Pi1, Pi2, Pi0
        baudrate=9600,  # assuming default
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=30
    )

def ReadOnly(val):
    if val:
        cmd = 'sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot'
    else:
        cmd = 'sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot'
    os.system(cmd)
    os.system('sudo chmod 777 /tmp/remoteLog')

def prepareRemoteLog():
    print("Prepare Remote Log ")
    os.system('sudo rm -rf /tmp/remoteLog')
    os.system('sudo touch /tmp/remoteLog')
    os.system('sudo chmod 777 /tmp/remoteLog')
    os.system('sudo stdbuf -i0 -e0 -o0 ir-keytable -c -p all -t > /tmp/remoteLog')

def getRemoteData():
    global lastRemoteTime
    fileExists = exists('/tmp/remoteLog')
    if not fileExists:
        return -1
    with open("/tmp/remoteLog", "r") as f:
        lines = f.readlines()
    
    if len(lines) >= 3:
        txtsplit = lines[-2].split()
        curTime = txtsplit[0][:-2]
        curCmd = txtsplit[-1]
        try:
            curTime = float(curTime)
            if curTime != lastRemoteTime:
                lastRemoteTime = curTime
                curCmd = int(curCmd, 16)
                retVal = curCmd
            else:
                retVal = -1
        except ValueError:
            print("conversion error")
            retVal = -1
        
        if os.path.getsize("/tmp/remoteLog") > 16000000:
            restartRemoteService()
            lastRemoteTime = 0
        return retVal

def extract_channel_number(text):
    pattern = r'CHANNEL\s*(\d{1,2})'
    match = re.search(pattern, text)
    if match:
        return int(match.group(1))
    return None

def remoteThread():
    global Buttons
    global ButtonsNames
    global remoteChannel
    
    while True:
        inData = getRemoteData()
        if inData < 0:
            time.sleep(1)
            continue
        
        # Convert inData to hexadecimal string
        hex_inData = hex(inData)
        print(f"Processing {hex_inData}")
        
        # Find the index of the button code in the Buttons list
        if inData in Buttons:
            index = Buttons.index(inData)
            button_name = ButtonsNames[index]
            print(f"Found button {hex_inData}")
            
            if "CHANNEL" in button_name:
                print(button_name)
                remoteChannel = extract_channel_number(button_name)
                ChangeInput(remoteChannel)
            else:
                print("Remote key not found!\n")
        else:
            print("Button not found!\n")
        
        time.sleep(1)  # To avoid busy-waiting

setup()
ChangeInput(1)
remoteThread()
    
