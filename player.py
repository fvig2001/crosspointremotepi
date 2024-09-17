#!/usr/bin/python3
from multiprocessing import Process, Lock
import RPi.GPIO as GPIO
import os
import secrets
import subprocess, time, sys
import subprocess

from subprocess import PIPE, Popen, STDOUT, check_output, CalledProcessError
from datetime import datetime
from os.path import exists
import threading
from threading import Thread

initDone = False
remoteChannel = 0
remotePin = 14

myRemoteLogThread = None

ButtonsNames = ["CHANNEL1","CHANNEL2","CHANNEL3","CHANNEL4","CHANNEL5","CHANNEL6","CHANNEL7","CHANNEL8","CHANNEL9","CHANNEL10","CHANNEL11","CHANNEL12"]
Buttons = [0x490b,0x4907,0x4903,0x490a,0x4906,0x4902,0x4909,0x4905,0x4901,0x4925,0x4926, 0x4927]
mutex = Lock()
def restartRemoteService():
	tempCmd = 'sudo pkill ir-keytable'
	os.system(tempCmd)			
	global myRemoteLogThread
	myRemoteLogThread = threading.Thread(target=prepareRemoteLog)
	myRemoteLogThread.start()

def setup():
	ReadOnly(True)
	restartRemoteService()
	myRemoteThread = threading.Thread(target=remoteThread)
	myRemoteThread.start()

	
def ReadOnly(val):
	cmd = ""
	if val:
		cmd = 'sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot'
	else:
		cmd = 'sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot'
	os.system(cmd)
	cmd = 'sudo chmod 777 /tmp/remoteLog'
	os.system(cmd)


def prepareRemoteLog():
	print("Prepare Remote Log ")
	tempCmd = 'sudo rm -rf /tmp/remoteLog'
	os.system(tempCmd)
	tempCmd = 'sudo touch /tmp/remoteLog'
	os.system(tempCmd)
	tempCmd = 'sudo chmod 777 /tmp/remoteLog'
	os.system(tempCmd)
	tempCmd = 'sudo stdbuf -i0 -e0 -o0 ir-keytable -c -p all -t > /tmp/remoteLog'
	os.system(tempCmd)
		

def getRemoteData():
	global lastRemoteTime
	retVal = -1
	fileExists = exists('/tmp/remoteLog')
	if not fileExists:
		return -1
	f = open("/tmp/remoteLog", "r")
	lines = f.readlines()
	f.close()
	fileLen = len(lines)
	if fileLen >= 3:
		#print (lines[fileLen-2])
		txtsplit = lines[fileLen-2].split()
		curTime = txtsplit[0]
		curTime = curTime[0:len(curTime)-2]
		curCmd = txtsplit[len(txtsplit)-1]
		try:
			curTime = float(curTime)
			if curTime != lastRemoteTime:
				lastRemoteTime = curTime
				curCmd = int(curCmd,16)
				retVal = curCmd

		except ValueError:
			print("conversion error")
			retVal = -1
		fileSize = os.path.getsize("/tmp/remoteLog") #if file is greater than 16 MB, restart remote log to save space
		if fileSize > 16000000:
			restartRemoteService()
			lastRemoteTime = 0 
	return retVal

def remoteThread():	
	global altChannel
	global player
	global adjustedTime
	global timeLeft
	global overlapTime
	global Buttons
	global ButtonsNames
	global origTimeLeft
	global remoteChannel
	global channelIndex
	global stopPlayer
	global pausePlayer
	global curIndex
	global videos
	global channelChanged
	global curVolume
	global volumeScale
	global isCommentary
	global curFile
	global remoteAspectOverride
	global lastRemoteTime
	global isLCD
	global isMute
	lastRemoteTime = 0.0
	while True:
		inData = getRemoteData()
		if inData < 0:
			time.sleep(1)
			continue
		oldchannelIndex = remoteChannel
		inData = str(hex(inData))
		print("processing " + str(inData))
		for button in range(len(Buttons)):#Runs through every value in list
			if (Buttons[button]) == inData:

				print("Found button " + str(Buttons[button]))

				if ButtonsNames[button].find("CHANNEL") != -1:
					print(ButtonsNames[button])

					chanVal = ButtonsNames[button][7:len(ButtonsNames[button])]
					chanVal = int(chanVal)

					remoteChannel = chanVal
					channelChanged = True
					break

				else:
					print("Remote key not found!\n")

setup()
while (True):
	time.sleep(1)