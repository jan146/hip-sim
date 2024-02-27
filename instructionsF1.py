from opc import Opcode
from typing import Callable, Any

def sicxeFix(self):
	self.setA(int(self.getF()))

def sicxeFloat(self):
	self.setF(float(self.getA()))

# not implemented
def sicxeHio(self):
	pass

# not implemented
def sicxeNorm(self):
	pass

# not implemented
def sicxeSio(self):
	pass

# not implemented
def sicxeTio(self):
	pass

opcode2instructionF1: dict[Opcode, Callable[[Any], None]] = {

	Opcode.FIX:		sicxeFix,
	Opcode.FLOAT:	sicxeFloat,
	Opcode.HIO:		sicxeHio,
	Opcode.NORM:	sicxeNorm,
	Opcode.SIO:		sicxeSio,
	Opcode.TIO:		sicxeTio,

}