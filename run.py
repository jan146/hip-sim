from typing import TextIO
from sys import argv
import time

from machine import Machine
from loader import loadObj
from misc import freq2clockPeriod
from ui import Ui

import logging
logging.basicConfig(level=logging.WARN, format="{levelname:5s} : \t{funcName:s} : {message:s}", style="{")
logger = logging.getLogger()

# first memory address that will be printed
printMemAddr: int = 0
# how many rows will be printed in tui
printMemRows: int = 10
# is tui paused
paused: bool = False

# key release handler for tui app
def tuiReleaseKey(key):

	# use variables declared outside this function
	global printMemAddr, paused, m, keyboard

	match key:
		case keyboard.Key.left:									# type: ignore
			if printMemAddr - 16 >= Machine.minAddress:
				printMemAddr -= 16
		case keyboard.Key.right:								# type: ignore
			if printMemAddr + 16 + 15 <= Machine.maxAddress:
				printMemAddr += 16
		case keyboard.Key.enter:								# type: ignore
			paused = not paused
		case keyboard.Key.space:								# type: ignore
			pausedBefore: bool = paused
			paused = False
			step(m)
			paused = pausedBefore

# run machine m with breakpoints
# GUI-less version
def runOld(m: Machine, breakpoints: list[int]):

	# import keyboard module globally
	global keyboard
	from pynput import keyboard
	# add keyboard listener
	listener = keyboard.Listener(on_release=tuiReleaseKey)
	listener.start()

	dt: float = time.time()

	if not step(m):			# must do at least single step
		return

	# check timer and wait for clock period to finish
	dt = time.time() - dt
	if m.getClockPeriod() - dt > 0:
		time.sleep(m.getClockPeriod() - dt)

	dt = time.time()
	while (m.getPC() not in breakpoints) and step(m):
		# check timer and wait for clock period to finish
		dt = time.time() - dt
		if m.getClockPeriod() - dt > 0:
			time.sleep(m.getClockPeriod() - dt)
		dt = time.time()

# run machine m with breakpoints
def run(m: Machine, ui: Ui, fileName: str):

	objFileName: str = fileName
	inBreakpoint: bool = False

	while True:

		# check for reset
		if ui.getSimReset():
			# reset machine
			m = Machine()
			reset(m, objFileName, ui)

		if m.getPC() in ui.getBreakpointsList():

			if ui.getSimRunning():
				if inBreakpoint:
					# reset to normal running state and make single step
					ui.startStopUpdate(True)
					inBreakpoint = False
					stepTimed(m)
					continue
				else:
					ui.startStopUpdate(False)
					inBreakpoint = True

		if ui.getFrequency() >= 0:
			m.setClockPeriod(freq2clockPeriod(ui.getFrequency(), clockPeriod))
			ui.setFrequency(-1)

		# single step
		if ui.getStepFlag() and m.getIsRunning():
			stepTimed(m)
			ui.setStepFlag(False)

		# running simulation
		elif ui.getSimRunning():
			# check if PC is in breakpoints
			if not (m.getPC() in ui.getBreakpointsList()):
				if m.getIsRunning():
					stepTimed(m)
		else:
			# check if user selected new obj file
			if len(ui.getObjFile()) > 0:
				m = Machine()
				objFileName = ui.getObjFile()
				reset(m, ui.getObjFile(), ui)

		# update UI
		ui.updateAll(m)

def reset(m: Machine, objFileName: str, ui: Ui):
	# open obj file
	objFile: TextIO = open(objFileName, "rt")
	# load obj data into machine's memory
	loadObj(objFile, m)
	# close obj file
	objFile.close()
	# set initial PC
	m.setPC(m.getProgStart())
	# reset UI flags
	ui.setSimReset(False)
	ui.startStopUpdate(False)
	ui.setStepFlag(False)
	ui.setObjFile("")

def step(m: Machine) -> bool:

	# use variables declared outside this function
	global printMemRows, printMemAddr, tui, paused

	if tui:
		print(m.registers2str())
		print(m.getInstructionsString())
		print(m.mem2str(printMemAddr, printMemRows))

	if paused:
		time.sleep(m.getClockPeriod())
		return True

	# note PC and run single step/instruction
	PCBefore: int = m.getPC()
	m.execute()
	logger.debug("\n")
	logger.debug(m)

	# check if PC has changed
	PCAfter: int = m.getPC()
	if PCBefore == PCAfter:
		logger.info("infinite loop -> halt")
		m.setIsRunning(False)
		return False
	else:
		return True

def stepTimed(m: Machine) -> bool:
	# start timer
	dt = time.time()
	# do a step
	halt: bool = step(m)
	# wait for clock period to finish
	dt = time.time() - dt
	dt = m.getClockPeriod() - dt
	if dt > 0:
		time.sleep(dt)
	return halt

# set simulation/machine frequency
freq: int = 0
clockPeriod: float = freq2clockPeriod(freq, 0)

# create an instance ot the machine
m: Machine = Machine()
m.setClockPeriod(clockPeriod)

# initialize UI
ui: Ui = Ui()

# parse arguments
tui: bool = False
zeroOutput: bool = False

if len(argv) > 2:
	tui = (argv[2] == "tui")
	zeroOutput = (argv[2] == "none")

if len(argv) > 1:
	# open obj file
	objFile: TextIO = open(argv[1], "rt")
	# load obj data into machine's memory
	loadObj(objFile, m)
	# close obj file
	objFile.close()
	# set initial PC
	m.setPC(m.getProgStart())
	if tui:
		paused = False
		runOld(m, [])
	elif zeroOutput:
		runOld(m, [])
	else:
		run(m, ui, argv[1])
else:
	run(m, ui, "")
