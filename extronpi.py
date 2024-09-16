#!/usr/bin/env python
import time
import serial
import RPi.GPIO as GPIO
import re
from datetime import datetime
global ser
global res
res = None
ser = None
global mode
mode = 0
remotePin = 14
debug = True

def extract_code_and_time(input_string):
	# Check if the word "scancode" is in the input string
	if "scancode" not in input_string:
		return False, None, None
	
	# Regular expression to match floating point number and hexadecimal code
	pattern = r"(\d+\.\d+):.*scancode\s*=\s*(0x[0-9A-Fa-f]{4})"
	
	# Search for the pattern in the input string
	match = re.search(pattern, input_string)
	
	if match:
		# Extract the floating point number and hexadecimal code
		time = float(match.group(1))
		code = match.group(2)
		return True, time, code
	else:
		# If no match is found, return False with None values
		return False, None, None

def Setup():

	global remotePin
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(remotePin, GPIO.IN)
	global ser
	ser = serial.Serial(
			port='/dev/ttyUSB0', #Replace ttyS0 with ttyAM0 for Pi1,Pi2,Pi0
			baudrate = 9600, #assuming default
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=1

#			timeout=30
	)

#for commands too lazy to compute checksum
def Write(str):
	global ser
	string = str + "\r\n"
	if debug:
		print("Write: " + string)
	arr = bytes(string, 'utf-8')
	ser.write(arr)

def Read():
	global ser
	x = ser.read(20)
	if debug:
		print("Read:  " + x.decode("utf-8"))
	return x.decode("utf-8") 

def GetHexValue(nVal):
	base = None
	if nVal < 0:
		base = GetNegHex(nVal)
	else:
		base = hex(int(nVal)).replace("0x","")
		while (len(base) < 6):
			base = "0" + base
	return base


def SendCommand(str):
	print("Paco3")
	global res
	Write(str)
	print("Paco4")

#	res = Read()
	print("Paco5")

#	if len(res) > 2:
#		return True
#	return False

def ChangeInput(input):
	base = int(input)
	cmd = str(base) + "!"
	#SendCommand(cmd)
	#return SendCommand(cmd)
	return True

def convertHex(binaryValue):
	tmpB2 = int(str(binaryValue),2) #Tempary proper base 2
	return hex(tmpB2)

def getBinary():
	print("binary")
	global remotePin
	#Internal vars
	num1s = 0 #Number of consecutive 1s read
	binary = 1 #The binary value
	command = [] #The list to store pulse times in
	previousValue = 0 #The last value
	value = GPIO.input(remotePin) #The current value
	
	#Waits for the sensor to pull pin low
	while value:
		value = GPIO.input(remotePin)
		
	#Records start time
	startTime = datetime.now()
	
	while True:
		#If change detected in value
		if previousValue != value:
			now = datetime.now()
			pulseTime = now - startTime #Calculate the time of pulse
			startTime = now #Reset start time
			command.append((previousValue, pulseTime.microseconds)) #Store recorded data
			
		#Updates consecutive 1s variable
		if value:
			num1s += 1
		else:
			num1s = 0
		
		#Breaks program when the amount of 1s surpasses 10000
		if num1s > 10000:
			break
			
		#Re-reads pin
		previousValue = value
		value = GPIO.input(remotePin)
		
	#Converts times to binary
	for (typ, tme) in command:
		if typ == 1: #If looking at rest period
			if tme > 1000: #If pulse greater than 1000us
				binary = binary *10 +1 #Must be 1
			else:
				binary *= 10 #Must be 0
			
	if len(str(binary)) > 34: #Sometimes, there is some stray characters
		binary = int(str(binary)[:34])
	return binary



ButtonsNames = ["CHANNEL1","CHANNEL2","CHANNEL3","CHANNEL4","CHANNEL5","CHANNEL6","CHANNEL7","CHANNEL8","CHANNEL9","CHANNEL10","CHANNEL11","CHANNEL12"]
Buttons = [0x490b,0x4907,0x4903,0x490a,0x4906,0x4902,0x4909,0x4905,0x4901,0x4925,0x4926, 0x4927]
Setup()
ChangeInput(1)
myRes = False

while True:
	try:
		inData = convertHex(getBinary()) #Runs subs to get incoming hex value
		print(inData)
		for button in range(len(Buttons)):#Runs through every value in list
			if hex(Buttons[button]) == inData: #Checks this against incomming
				if ButtonsNames[button].find("CHANNEL") != -1:
					chanVal = ButtonsNames[button][7:len(ButtonsNames[button])]
					chanVal = int(chanVal)
					ChangeInput(chanVal)
					break

	except Exception as e:
		print("Remote exception caught " + str(e))
