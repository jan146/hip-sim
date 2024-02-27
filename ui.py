import tkinter as tk
from tkinter.filedialog import askopenfilename
from machine import Machine

import logging
logger = logging.getLogger(__name__)

class Ui():

	# ui elements
	window: tk.Tk				# whole app window

	col0: tk.Frame				# left side of window
	registers: tk.Frame			# container for registersText
	registersText: tk.Text		# registers status
	instructions: tk.Frame		# container for instructionsText
	instructionsText: tk.Text	# last N instructions
	interface: tk.Frame			# container for buttons & frequency containers
	interfaceButtons: tk.Frame	# container for buttons
	interfaceFreq: tk.Frame		# container for frequency menu
	openButton: tk.Button		# button for opening file choose prompt
	resetButton: tk.Button		# button for resetting machine
	startStopButton: tk.Button	# button for starting/stopping simulation
	stepButton: tk.Button		# button for making single simulation step
	frequencyHelp: tk.Text		# text explaining frequency
	frequencyInput: tk.Text		# input field to change machine's frequency

	col1: tk.Frame				# right side of window
	memory: tk.Frame			# container for memory display
	memoryText: tk.Text			# representation of memory in hex digits
	memoryMove: tk.Frame		# container for memory move containers
	memoryMoveLF: tk.Frame		# container for memory move left
	memoryMoveRF: tk.Frame		# container for memory move left
	memoryMoveLB: tk.Button		# move "up" in memory view
	memoryMoveRB: tk.Button		# move "down" in memory view
	breakpoints: tk.Frame		# container for breakpoints
	breakpointsLF: tk.Frame		# left container for breakpoints
	breakpointsHelp: tk.Text	# breakpoints user instructions
	breakpointsInput: tk.Text	# breakpoints text area
	breakpointsText: tk.Text	# printed list of user input breakpoints
	breakpointsRF: tk.Frame		# right container for breakpoints
	breakpointsBtn: tk.Button	# breakpoints sumbit button

	# constants
	defaultFont: tuple[str, int] = ("monospace", 10)
	foregroundColor: str = "#FFFFFF"
	backgroundColor: str = "#222222"
	backgroundColorAlt: str = "#333333"
	col0_width = 300
	col1_width = 800
	memRows = 16
	memRowWidth = 16

	# index of first memory byte displayed
	memoryIndex: int

	# breakpoints from user input
	breakpointsList: list[int]

	# used to check if simulation is running
	simRunning: bool

	# used to check if single step should be made
	stepFlag: bool

	# used to check if simulation should reset
	simReset: bool

	# used to check if frequency is to be changed
	frequency: int

	# used to check if new obj should be loaded
	objFile: str

	def __init__(self):

		# create main window
		self.window = tk.Tk()
		self.window.geometry("1100x800")
		self.window.title("sictools from wish")
		self.window.tk_setPalette(foreground=Ui.foregroundColor, background=Ui.backgroundColor)
		self.window.option_add("*Font", Ui.defaultFont)

		# left side of screen: registers, instructions and controls
		self.col0 = tk.Frame(master=self.window, width=Ui.col0_width, height=800)
		self.col0.pack(fill=tk.Y, side=tk.LEFT)
		
		# initialize container elements
		self.registers = tk.Frame(master=self.col0, height=250, width=Ui.col0_width)
		self.registers.pack(fill=tk.X, side=tk.TOP, expand=True)
		self.instructions = tk.Frame(master=self.col0, height=50, width=Ui.col0_width)
		self.instructions.pack(fill=tk.X, side=tk.TOP, expand=True, pady=0)
		self.interface = tk.Frame(master=self.col0, height=250, width=Ui.col0_width)
		self.interface.pack(fill=tk.X, side=tk.TOP, expand=True)
		
		# right side of screen: memory and breakpoints
		self.col1 = tk.Frame(master=self.window, width=Ui.col1_width, height=800)
		self.col1.pack(fill=tk.Y, side=tk.LEFT)
		
		# initialize container elements
		self.memory = tk.Frame(master=self.col1, height=650, width=Ui.col1_width)
		self.memory.pack(fill=tk.X, side=tk.TOP, expand=True)
		self.memoryMove = tk.Frame(master=self.col1, height=50, width=Ui.col1_width)
		self.memoryMove.pack(fill=tk.X, side=tk.TOP, expand=True)
		self.breakpoints = tk.Frame(master=self.col1, height=100, width=Ui.col1_width)
		self.breakpoints.pack(fill=tk.X, side=tk.TOP, expand=True)
		
		self.registersText = tk.Text(master=self.registers, height=4, width=50, highlightthickness=0, bd=0)
		self.registersText.pack(anchor=tk.CENTER, expand=True, fill=tk.BOTH)
		self.registersText.tag_configure("center", justify="center")

		self.instructionsText = tk.Text(master=self.instructions, height=10, width=50, highlightthickness=0, bd=0)
		self.instructionsText.pack(anchor=tk.CENTER, expand=True, fill=tk.BOTH)
		self.instructionsText.tag_configure("center", justify="center")

		self.memoryText = tk.Text(master=self.memory, height=17, width=50, highlightthickness=0, bd=0)
		self.memoryText.pack(anchor=tk.CENTER, expand=True, fill=tk.BOTH)
		self.memoryText.tag_configure("center", justify="center")
		self.memoryText.insert("1.0", "{:5s} +0 +1 +2 +3 +4 +5 +6 +7 +8 +9 +A +B +C +D +E +F".format(""))
		self.memoryIndex = 0

		self.memoryMoveLF = tk.Frame(master=self.memoryMove, background=Ui.backgroundColor)
		self.memoryMoveLF.pack(side=tk.LEFT, fill=tk.X, expand=True)
		self.memoryMoveLB = tk.Button(master=self.memoryMoveLF, text="<--", bg=Ui.backgroundColorAlt, height=1, width=5, command=self.decMemIndex)
		self.memoryMoveLB.pack(anchor="e", expand=True, padx=10)

		self.memoryMoveRF = tk.Frame(master=self.memoryMove, background=Ui.backgroundColor)
		self.memoryMoveRF.pack(side=tk.RIGHT, fill=tk.X, expand=True)
		self.memoryMoveRB = tk.Button(master=self.memoryMoveRF, text="-->", bg=Ui.backgroundColorAlt, height=1, width=5, command=self.incMemIndex)
		self.memoryMoveRB.pack(anchor="w", expand=True, padx=10)

		self.breakpointsLF = tk.Frame(master=self.breakpoints, height=100, width=550)
		self.breakpointsLF.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

		self.breakpointsRF = tk.Frame(master=self.breakpoints, height=100, width=75)
		self.breakpointsRF.pack(side=tk.RIGHT, expand=True)

		self.breakpointsHelp = tk.Text(master=self.breakpointsLF, background=Ui.backgroundColor, height=2, highlightthickness=0, bd=0)
		self.breakpointsHelp.pack(side=tk.TOP, fill=tk.X, expand=False)
		self.breakpointsHelp.insert("1.0", "Breakpoints: enter comma separated addresses in decimal or hexadecimal form (e. g.: \"1234, 0xff, 96\")")
		self.breakpointsHelp.configure(state="disabled", wrap="word")

		self.breakpointsInput = tk.Text(master=self.breakpointsLF, background=Ui.backgroundColorAlt, height=1)
		self.breakpointsInput.pack(expand=True, fill=tk.X)
		self.breakpointsInput.bind("<Return>", self.updateBreakpointsList)
		self.breakpointsInput.bind("<KP_Enter>", self.updateBreakpointsList)

		self.breakpointsText = tk.Text(master=self.breakpointsLF, background=Ui.backgroundColor, height=1, highlightthickness=0, bd=0)
		self.breakpointsText.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
		self.breakpointsText.insert("1.0", "[]")
		self.breakpointsText.configure(state="disabled")

		self.breakpointsSubmit = tk.Button(master=self.breakpointsRF, text="Submit", bg=Ui.backgroundColorAlt, height=2, width=5, command=self.updateBreakpointsList)
		self.breakpointsSubmit.pack(expand=True)
		self.breakpointsList = []

		self.interfaceButtons = tk.Frame(master=self.interface, background=Ui.backgroundColor, height=100)
		self.interfaceButtons.pack(side=tk.TOP, fill=tk.X, expand=True)

		self.openButton = tk.Button(master=self.interfaceButtons, text="Load obj", bg=Ui.backgroundColorAlt, height=1, width=7, command=lambda: self.setObjFile(askopenfilename(filetypes=[("object files", "*.obj")])))
		self.openButton.place(x=10, y=0)
		self.objFile = ""

		self.resetButton = tk.Button(master=self.interfaceButtons, text="Reset", bg=Ui.backgroundColorAlt, height=1, width=7, command=lambda: self.setSimReset(True))
		self.resetButton.place(x=100, y=0)
		self.simReset = False

		self.startStopButton = tk.Button(master=self.interfaceButtons, text="Start", bg=Ui.backgroundColorAlt, height=1, width=7, command=lambda: self.startStopUpdate(not self.getSimRunning()))
		self.startStopButton.place(x=10, y=50)
		self.simRunning = False

		self.stepButton = tk.Button(master=self.interfaceButtons, text="Step", bg=Ui.backgroundColorAlt, height=1, width=7, command=lambda: self.setStepFlag(True))
		self.stepButton.place(x=100, y=50)
		self.stepFlag = False

		self.interfaceFreq = tk.Frame(master=self.interface, background=Ui.backgroundColor, height=100)
		self.interfaceFreq.pack(side=tk.TOP, fill=tk.X, expand=True)

		self.frequencyHelp = tk.Text(master=self.interfaceFreq, background=Ui.backgroundColor, height=1, highlightthickness=0, bd=0, width=0)
		self.frequencyHelp.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10)
		self.frequencyHelp.insert("1.0", "Frequency [Hz]:")
		self.frequencyHelp.configure(state="disabled", wrap="word")

		self.frequencyInput = tk.Text(master=self.interfaceFreq, background=Ui.backgroundColorAlt, height=1, width=0)
		self.frequencyInput.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10)
		self.frequencyInput.bind("<Return>", self.updateFrequency)
		self.frequencyInput.bind("<KP_Enter>", self.updateFrequency)
		self.frequency = -1

		# window.mainloop()

	def getSimReset(self) -> bool:
		return self.simReset

	def getSimRunning(self) -> bool:
		return self.simRunning

	def getStepFlag(self) -> bool:
		return self.stepFlag

	def getObjFile(self) -> str:
		return self.objFile

	def getFrequency(self) -> int:
		return self.frequency

	def setSimReset(self, simReset: bool):
		self.simReset = simReset

	def setStepFlag(self, stepFlag: bool):
		self.stepFlag = stepFlag

	def setObjFile(self, objFile: str):
		self.objFile = objFile

	def setFrequency(self, frequency: int):
		self.frequency = frequency

	def getBreakpointsList(self) -> list[int]:
		return self.breakpointsList

	def startStopUpdate(self, running: bool):
		self.simRunning = running
		self.startStopButton.configure(text=("Stop" if running else "Start"))

	def updateFrequency(self, *event):
		frequencyString = self.frequencyInput.get("1.0", tk.END)
		self.frequencyInput.delete("1.0", tk.END)
		try:
			self.frequency = int(frequencyString)
		except ValueError:
			pass

	def updateBreakpointsList(self, *event):
		
		# update breakpointsList values
		strings = [x.strip() for x in self.breakpointsInput.get("1.0", tk.END).strip().split(",")]
		if strings == [""]:
			self.breakpointsList = []
		else:
			try:
				self.breakpointsList = [(int(x, 16) if x.startswith("0x") else int(x)) for x in strings]
			except ValueError:
				logger.warn("invalid breakpoints in user input")
				self.breakpointsList = []

		# show them on screen
		self.breakpointsText.configure(state="normal")
		self.breakpointsText.delete("1.0", tk.END)
		self.breakpointsText.insert("1.0", str(self.breakpointsList))
		self.breakpointsText.update()
		self.breakpointsText.configure(state="disabled")

		# clear input area
		self.breakpointsInput.delete("1.0", tk.END)

	def incMemIndex(self):

		# check if memory locations will be valid
		# the last index in memory that will have to be shown
		addrEnd: int = self.memoryIndex + 2 * Ui.memRowWidth * Ui.memRows - 1
		if addrEnd > Machine.maxAddress:
			logger.info("trying to go past maximum memory address (" + str(addrEnd) + ")")
			return
		
		self.memoryIndex += Ui.memRowWidth * Ui.memRows

	def decMemIndex(self):

		# check if memory locations will be valid
		# the first index in memory that will have to be shown
		addrStart: int = self.memoryIndex - Ui.memRowWidth * Ui.memRows
		if addrStart < Machine.minAddress:
			logger.info("trying to go past minimum memory address (" + str(addrStart) + ")")
			return
		
		self.memoryIndex -= Ui.memRowWidth * Ui.memRows

	def updateRegisters(self, m: Machine):
		self.registersText.delete("1.0", tk.END)
		self.registersText.insert(tk.END, m.registers2str())
		self.registersText.tag_add("center", "1.0", "end")
		self.registersText.update()

	def updateInstructions(self, m: Machine):
		self.instructionsText.delete("1.0", tk.END)
		self.instructionsText.insert(tk.END, m.getInstructionsString())
		self.instructionsText.tag_add("center", "1.0", "end")
		self.instructionsText.update()

	def updateMemory(self, m: Machine):
		self.memoryText.delete("2.0", tk.END)
		self.memoryText.insert(tk.END, "\n")
		self.memoryText.insert(tk.END, m.mem2str(self.memoryIndex, Ui.memRows))
		self.memoryText.tag_add("center", "1.0", "end")
		self.memoryText.update()

	def updateAll(self, m: Machine):
		self.window.update_idletasks()
		self.updateRegisters(m)
		self.updateInstructions(m)
		self.updateMemory(m)
