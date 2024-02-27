from collections import defaultdict, deque
from typing import Callable

from ccbits import CCBits
from device import Device, InputDevice, OutputDevice, FileDevice
from opc import *
from nixpbebits import Nixbpe
from misc import bytes2int, bytes2float, float2bytes
import instructionsSICF3F4 as isicf3f4
import instructionsF1 as if1
import instructionsF2 as if2

import logging
logger = logging.getLogger(__name__)

class Machine():

	# type alias
	Reg = int
	RegF = float
	Mem = bytes

	@staticmethod
	def reg2str(val: int) -> str:
		return "{:06x}".format(val)

	# constants
	regMaxVal: 	Reg = 0xFFFFFF
	regMinVal: 	Reg = 0x000000
	maxAddress:	int = 0xFFFFF
	minAddress:	int = 0x00000

	def __init__(self):
		# initialize devices & standard streams
		self.devices: list[Device|None] = [None] * 256
		self.devices[0] = InputDevice("stdin")
		self.devices[1] = OutputDevice("stdout")
		self.devices[2] = OutputDevice("stderr")
		self.devices[3] = InputDevice("stdrng")
		self.devices[4] = FileDevice("stdtimer")

		# initialize registers
		# A, X, L, B, S, T, F, _, PC, SW <-> 0..9
		# list of 10 registers, initialized to zeros
		self.registers: list[Machine.Reg] = [0] * 10
		self.regF: Machine.RegF = 0.0

		# initialize memory
		# memory: memory address (int) -> content at memory address (bytes (1))
		# defaultdict: we don't want to initialize the entire memory on startup
		# -> make default value at any memory location a byte of 0s
		self.mem: defaultdict[int, Machine.Mem] = defaultdict(lambda: b'\x00')

		# initialize instructions history string
		self.instructionsStr = deque([])
		self.instructionsStrSize = 10

		# machine is running until infinite loop
		self.isRunning = True

		# set maximum clock frequency
		self.clockPeriod = 0

	# loader sets these properties
	# name of program
	progName: str
	# starting address of program
	codeAddress: int
	# object program length
	progLength: int
	# address of first executable instruction
	progStart: int
	# check if the machine is currently executing instructions
	isRunning: bool
	# machine's clock period (minimum time per instruction)
	clockPeriod: float

	# list of instructions in string format (for displaying only)
	instructionsStr: deque[str]
	# size of array above
	instructionsStrSize: int

	def getProgName(self) -> str:
		return self.progName
	def getCodeAddress(self) -> int:
		return self.codeAddress
	def getProgLength(self) -> int:
		return self.progLength
	def getProgStart(self) -> int:
		return self.progStart
	def getIsRunning(self) -> bool:
		return self.isRunning
	def getClockPeriod(self) -> float:
		return self.clockPeriod
	
	def setProgName(self, progName: str):
		self.progName = progName
	def setCodeAddress(self, codeAddress: int):
		self.codeAddress = codeAddress
	def setProgLength(self, progLength: int):
		self.progLength = progLength
	def setProgStart(self, progStart: int):
		self.progStart = progStart
	def setIsRunning(self, isRunning: bool):
		self.isRunning = isRunning
	def setClockPeriod(self, clockPeriod: float):
		self.clockPeriod = clockPeriod

	# getters
	def getA(self) -> Reg:
		return self.registers[0]
	def getX(self) -> Reg:
		return self.registers[1]
	def getL(self) -> Reg:
		return self.registers[2]
	def getB(self) -> Reg:
		return self.registers[3]
	def getS(self) -> Reg:
		return self.registers[4]
	def getT(self) -> Reg:
		return self.registers[5]
	def getF(self) -> RegF:
		return self.regF
	def getPC(self) -> Reg:
		return self.registers[8]
	def getSW(self) -> Reg:
		return self.registers[9]

	# setters
	def setA(self, val: Reg):
		self.registers[0] = val % (Machine.regMaxVal + 1)
	def setX(self, val: Reg):
		self.registers[1] = val % (Machine.regMaxVal + 1)
	def setL(self, val: Reg):
		self.registers[2] = val % (Machine.regMaxVal + 1)
	def setB(self, val: Reg):
		self.registers[3] = val % (Machine.regMaxVal + 1)
	def setS(self, val: Reg):
		self.registers[4] = val % (Machine.regMaxVal + 1)
	def setT(self, val: Reg):
		self.registers[5] = val % (Machine.regMaxVal + 1)
	def setF(self, val: RegF):
		self.regF = val
	def setPC(self, val: Reg):
		self.registers[8] = val % (Machine.regMaxVal + 1)
	def setSW(self, val: Reg):
		self.registers[9] = val % (Machine.regMaxVal + 1)

	# CC bits (needs CCBits class)
	def getCC(self) -> CCBits:
		return CCBits(self.getSW())
	def setCC(self, cc: CCBits):
		self.setSW(cc.value)

	# set and get via index	(use setF and getF for reg. F)
	def getReg(self, reg: int) -> Reg:
		return self.registers[reg]
	def setReg(self, reg: int, val: Reg):
		if self.regMinVal <= val <= self.regMaxVal:
			self.registers[reg] = val
		else:
			logger.error("value " + str(val) + " is not valid for register with index " + str(reg))

	def getByte(self, addr: int) -> Mem:
		if self.minAddress <= addr <= self.maxAddress:
			return self.mem[addr]
		else:
			logger.error("invalid address (" + str(addr) + ")")
			# default: return byte with zeros
			return self.Mem(1)
	def setByte(self, addr: int, val: Mem):
		if len(val) == 1:
			if self.minAddress <= addr <= self.maxAddress:
				self.mem[addr] = val
			else:
				logger.error("invalid address (" + str(addr) + ")")
		else:
			logger.error("1 byte required, not " + str(len(val)) + " bytes")

	def getWord(self, addr: int) -> Mem:

		if not (self.minAddress <= addr and (addr+2) <= self.maxAddress):
			logger.error("invalid address (" + str(addr) + ")")
			return self.Mem(3)

		return (self.mem[addr] + self.mem[addr+1] + self.mem[addr+2])

	def setWord(self, addr: int, val: Mem):

		if not (self.minAddress <= addr and (addr+2) <= self.maxAddress):
			logger.error("invalid address (" + str(addr) + ")")
			return

		if len(val) != 3:
			logger.error("3 bytes required, got (" + str(len(val)) + ")")
			return

		for i in range(3):
			self.mem[addr+i] = val[i:i+1]

	def getFloat(self, addr: int) -> float:

		if not (self.minAddress <= addr and (addr+5) <= self.maxAddress):
			logger.error("invalid address (" + str(addr) + ")")
			return 0.0

		byteList: list[bytes] = [self.getByte(addr+i) for i in range(6)]

		return bytes2float(byteList)

	def setFloat(self, addr: int, val: float):

		if not (self.minAddress <= addr and (addr+5) <= self.maxAddress):
			logger.error("invalid address (" + str(addr) + ")")
			return

		bytesFloat: list[bytes] = float2bytes(val)

		for i in range(6):
			self.setByte(addr+i, bytesFloat[i])

	"""

	0 |	1	 ...  11 | 12			     ...				 47
	s |		  e		 |				      f
	0 |	0000000 0000 | 0000 00000000 00000000 00000000 00000000

	s = 0, e = 1026, f = 1.625
	0 |	1	 ...  11 | 12			     ...				 47
	s |		  e		 |				      f
	0 |	1000000 0010 | 1010 00000000 00000000 00000000 00000000
	val = s * f * (2 ^ (e - 1024)) = 6.5

		m = Machine()
		m.mem[0] = b'\x40'
		m.mem[1] = b'\x2a'
		m.mem[2] = b'\x00'
		m.mem[3] = b'\x00'
		m.mem[4] = b'\x00'
		m.mem[5] = b'\x00'
		m.getFloat(0)

		m = Machine()
		m.setFloat(0, 6.5)
		m.getFloat(0)
		
		import math
		m = Machine()
		m.setFloat(0, -math.pi)
		m.getFloat(0)

	"""

	def getDevice(self, num: int) -> Device|None:

		if not (0 <= num <= 256):
			logger.error("invalid device number (" + str(num) + ")")
			return None
		return self.devices[num]

	def setDevice(self, num: int, device: Device):
		if not (0 <= num <= 256):
			logger.error("invalid device number (" + str(num) + ")")
		else:
			self.devices[num] = device

	def addInstructionString(self, instruction: str):
		if len(self.instructionsStr) >= self.instructionsStrSize:
			self.instructionsStr.popleft()
			self.instructionsStr.append(instruction.ljust(40))
		else:
			self.instructionsStr.append(instruction.ljust(40))

	def getInstructionsString(self) -> str:
		return ("\n".join(self.instructionsStr) + "\n").upper()

	def fetch(self) -> Mem:
		valPC: int = self.getPC()					# get value of PC
		byte: Machine.Mem = self.getByte(valPC)		# get the byte that PC is pointing to
		self.setPC(valPC + 1)						# increment PC
		return byte

	def fetchUint8(self) -> int:
		fetchedByte: Machine.Mem = self.fetch()
		return int.from_bytes(bytes=fetchedByte, byteorder="big", signed=False)

	def execute(self):
		int1: int = self.fetchUint8()				# get first byte
		logger.debug("byte1: " + hex(int1))

		# check if it is a valid op. code (ignore lowest 2 bits)
		if not ((int1 & 0xFC) in setOpcodesInt):
			logger.error("invalid opcode (" + str(int1) + ")")
			return

		# F1
		if Opcode((int1 & 0xFC)) in setOpcodesF1:
			logger.info("instruction format: F1")
			self.execF1(Opcode(int1))			# execute F1
		
		# F2
		elif Opcode((int1 & 0xFC)) in setOpcodesF2:
			logger.info("instruction format: F2")
			int2: int = self.fetchUint8()			# get second byte
			logger.debug("byte2: " + hex(int2))
			r1: int = int2 >> 4						# extract r1
			r2: int = int2 % 0x10					# extract r2
			self.execF2(Opcode(int1), r1, r2)	# execute F2

		# SIC, F3 or F4
		else:
			# SIC
			if int1 % 4 == 0:

				logger.info("instruction format: SIC")
				# initialize nixbpe
				nixbpe = Nixbpe()
				# nixbpe.setN(0)	# default is 0
				# nixbpe.setI(0)	# default is 0

				int2: int = self.fetchUint8()		# get second byte
				logger.debug("byte2: " + hex(int2))
				if int2 & 0x80:						# check MSb
					nixbpe.setX(1)					# set X accordingly

				int3: int = self.fetchUint8()
				logger.debug("byte3: " + hex(int3))
				address: int = ((int2 & 0x7F) << 8) + int3
				addressSigned: int = (-0x4000 if address & 0x4000 else 0) + (address & 0x3FF)

				self.execSICF3F4(Opcode(int1), nixbpe, address, addressSigned)
			
			# F3 or F4
			else:
				
				# initialize nixbpe
				nixbpe = Nixbpe()

				# read bits n and i from first byte
				if int1 & 0x01:
					nixbpe.setI(1)
				if int1 & 0x02:
					nixbpe.setN(1)

				# read bits x, b, p and e from second byte
				int2: int = self.fetchUint8()
				logger.debug("byte2: " + hex(int2))
				if int2 & 0x80:
					nixbpe.setX(1)
				if int2 & 0x40:
					nixbpe.setB(1)
				if int2 & 0x20:
					nixbpe.setP(1)
				if int2 & 0x10:
					nixbpe.setE(1)

				int3: int = self.fetchUint8()
				logger.debug("byte3: " + hex(int3))
				
				# F4
				if nixbpe.getE():
					
					logger.info("instruction format: F4")
					int4: int = self.fetchUint8()
					logger.debug("byte4: " + hex(int4))
					
					address: int = ((int2 & 0x0F) << 16) + (int3 << 8) + int4
					addressSigned: int = (-0x80000 if address & 0x80000 else 0) + (address & 0x7FFFF)

					self.execSICF3F4(Opcode(int1 & 0xFC), nixbpe, address, addressSigned)
				
				# F3
				else:

					logger.info("instruction format: F3")
					offset: int = ((int2 & 0x0F) << 8) + int3
					offsetSigned: int = (-0x800 if offset & 0x800 else 0) + (offset & 0x7FF)
					self.execSICF3F4(Opcode(int1 & 0xFC), nixbpe, offset, offsetSigned)

	def execF1(self, opcode: Opcode):

		logger.debug("opcode: " + str(opcode))

		# get instruction from opcode
		instruction: Callable[[Machine], None]
		try:
			instruction = if1.opcode2instructionF1[opcode]
		except KeyError:
			logger.error("invalid op. code (" + str(opcode) + ")")
			return
		logger.info("instruction: " + str(instruction))
		self.addInstructionString("{:3s}: {:6s}".format("F1", opcode))

		# execute the instruction
		instruction(self)

	def execF2(self, opcode: Opcode, r1: int, r2: int):

		logger.debug("opcode: " + str(opcode) + ", r1: " + str(r1) + ", r2: " + str(r2))
		
		# get instruction from opcode
		instruction: Callable[[Machine, int, int], None]
		try:
			instruction = if2.opcode2instructionF2[opcode]
		except KeyError:
			logger.error("invalid op. code (" + str(opcode) + ")")
			return
		logger.info("instruction: " + str(instruction))
		self.addInstructionString("{:3s}: {:6s} r1={:1d} r2={:1d}".format("F2", opcode, r1, r2))

		# execute the instruction
		instruction(self, r1, r2)

	def baseRelative(self, uOperand: int, sOperand: int):
		return (self.getB() + uOperand)

	def PCRelative(self, uOperand: int, sOperand: int):
		return (self.getPC() + sOperand)

	def directAddressing(self, uOperand: int, sOperand: int):
		return uOperand

	# returns function that will calculate the TA
	def getTA(self, nixbpe: Nixbpe) -> Callable[[int, int], int]:
		match nixbpe.getTuple():
			case (0, 0, _, _, _, _):			# legacy SIC
				logger.info("using direct addressing (legacy SIC)")
				return self.directAddressing
			case (_, _, _, 1, 0, _):
				logger.info("using base-relative addressing")
				return self.baseRelative
			case (_, _, _, 0, 1, _):
				logger.info("using PC-relative addressing")
				return self.PCRelative
			case (_, _, _, 0, 0, _):
				logger.info("using direct addressing")
				return self.directAddressing
			case _:
				logger.error("invalid combination of b and p bits (b=" + str(nixbpe.getB()) + ", p=" + str(nixbpe.getP()) + ")")
				return (lambda x, y: 0)

	# 2 steps of dereferencing
	def indirectAddressing(self, targetAddress: int) -> bytes:
		singleDereference: int = bytes2int(self.getWord(targetAddress))
		if singleDereference > Machine.maxAddress:
			logger.error("value after single dereference is over 20 bits (" + hex(singleDereference) + ")")
			return bytes(3)
		return self.getWord(singleDereference)

	# 0 steps of dereferencing
	def immediateAddressing(self, targetAddress: int) -> bytes:
		try:
			return int.to_bytes(targetAddress, byteorder="big", length=3, signed=False)
		except OverflowError:
			logger.error("targetAddress too big (" + hex(targetAddress) + ")")
			return bytes(3)

	# 1 step of dereferencing
	def simpleAddressing(self, targetAddress: int) -> bytes:
		return self.getWord(targetAddress)

	# returns the function that will use the TA
	def getFP(self, opcode: Opcode, nixbpe: Nixbpe) -> Callable[[int], bytes]:
			
		# store/jump instructions
		if opcode in isicf3f4.opcodeStoreJump:
			logger.info("store/jump instructions -> implicit level of indirection")
			match nixbpe.getTuple():
				case (1, 0, _, _, _, _):
					logger.info("using simple addressing")
					return self.simpleAddressing
				case _:
					logger.info("using immediate addressing")
					return self.immediateAddressing

		# other instructions
		match nixbpe.getTuple():
			case (1, 0, _, _, _, _):
				logger.info("using indirect addressing")
				return self.indirectAddressing
			case (0, 1, _, _, _, _):
				logger.info("using immediate addressing")
				return self.immediateAddressing
			case _:
				logger.info("using simple addressing")
				return self.simpleAddressing

	def execSICF3F4(self, opcode: Opcode, nixbpe: Nixbpe, uOperand: int, sOperand: int):

		# check if indexing with # or @ is used
		match nixbpe.getTuple():
			case (n, i, x, _, _, _) if x and n != i:
				logger.error("indexing cannot be used with immediate or indirect addressing modes")
				return
			case _:
				pass
		
		logger.debug("uOperand (" + hex(uOperand) + ")")
		logger.debug("sOperand (" + hex(sOperand) + ")")

		# get targetAddress
		targetAddress: int = (self.getTA(nixbpe))(uOperand, sOperand)
		# indexed addressing
		if nixbpe.getX():
			targetAddress += self.getX()
		# target address must be 20 bits since memory is addressed with 20 bits
		targetAddress %= 0x100000
		logger.debug("targetAddress (" + hex(targetAddress) + ")")

		# the parameter that will actually be used in instructions
		finalizedParameter: bytes = (self.getFP(opcode, nixbpe))(targetAddress)
		logger.debug("finalizedParameter: " + str(finalizedParameter))

		# get instruction from opcode
		instruction: Callable[[Machine, Nixbpe, bytes], None]
		try:
			instruction = isicf3f4.opcode2instructionSICF3F4[opcode]
		except KeyError:
			logger.error("invalid op. code (" + str(opcode) + ")")
			return
		logger.info("instruction: " + str(instruction))

		# create disassebmly-like instruction string
		self.addInstructionString(self.createInstructionString(nixbpe, opcode, uOperand))

		# execute the instruction
		instruction(self, nixbpe, finalizedParameter)

	def createInstructionString(self, nixbpe: Nixbpe, opcode: Opcode, operand: int):
		
		format: str = ""
		match nixbpe.getTuple():
			case (0, 0, _, _, _, _):
				format = "SIC"
			case (_, _, _, _, _, 1):
				format = "F4"
			case _:
				format = "F3"

		bpAddressing: str = ""
		match nixbpe.getB(), nixbpe.getP():
			case (1, 0):
				bpAddressing = "B +"
			case (0, 1):
				bpAddressing = "PC +"
			case (0, 0):
				bpAddressing = "Abs:"
		
		niAddressing: str = ""
		match nixbpe.getN(), nixbpe.getI():
			case (1, 0):
				niAddressing = "@Indirect"
			case (0, 1):
				niAddressing = "#Immediate"
			case (1, 1):
				niAddressing = " Simple"
			case (0, 0):
				niAddressing = " SIC"

		xOffset: str = ""
		if nixbpe.getX():
			xOffset = ",X"

		return "{:3s}: {:6s} {:s} {:06x}{:s}, {:s}".format(format, opcode, bpAddressing, operand, xOffset, niAddressing)

	def registers2str(self) -> str:
		lineWidth: int = 30

		axl: str = ""
		axl += "A:  "
		axl += Machine.reg2str(self.getA())
		axl += " "
		axl += "X: "
		axl += Machine.reg2str(self.getX())
		axl += " "
		axl += "L: "
		axl += Machine.reg2str(self.getL())
		axl = axl.ljust(lineWidth)
		axl += "\n"

		stb: str = ""
		stb += "S:  "
		stb += Machine.reg2str(self.getS())
		stb += " "
		stb += "T: "
		stb += Machine.reg2str(self.getT())
		stb += " "
		stb += "B: "
		stb += Machine.reg2str(self.getB())
		stb = stb.ljust(lineWidth)
		stb += "\n"

		swf: str = ""
		swf += "SW: "
		swf += Machine.reg2str(self.getSW())
		swf += " "
		swf += "F: "
		swf += "".join(["{:02x}".format(byte[0]) for byte in float2bytes(self.getF())])
		swf = swf.ljust(lineWidth)
		swf += "\n"

		pcf: str = ""
		pcf += "PC: "
		pcf += Machine.reg2str(self.getPC())
		pcf += " "
		pcf += "F: "
		pcf += "{:+12.3f}".format(self.getF())
		pcf = pcf.ljust(lineWidth)
		pcf += "\n"

		return (axl + stb + swf + pcf).upper()

	def mem2str(self, addrStart: int, rows: int) -> str:

		# check if address is valid
		rowWidth: int = 16
		addrEnd: int = addrStart + rows * rowWidth - 1
		if not (Machine.minAddress <= addrStart <= Machine.maxAddress) or not (Machine.minAddress <= addrEnd <= Machine.maxAddress):
			logger.error("invalid memory span: addrStart=" + str(addrStart) + ", addrEnd=" + str(addrEnd))
			return ""
		if rows < 1:
			logger.error("number of rows is not a positive integer (" + str(rows) + ")")
			return ""

		s: str = ""
		for i in range(rows):
			addr = addrStart + i * rowWidth
			s += "{:05x} ".format(addr)
			s += " ".join([self.getByte(addr + i).hex() for i in range(rowWidth)])
			s += "\n"

		return s.upper()

	def __str__(self) -> str:
		s: str = ""

		s += self.registers2str() + "\n"
		s += self.getInstructionsString() + "\n"
		s += self.mem2str(0x0, 10)

		return s

	"""
	F1:
m = Machine()
m.setByte(0, b'\xc4')
m.execute()

	F2:
m = Machine()
m.setByte(0, b'\x90')
m.setByte(1, b'\x61')
m.execute()

	SIC:
m = Machine()
m.setByte(0, b'\x40')
m.setByte(1, b'\x91')
m.setByte(2, b'\x1f')
m.execute()
4383

	F3:
m = Machine()
m.setByte(0, b'\x90')
m.setByte(1, b'\x61')
m.execute()

	"""

"""

m = Machine()

m.setWord(0x100, b"\x01\x02\x03")
print("mem[0x100]: " + str(m.getWord(0x100)))

opcode = Opcode.LDA
x = 0
operand = 0x100

instruction = opcode.value << 1
instruction += x
instruction = instruction << 15
instruction += operand

print("instruction: " + hex(instruction) + " " + str(Machine.int2mem(instruction, 3)))
m.setWord(0, Machine.int2mem(instruction, 3))
print("mem[0]: " + str(m.getWord(0)))

m.execute()

print("A is now: " + hex(m.getA()) + " " + bin(m.getA()))
	
#########################################################################################################

m.setWord(0x200, b"\x00\xa0\x1b")
print("mem[0x200]: " + str(m.getWord(0x200)))

opcode = Opcode.OR
x = 0
operand = 0x200

instruction = opcode.value << 1
instruction += x
instruction = instruction << 15
instruction += operand

print("instruction: " + hex(instruction) + " " + str(Machine.int2mem(instruction, 3)))
m.setWord(3, Machine.int2mem(instruction, 3))
print("mem[3]: " + str(m.getWord(3)))

m.execute()

print("A is now: " + hex(m.getA()) + " " + bin(m.getA()))

print(m)

"""
