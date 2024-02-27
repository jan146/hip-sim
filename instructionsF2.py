from opc import Opcode
from typing import Callable, Any
from ccbits import CCBits
from misc import uns2sgn

def sicxeAddr(self, r1: int, r2: int):
	self.setReg(r2, self.getReg(r2) + self.getReg(r1))

def sicxeClear(self, r1: int, r2: int):
	self.setReg(r1, 0)

def sicxeCompr(self, r1: int, r2: int):
	diff: int = uns2sgn(self.getReg(r1), 3) - uns2sgn(self.getReg(r2), 3)
	cc: CCBits = CCBits.GT if diff > 0 else (CCBits.LT if diff < 0 else CCBits.EQ)
	self.setCC(cc)

def sicxeDivr(self, r1: int, r2: int):
	self.setReg(r2, self.getReg(r2) // self.getReg(r1))

def sicxeMulr(self, r1: int, r2: int):
	self.setReg(r2, self.getReg(r2) * self.getReg(r1))

def sicxeRmo(self, r1: int, r2: int):
	self.setReg(r2, self.getReg(r1))

def sicxeShiftl(self, r1: int, n: int):
	self.setReg(r1, self.getReg(r1) << n)

def sicxeShiftr(self, r1: int, n: int):
	self.setReg(r1, self.getReg(r1) >> n)

def sicxeSubr(self, r1: int, r2: int):
	self.setReg(r2, self.getReg(r2) - self.getReg(r1))

# not implemented
def sicxeSvc(self, r1: int, r2: int):
	pass

def sicxeTixr(self, r1: int, r2: int):
	self.setX(self.getX() + 1)
	diff: int = self.getX() - self.getReg(r1)
	cc: CCBits = CCBits.GT if diff > 0 else (CCBits.LT if diff < 0 else CCBits.EQ)
	self.setCC(cc)

opcode2instructionF2: dict[Opcode, Callable[[Any, int, int], None]] = {

	Opcode.ADDR:	sicxeAddr,
	Opcode.CLEAR:	sicxeClear,
	Opcode.COMPR:	sicxeCompr,
	Opcode.DIVR:	sicxeDivr,
	Opcode.MULR:	sicxeMulr,
	Opcode.RMO:		sicxeRmo,
	Opcode.SHIFTL:	sicxeShiftl,
	Opcode.SHIFTR:	sicxeShiftr,
	Opcode.SUBR:	sicxeSubr,
	Opcode.SVC:		sicxeSvc,
	Opcode.TIXR:	sicxeTixr,

}