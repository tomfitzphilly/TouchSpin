#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  rewrite_TS.py
#  
#  Copyright 2023 Tom Fitzsimons <tom.fitzsimons@wiffonline.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it with attribution under the terms of the GNU General Public License.
#
#  Conventions: variables are in camelCase (ex: cycleTime);
#  Functions are XxxXxx (ex: InitUsb)
#  Import the needed libraries
import string
import os.path
import csv
import datetime
import warnings
import os
import atexit
import random
import sys
import serial
ser = serial.Serial(port='/dev/ttyUSB0',
	baudrate = 38400,parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,
	timeout=5.0,xonxoff=1)
import pigpio #https://pypi.python.org/pypi/RPi.GPIO more info
import time
import timeit
from timeit import default_timer as timer
from tkinter import *
from tkinter import ttk
from tkinter import messagebox as tkmb

# Define needed variables
pi = pigpio.pi()
stop = 1
pin1 =  6     	# A
pin2 = 13       # A-
pin3 = 26       # B
pin4 = 19       # B-
stepPins = [6,13,19,26]
cycleTime = 4
stepTime = 0.0065 # This is the default step time
rpm = "0"
rpmStr = "0"
rpmTime = 0.03
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
eTime1 = 0.0
stepCounter = 0
startTime = timer()
direction = 0
cycleCnt = 0

# Set up a data storage file and site name
site = '../Desktop/TouchSpin_Test'
filename = site +'.csv'

# Prevent warnings from stopping the program
warnings.filterwarnings("ignore")

# Check for connection to USB Motor
try:
	ser = serial.Serial(port='/dev/ttyUSB0',baudrate = 38400,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,timeout=5.0,xonxoff=1)
	time.sleep(0.2)
	ser.flushOutput()
	ser.flushInput()
except:
	result = tkmb.showerror("Motor Controller Error","Motor Controller Not Found!\n\nCheck controller USB Connection\nand/or motor power supply then\nrestart this program.")   #, options)Motaskyesno("Python","You have not entered a Run ID!  Do you want to continue?")
	sys.exit()
	
# Add some FLAGS
flag_spin = 0
# Spinner not running
flag_run = 0
# Stepper not running
flag_stop = 1
# All motors stopped
flag_emStop = 0
# An emergency stop flag

#Set up and configure main GUI window
root = Tk()
root.title('TS Ver 2.0')
root.geometry("1000x400+100+100")# Width, Height, Down, Right

# Start up functions
def WriteSerial(cmd): #OK
	# Writes commands to the serial port for the USB motor
	#print(cmd)
	cmd = cmd + chr(13)
	#print(cmd)
	ser.write(cmd.encode())
	return

def ReadSerial(cmd,sLen): #OK
	# Reads data from the serial port for the USB motor
	retVal = ""
	strLen = int(sLen)
	while len(retVal) < strLen:
		retVal = retVal + ser.read(1)
	return(retVal)
	
def InitUsb(): #OK
	# Check for USB mnotor controller. Open port if found
	# Otherwise warn and Halt
	ser = serial.Serial(port='/dev/ttyUSB0',baudrate = 38400,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,timeout=5.0,xonxoff=1)
	try:
		ser = serial.Serial(port='/dev/ttyUSB0',baudrate = 38400,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,timeout=5.0,xonxoff=1)
		time.sleep(0.2)
		ser.flushOutput()
		ser.flushInput()
	except:
		result = tkmb.showerror("Motor Controller Error", "Motor Controller Not Found!\n\nCheck controller USB Connection\nand/or motor power supply then\nrestart this program.")   #, options)Motaskyesno("Python","You have not entered a Run ID!  Do you want to continue?")
		sys.exit()
	# Set baseline USB motor variables
	cmd="@0V*"
	cmd = cmd.encode('utf-8')
	ser.write(cmd)
	cmd = "@0KG10"
	cmd = cmd.encode()
	ser.write(cmd)
	cmd = "@0-"
	cmd = cmd.encode()
	ser.write(cmd)

InitUsb()

# Functions needed by the GUI
def StopNow():
	pass
	
def StopAll():
	# Stops all the motors
	global stepPins
	for pin in stepPins:
		pi.write(pin,0)
	StopSpin()
	return()
	
def MoveUp():
	# Calculate the time between steps and
	# Move sample platform start position UP
	global stepTime
	global cycleTime
	global flag_run
	sTime = ent_stepSpd.get();
	print(sTime)
	sTime = float(sTime)
	stepTime = ((1.0/float(sTime))/100.0)
	
	print(str(stepTime))
	flag_run=1
	
	maxSteps = int(ent_moveSteps.get())
	if maxSteps =="":
		maxSteps = 0
	stepCounter = 0

	print("Up: "  + str(maxSteps) + " steps")
		
	while ((stepCounter < maxSteps) and (flag_run==1)):
		try:
			pin = stepCounter % 4
			if pin == 0:
				Step1()
				time.sleep (.005)
			elif pin == 1:
				Step2()
				time.sleep (.005)
			elif pin == 2:
				Step3()
				time.sleep(.005)
			elif pin == 3:
				Step4()
				time.sleep(.005)
			#time.sleep(stepTime)
		except KeyboardInterrupt:
			flag_stop = 1
			StopAll()
			break;
		stepCounter += 1
		print(stepCounter)
	flag_run=0
		  
	root.update_idletasks()
	root.update()
		
	#StopAll()
	print("Move Up Completed!")
	return
	
def MoveDown():
	# Calculate the time between steps and
	# Move sample platform start position DOWN
	global stepTime
	global cycleTime
	global flag_run
	sTime = ent_stepSpd.get();
	print(sTime)
	sTime = float(sTime)
	stepTime = ((1.0/float(sTime))/100.0)
	
	print(str(stepTime))
	flag_run=1
	
	maxSteps = int(ent_moveSteps.get())
	if maxSteps =="":
		maxSteps = 0
	stepCounter = 0

	print("Down: "  + str(maxSteps) + " steps")
		
	while ((stepCounter < maxSteps) and (flag_run==1)):
		try:
			pin = stepCounter % 4
			if pin == 0:
				Step4()
				time.sleep (.005)
			elif pin == 1:
				Step3()
				time.sleep (.005)
			elif pin == 2:
				Step2()
				time.sleep(.005)
			elif pin == 3:
				Step1()
				time.sleep(.005)
			#time.sleep(stepTime)
		except KeyboardInterrupt:
			flag_stop = 1
			StopAll()
			break;
		stepCounter += 1
		print(stepCounter)
	flag_run=0
		  
	root.update_idletasks()
	root.update()
		
	#StopAll()
	print("Move Down Completed!")
	return

def StartSpin(): #OK
	# Start Spinner, wait 5 seconds and check the speed. Update GUI
	global ent_tgtSpd
	thisSpeed = ent_tgtSpd.get()
	thisSpeed = int(thisSpeed)
	if((thisSpeed <100) or (thisSpeed > 4000)):
		msgText = "Spindle Speed must be between\n100 and 4000 RPM>"
		tkmb.showerror("Spindle Speed Error!",msgText)
	print(thisSpeed)
	lbl_spinning.config(text="Spinning Up", bg = "yellow")
	root.update_idletasks()
	cmd = ("@0M"+str(thisSpeed))
	cmd.encode()
	WriteSerial(cmd)
	time.sleep(0.5)
	cmd = ("@0-")
	cmd.encode()
	WriteSerial(cmd)
	time.sleep(0.5)
	cmd="@0S"
	#print(cmd)
	WriteSerial(cmd)
	time.sleep(5.0)
	lbl_spinning.config(text="Spindle Running", bg = "pale green")
	SpinCheck()
	
def StopSpin(): #OK
	# Stop Spinner, Update the GUI
	lbl_spinning.config(text="Spindle Stopped", bg = "red")
	cmd = "@0,"
	cmd.encode()
	WriteSerial(cmd)
	lbl_actSpd.config(text="0")
	lbl_radSpd.config(text="0")

def SpinCheck(): #OK 
	# Check the spinner speed, Update the GUI
	global lbl_actSpd
	rpm=""
	ser.flushOutput()
	ser.flushInput()
	time.sleep(.2)
	sLen = 5
	cmd = "@0VM" + chr(13)
	cmd.encode()
	WriteSerial(cmd)
	rpm = ser.read(5)
	rpm = rpm.decode()
	print("Decoded RPM = ", rpm)
	rpmStr = str(rpm)
	rpmStr = rpmStr.strip("M")
	print ('RPM is: ', rpmStr)
	rpmStrFloat=float(rpmStr)
	rpmStrFormat = ("{:.0f}".format(rpmStrFloat))
	lbl_actSpd.config(text=rpmStrFormat)
	root.update_idletasks()
	print("Passing back: ", rpmStr)
	CalcSpeed(rpmStr)
	return(rpmStr)
	
def CalcSpeed(rpmStr): #OK
	# Calculates linear.radial speed
	rpmStr
	print("Here's the RPM: ")
	print(rpmStr)
	global pinDiam
	d=pinDiam.get()
	print(d)
	rpm = int(rpmStr)
	print("Here is CalcSpeed rpm: ", rpm)
	rps = (rpm/60)
	print("Here is the rps: ",rps)
	angVel = rps*2*3.1417
	print ("AngVel is: ", angVel)
	diam = pinDiam.get()
	diam = int(diam)
	radius = diam/2
	print("The radius is: ",radius)
	radialSpeed = radius*angVel
	radialSpeedStr = ("{:.2f}".format(radialSpeed))
	lbl_radSpd.config(text=radialSpeedStr)
	root.update_idletasks()
	pass
	
def GetDate(): #OK
	# Get the system date
	ent_runDate.delete(0,END)
	nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	ent_runDate.insert(0,nowTime)
	
def RunGPIOMotors(): #OK
	# Run the steppers through entered UP/DOWN cycles
	global stepTime
	global cycleTime
	global flag_stop
	global startTime
	global rpmTime
	global cycleCnt
	global flag_emStop
	flag_emStop = 0
	flag_stop = 0
	completedCycles=0

	sTime = ent_stepSpd.get();
	stepTime = ((1.0/float(sTime))/100.0)

	print("RunGPIO step Time",str(stepTime))

	if ent_runNum.get() == "":
		result = tkmb.askyesno("Python","You have not entered a Run ID!  Do you want to continue?")
		if result == 0:
			return
		
	if (ent_runDate.get() == ""):
		result = tkmb.askyesno("TouchSpin","You have not entered a Start DateTime!  Using System Time.")
		if result == 0:
			return
	else:
		GetDate()
		
	if (ent_numCycles.get() == ""):
		ent_numCycles.insert(0,"10")
	maxCycles = int(ent_numCycles.get())
	if(ent_numSteps.get() == ""):
		ent_numSteps.insert(0,"10")
	steps = int(ent_numSteps.get())
	cycleCnt = 0
	Label(root, text = "Completed Cycles " + str("        ")).grid(row=3, column=2,sticky='W')
	startTime = time.time()

	lbl_status.config(text = "Steppers Running", bg = "pale green")
	
	root.update_idletasks()
	root.update()
	
	global flag_run
	thisDate = ent_runDate.get()
	if(thisDate < "2000-01-01 00:00:00"):
		ent_runDate.delete(0,END)
		nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		ent_runDate.insert(0,nowTime.strip(" "))

	flag_run = 1
	while ((flag_run == 1) and (flag_emStop==0)):
		try:
			cycleCnt += 1
			RunRig(1,steps)
			
			RunRig(0,steps)
			Label(root, text = "Completed Cycles " + str(cycleCnt)).grid(row=3, column=2,sticky='W')
			
			if(cycleCnt >= maxCycles):
				StopAll()
				cycleCnt = 0
				completedCycles = (cycleCnt+1)
				flag_run = 0
				break
			if flag_stop == 1:
				StopAll()
				flag_run = 0
				stop = 0
				break;
		except KeyboardInterrupt:
			flag_run = 0
				
		if cycleCnt >= maxCycles or flag_stop == 1:
			Halt("S")
			Flag_stop = 0
			flag_run = 0
			
	lbl_status.config(text = "Steppers Stopped", bg = "red")
	#time.sleep(StepTime)

	return(startTime, maxCycles)
	
def RunRig(direction, steps): #OK
	# Runs the steppers through 1 up or down cycle
	global lbl_status
	# global stepTime
	global cycleTime
	global cycleCnt
	global flag_stop
	global rpmTime
	sTime = ent_stepSpd.get();
	print ("stepSpd = ",sTime)
	stepTime = ((1.0/float(sTime))/100.0)
	lbl_status.config(text="Steppers Running")
	#stop = 0
	eTime1 = 0.0
	stepCounter = 0
	startTime = timer()
	root.update_idletasks()
	
	if(direction == 0):	
		cycleCnt += 1
		print("Down")
	else:
		print("Up")

	while ((stepCounter < steps) and (flag_stop == 0)):
		pin = stepCounter % 4
		if(direction == 1):		
			if pin == 0:
				Step1()
				time.sleep(stepTime)
			elif pin == 1:
				Step2()
				time.sleep(stepTime)
			elif pin == 2:
				Step3()
				time.sleep(stepTime)
			elif pin == 3:
				Step4()
				time.sleep(stepTime)
		if(direction == 0):	
			if pin == 0:
				Step4()
				time.sleep(stepTime)
			elif pin == 1:
				Step3()
				time.sleep(stepTime)
			elif pin == 2:
				Step2()
				time.sleep(stepTime)
			elif pin == 3:
				Step1()
				time.sleep(stepTime)
		stepCounter += 1
		root.update_idletasks()
		root.update()
		if flag_stop == 1:
			StopAll()
			cycleCnt = 0
			break
	root.update()
	endTime = timer()

	eTime1 = endTime - startTime
	print(str(cycleCnt) + " - " + str(eTime1))
	return()

def Halt(opCode):
	lbl_status.config(text="Steppers Stopped", bg="red")
	lbl_spinning.config(text="Spindle Stopped", bg="red")
	pass
	
# def ProgQuit():
	# # Quit the program
	# StoreData()
	# MotorsOff()
	# for pin in stepPins:
	  # pi.write(pin,0)
	
	# cycleCnt = 0
	
	# root.destroy()

# Functions to run the system
def Step1(): #OK
	pass
	# define stepper motor steps at 200/rev 
	pi.write(pin1, 1)
	pi.write(pin2, 0)
	pi.write(pin3, 1)
	pi.write(pin4, 0)
	return()
	
def Step2(): #OK
	pass   
	pi.write(pin1, 0)
	pi.write(pin2, 1)
	pi.write(pin3, 1)
	pi.write(pin4, 0)
	return()
 
def Step3(): #OK
	pass    
	pi.write(pin1, 0)
	pi.write(pin2, 1)
	pi.write(pin3, 0)
	pi.write(pin4, 1)
	return()
	
def Step4(): #OK
	pass    
	pi.write(pin1, 1)
	pi.write(pin2, 0)
	pi.write(pin3, 0)
	pi.write(pin4, 1)
	return()

def StoreData(): #OK
	# Check to see if the data file exists.  If not create it.
	# If it exists append data to the 1st line of the file.
	global filename
	global stepTime
	global cycleTime
	global now
	global maxCycles

	start = startTime
	end = time.time()
	rTime = end - start
	
	runTime = "{0:.2f}".format(rTime)

	if os.path.exists(filename):
		f = open(filename,'r')
		temp = f.read()
		f.close()
	  
		f = open(filename, 'w')
		f.write("Start DateTime: "+str(now)
			+", Run ID: "+str(ent_runNum.get())
			+", Run Time: "+str(runTime)
			+" seconds, Spin Speed: "+str(ent_tgtSpd.get())
			+", Total Cycles: "+str(ent_numCycles.get())
			+", Steps: "+str(ent_numSteps.get())+ '\n')
		f.write(temp)
		f.close()
		Halt("S")
	else:
		append_write = 'w' # make a new file if not
		runData = open(filename,append_write)
		runData.write("Start DateTime: "+str(now)
			+", Run ID: "+str(ent_runNum.get())
			+", Run Time: "+str(runTime)
			+" seconds, Spin Speed: "+str(ent_tgtSpd.get())
			+", Total Cycles: "+str(ent_numCycles.get())
			+", Steps: "+str(ent_numSteps.get())+ '\n')
		runData.close()
	Halt("S")

	return()

def TurnOffMotors():
	global stepPins
	for pin in stepPins:
		pi.write(pin,0)
	cmd = "@0,"
	cmd.encode()
	WriteSerial(cmd)
	root.quit()
	
def MotorsOff():
	global flag_emStop
	global flag_stop
	flag_stop = 1
	flag_emStop=1
	lbl_radSpd.config(text="0")
	time.sleep(2)
	lbl_spinning.config(text="Spindle Stopped", bg = "red")
	time.sleep(2)
	global stepPins
	for pin in stepPins:
		pi.write(pin,0)
	cmd = "@0,"
	cmd.encode()
	WriteSerial(cmd)
	flag_stop = 0
	return(flag_emStop)
	
# Set up clean exits if "QUIT" not used
atexit.register(TurnOffMotors)

# Configure the GUI - Set up logical frames and populate with defaults

lf_step=LabelFrame (root, text = "Step Control",font = "bold", height=10)
lf_step.grid(row=1, column=1, sticky = "nw")
lbl_steps = Label(lf_step,
	text="Number of Steps",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW).grid(row=1, column=1)
ent_numSteps= Entry(lf_step, 
	width=7)
ent_numSteps.grid(row=1, column=2, sticky = NW)	
lbl_cycles = Label(lf_step,
	text="Number of Cycles",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_cycles.grid(row=2, column=1)
ent_numCycles= Entry(lf_step, 
	width=7)
ent_numCycles.grid(row=2, column=2, sticky = NW)	
lbl_stepSpd = Label(lf_step,
	text="Cycle Speed (4 - 16)",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_stepSpd.grid(row=3, column=1)
ent_stepSpd= Entry(lf_step, 
	width=7)
ent_stepSpd.insert(END,"10")
ent_stepSpd.grid(row=3, column=2, sticky = SW)
lbl_moveSteps = Label(lf_step,
	text = "# of MOVE Steps",
	width=12,
	padx = 2,
	pady=2,
	anchor=NW)
lbl_moveSteps.grid(row=1, column=3, columnspan=2)
ent_moveSteps= Entry(lf_step, 
	width=7)
ent_moveSteps.insert(END,500)
ent_moveSteps.grid(row=2, column=3, columnspan=2)
	
but_up=Button(lf_step,
	text="Move\nUP",
	command=MoveUp,
	width = 10).grid(row=3, column=3)
but_down=Button(lf_step,
	text="Move\nDOWN",
	command=MoveDown,
	width = 10).grid(row=3, column=4)

lf_spin = LabelFrame (root, text = "Spin Control",font = "bold", height = 10)
lf_spin.grid(row=2, column=1, sticky = "nw")
lbl_spinSpd = Label(lf_spin,
	text="Set Spin Speed",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_spinSpd.grid(row=1, column=1)
ent_tgtSpd= Entry(lf_spin, 
	width=7)
ent_tgtSpd.grid(row=1, column=2, sticky="nw")
ent_tgtSpd.insert(END,"2000")
lbl_speed = Label(lf_spin,
	text="Measured Speed\n'RPM'",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_speed.grid(row=2, column=1)
lbl_actSpd = Label(lf_spin,
	text=rpm,
	width=7,
	padx = 2,
	pady = 2,
	anchor = NE)
lbl_actSpd.grid(row=2, column=2, sticky="nw")
lbl_diam = Label(lf_spin,
	text="Disk to Pin\nDiameter in mm",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NE).grid(row=1, column=3)
# Set up radio buttons and create a variable to hold the choice
pinDiam = StringVar(lf_spin,"3") 
Radiobutton(lf_spin, text = "1", variable = pinDiam, value = "1").grid(row = 1, column=4)
Radiobutton(lf_spin, text = "3", variable = pinDiam, value = "3").grid(row=1, column=5)
lbl_linSpd = Label(lf_spin,
	text="Linear Speed\n'mm/sec'",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NE)
lbl_linSpd.grid(row=2, column=3)
lbl_radSpd = Label(lf_spin,
	text = "0",
	width = 12,
	padx = 2,
	pady = 2,
	anchor = NE)
lbl_radSpd.grid(row = 2, column = 4)

but_spinRun=Button(lf_spin,
	text="Start\nSpinner",
	command=StartSpin,
	width = 10).grid(row=4, column=1)
but_spinStop=Button(lf_spin,
	text="Stop\nSpinner",
	command=StopSpin,
	width = 10).grid(row=4, column=2)
but_SpinCheck=Button(lf_spin,
	text="Check\nSpeed",
	command=SpinCheck,
	width = 10).grid(row=4, column=3)

lf_runData = LabelFrame (root, text = "Run Data",font = "bold")
lf_runData.grid(row=1, column=2, sticky = "nw")
lbl_runNum = Label(lf_runData,
	text="Run Number",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_runNum.grid(row=1, column=1)
lbl_runDate = Label(lf_runData,
	text="Run Date",
	width=15,
	padx = 2,
	pady = 2,
	anchor = NW)
lbl_runDate.grid(row=2, column=1)
ent_runNum=Entry(lf_runData, 
	width=30)
ent_runNum.grid(row=1, column=2)
ent_runDate=Entry(lf_runData,
	width=30)
ent_runDate.grid(row=2, column=2)
but_useDate=Button(lf_runData,
	text="Use/Update\nSystem Date",
	command=GetDate,
	width = 10).grid(row=4, column=1)
but_StoreData=Button(lf_runData,
	text="Store\nData",
	command=StoreData,
	width = 10).grid(row=4, column=2)
lf_buttons = LabelFrame (root, text = "Program Control",font = "bold", height = 20, width = 20)
lf_buttons.grid(row=2, column=2, sticky = "nw")
but_runStart=Button(lf_buttons,
	text="Start\nRun",
	command=RunGPIOMotors,
	width = 10).grid(row=4, column=1)
but_runStop=Button(lf_buttons,
	text="Stop\nRun",
	command=Halt,
	width = 10).grid(row=4, column=2)
but_quit=Button(lf_buttons,
	text="QUIT\nProgram",
	command=TurnOffMotors,
	width = 10).grid(row=4, column=3)
but_emergStop=Button(lf_buttons,
	text="Emergency\nStop",
	command=MotorsOff,
	bg="red",
	width = 10).grid(row=5, column=2)

# ROOT Info Labels
lbl_status = Label(root,
	text="Steppers Stopped",
	width=15,
	padx = 2,
	pady = 2,
	bg = "red",
	anchor = NW)
lbl_status.grid(row=3, column=1)
lbl_spinning = Label(root,
	text = "Spindle Stopped",
	width = 15,
	padx = 2,
	pady = 2,
	bg= "red",
	anchor = NW)
lbl_spinning.grid(row=4, column = 1)

# Function to run the program as a loop
mainloop()
