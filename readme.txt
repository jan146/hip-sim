Sic/XE Simulator
Requires python 3.10 (or later)
Requires also tkinter (gui) or pynput (tui) libraries

Usage:
	- gui (recommended)
		- python run.py [path to obj file (optional)]
		- slow due to gui library not supporting running in non-main thread
	- tui
		- python run.py [path to obj file] tui
	- no output (just run simulation)
		- python run.py [path to obj file] none

Features:
	- essential features
		- registers
		- memory
		- devices (stdin, stdout, stderr)
		- all addressing modes
		- all insturction formats
		- integer arithmetic and bitwise operations
		- jump instructions
		- load and store instructions
		- automatic program execution (start, stop and step)
	- additional features
		- floating point arithmetic
		- additional devices
			- stdrng (device 3)
				- read single randomized byte from device
			- stdtimer (device 4)
				- start timer by writing 0x01 to the device
				- stop timer by writing 0x02 to the device
				- read timer value byte by byte (from MSB to LSB)
		- code disassembly
			- view instruction format, addressing mode and operand
		- memory overview
		- breakpoints
		- gui (and tui*)
			- monitor the simulation

