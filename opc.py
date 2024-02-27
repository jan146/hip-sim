from enum import Enum
class Opcode(Enum):
	ADD = 0x18
	ADDF = 0x58
	ADDR = 0x90
	AND = 0x40
	CLEAR = 0xB4
	COMP = 0x28
	COMPF = 0x88
	COMPR = 0xA0
	DIV = 0x24
	DIVF = 0x64
	DIVR = 0x9C
	FIX = 0xC4
	FLOAT = 0xC0
	HIO = 0xF4
	J = 0x3C
	JEQ = 0x30
	JGT = 0x34
	JLT = 0x38
	JSUB = 0x48
	LDA = 0x00
	LDB = 0x68
	LDCH = 0x50
	LDF = 0x70
	LDL = 0x08
	LDS = 0x6C
	LDT = 0x74
	LDX = 0x04
	LPS = 0xD0
	MUL = 0x20
	MULF = 0x60
	MULR = 0x98
	NORM = 0xC8
	OR = 0x44
	RD = 0xD8
	RMO = 0xAC
	RSUB = 0x4C
	SHIFTL = 0xA4
	SHIFTR = 0xA8
	SIO = 0xF0
	SSK = 0xEC
	STA = 0x0C
	STB = 0x78
	STCH = 0x54
	STF = 0x80
	STI = 0xD4
	STL = 0x14
	STS = 0x7C
	STSW = 0xE8
	STT = 0x84
	STX = 0x10
	SUB = 0x1C
	SUBF = 0x5C
	SUBR = 0x94
	SVC = 0xB0
	TD = 0xE0
	TIO = 0xF8
	TIX = 0x2C
	TIXR = 0xB8
	WD = 0xDC

	def __str__(self) -> str:
		return self.name

setOpcodesInt:	set[int]	= set([x.value for x in Opcode])
setOpcodesF1:	set[Opcode]	= {Opcode.FIX, Opcode.FLOAT, Opcode.HIO, Opcode.NORM, Opcode.SIO, Opcode.TIO}
setOpcodesF2:	set[Opcode]	= {Opcode.ADDR, Opcode.CLEAR, Opcode.COMPR, Opcode.DIVR, Opcode.MULR, Opcode.RMO, Opcode.SHIFTL, Opcode.SHIFTR, Opcode.SUBR, Opcode.SVC, Opcode.TIXR}
setOpcodesSIC:	set[Opcode]	= {Opcode.ADD, Opcode.AND, Opcode.COMP, Opcode.DIV, Opcode.J, Opcode.JEQ, Opcode.JGT, Opcode.JLT, Opcode.JSUB, Opcode.LDA, Opcode.LDCH, Opcode.LDL, Opcode.LDS, Opcode.LDT, Opcode.LDX, Opcode.MUL, Opcode.OR, Opcode.RD, Opcode.RSUB, Opcode.STA, Opcode.STCH, Opcode.STL, Opcode.STSW, Opcode.STX, Opcode.SUB, Opcode.TD, Opcode.TIX, Opcode.WD}
setOpcodesF3F4:	set[Opcode]	= {Opcode.ADDF, Opcode.COMPF, Opcode.DIVF, Opcode.LDB, Opcode.LDF, Opcode.LPS, Opcode.MULF, Opcode.SSK, Opcode.STB, Opcode.STF, Opcode.STI, Opcode.STS, Opcode.STT, Opcode.SUBF}