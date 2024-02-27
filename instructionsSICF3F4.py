from opc import Opcode
from ccbits import CCBits
from typing import Callable, Any
from device import FileDevice
from nixpbebits import Nixbpe
from misc import int2bytes, bytes2float, float2bytes, uns2sgn

import logging
logger = logging.getLogger(__name__)

def signed(parameter: bytes) -> int:
	return int.from_bytes(bytes=parameter, byteorder="big", signed=True)

def unsigned(parameter: bytes) -> int:
	return int.from_bytes(bytes=parameter, byteorder="big", signed=False)

########################################################################################

def sicAdd(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() + unsigned(parameter))

def sicAnd(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() & unsigned(parameter))

def sicComp(self, nixbpe: Nixbpe, parameter: bytes):
	diff: int = uns2sgn(self.getA(), 3) - signed(parameter)
	cc: CCBits = CCBits.GT if diff > 0 else (CCBits.LT if diff < 0 else CCBits.EQ)
	self.setCC(cc)

def sicDiv(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() // unsigned(parameter))

def sicJ(self, nixbpe: Nixbpe, parameter: bytes):
	self.setPC(unsigned(parameter))

def sicJeq(self, nixbpe: Nixbpe, parameter: bytes):
	newPC: int = unsigned(parameter) if self.getCC() == CCBits.EQ else self.getPC()
	self.setPC(newPC)

def sicJgt(self, nixbpe: Nixbpe, parameter: bytes):
	newPC: int = unsigned(parameter) if self.getCC() == CCBits.GT else self.getPC()
	self.setPC(newPC)

def sicJlt(self, nixbpe: Nixbpe, parameter: bytes):
	newPC: int = unsigned(parameter) if self.getCC() == CCBits.LT else self.getPC()
	self.setPC(newPC)

def sicJsub(self, nixbpe: Nixbpe, parameter: bytes):
	self.setL(self.getPC())
	self.setPC(unsigned(parameter))

def sicLda(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(unsigned(parameter))

def sicLdch(self, nixbpe: Nixbpe, parameter: bytes):
	valA: bytes = int.to_bytes(self.getA(), length=3, byteorder="big", signed=False)
	newVal: bytes = valA[:2]						# keep upper 2 bytes of A
	match nixbpe.getTuple():
		case (0, 1, _, _, _, _):					# immediate addressing -> append upper byte
			newVal += parameter[-1:]
		case _:										# simple/indirect addr. -> append lower byte
			newVal += parameter[:1]
	self.setA(unsigned(newVal))

def sicLdl(self, nixbpe: Nixbpe, parameter: bytes):
	self.setL(unsigned(parameter))

def sicLds(self, nixbpe: Nixbpe, parameter: bytes):
	self.setS(unsigned(parameter))

def sicLdt(self, nixbpe: Nixbpe, parameter: bytes):
	self.setT(unsigned(parameter))

def sicLdx(self, nixbpe: Nixbpe, parameter: bytes):
	self.setX(unsigned(parameter))

def sicMul(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() * unsigned(parameter))

def sicOr(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() | unsigned(parameter))

def sicRsub(self, nixbpe: Nixbpe, parameter: bytes):
	self.setPC(self.getL())

def sicSta(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getA(), 3))

def sicStch(self, nixbpe: Nixbpe, parameter: bytes):
	self.setByte(addr=unsigned(parameter), val=int2bytes(self.getA(), 3)[-1:])

def sicStl(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getL(), 3))

def sicStsw(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getSW(), 3))

def sicStx(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getX(), 3))

def sicSub(self, nixbpe: Nixbpe, parameter: bytes):
	self.setA(self.getA() - unsigned(parameter))

def sicTix(self, nixbpe: Nixbpe, parameter: bytes):
	self.setX(self.getX() + 1)
	diff: int = self.getX() - unsigned(parameter)
	cc: CCBits = CCBits.GT if diff > 0 else (CCBits.LT if diff < 0 else CCBits.EQ)
	self.setCC(cc)

def sicRd(self, nixbpe: Nixbpe, parameter: bytes):

	# check for immediate addressing
	match nixbpe.getTuple():
		case (0, 1, _, _, _, _):
			parameter = parameter[-1:]
		case _:
			parameter = parameter[:1]

	# check if device is available for reading
	deviceId: int = unsigned(parameter)
	if not (0 <= deviceId <= 256) or deviceId in (1, 2):
		logger.error("invalid device id (" + str(deviceId) + ")")
		return

	# create/get device
	device: FileDevice
	if self.getDevice(deviceId) is None:
		fileName: str = "{:02x}".format(deviceId).upper() + ".dev"
		device = FileDevice(fileName)
		self.setDevice(deviceId, device)
	else:
		device = self.getDevice(deviceId)
	
	if device.isInitialized():
		readByte: bytes = device.read()
		if len(readByte) < 1:		# on end: read zeros
			readByte = b"\x00"
		valA: int = self.getA()
		valA &= 0xFFFF00			# set A.low to the read byte
		valA += readByte[0]
		self.setA(valA)
	else:				# file is not accessible
		logger.error("device is not accessible (" + str(deviceId) + ")")

def sicTd(self, nixbpe: Nixbpe, parameter: bytes):

	# check for immediate addressing
	match nixbpe.getTuple():
		case (0, 1, _, _, _, _):
			parameter = parameter[-1:]
		case _:
			parameter = parameter[:1]

	# check if device id is valid
	deviceId: int = unsigned(parameter)
	if not (0 <= deviceId <= 256):
		logger.error("invalid device id (" + str(deviceId) + ")")
		return

	# create/get device
	device: FileDevice
	if self.getDevice(deviceId) is None:
		fileName: str = "{:02x}".format(deviceId).upper() + ".dev"
		device = FileDevice(fileName)
		self.setDevice(deviceId, device)
	else:
		device = self.getDevice(deviceId)

	if device.isInitialized():
		self.setCC(CCBits.LT)
	else:
		self.setCC(CCBits.EQ)

def sicWd(self, nixbpe: Nixbpe, parameter: bytes):

	# check for immediate addressing
	match nixbpe.getTuple():
		case (0, 1, _, _, _, _):
			parameter = parameter[-1:]
		case _:
			parameter = parameter[:1]

	# check if device is available for writing
	deviceId: int = unsigned(parameter)
	if not (0 <= deviceId <= 256) or deviceId == 0:
		logger.error("invalid device id (" + str(deviceId) + ")")
		return

	# create/get device
	device: FileDevice
	if self.getDevice(deviceId) is None:
		fileName: str = "{:02x}".format(deviceId).upper() + ".dev"
		device = FileDevice(fileName)
		self.setDevice(deviceId, device)
	else:
		device = self.getDevice(deviceId)

	if device.isInitialized():
		valA: int = self.getA()
		valA &= 0x0000FF
		device.write(int2bytes(valA, 1))
		device.flush()
	else:				# file is not accessible
		logger.error("device is not accessible (" + str(deviceId) + ")")

def sicxeAddf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	self.setF(self.getF() + parameterFloat)

def sicxeCompf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	cc: CCBits = CCBits.GT if self.getF() > parameterFloat else (CCBits.LT if self.getF() < parameterFloat else CCBits.EQ)
	self.setCC(cc)

def sicxeDivf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	self.setF(self.getF() / parameterFloat)

def sicxeLdb(self, nixbpe: Nixbpe, parameter: bytes):
	self.setB(unsigned(parameter))

def sicxeLdf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	self.setF(parameterFloat)

# not implemented
def sicxeLps(self, nixbpe: Nixbpe, parameter: bytes):
	pass

def sicxeMulf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	self.setF(self.getF() * parameterFloat)

# not implemented
def sicxeSsk(self, nixbpe: Nixbpe, parameter: bytes):
	pass

def sicxeStb(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getB(), 3))

def sicxeStf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList = float2bytes(self.getF())
	self.setWord(addr=(unsigned(parameter) + 0), val=b"".join(byteList[:3]))
	self.setWord(addr=(unsigned(parameter) + 3), val=b"".join(byteList[3:]))

# not implemented
def sicxeSti(self, nixbpe: Nixbpe, parameter: bytes):
	pass

def sicxeSts(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getS(), 3))

def sicxeStt(self, nixbpe: Nixbpe, parameter: bytes):
	self.setWord(addr=unsigned(parameter), val=int2bytes(self.getT(), 3))

def sicxeSubf(self, nixbpe: Nixbpe, parameter: bytes):
	byteList: list[bytes] = [bytes([x]) for x in parameter]
	parameterFloat: float = bytes2float(byteList)
	self.setF(self.getF() - parameterFloat)

opcode2instructionSICF3F4: dict[Opcode, Callable[[Any, Nixbpe, bytes], None]] = {
	
	# legacy SIC instructions
	Opcode.ADD:		sicAdd,
	Opcode.AND:		sicAnd,
	Opcode.COMP:	sicComp,
	Opcode.DIV:		sicDiv,
	Opcode.J:		sicJ,
	Opcode.JEQ:		sicJeq,
	Opcode.JGT:		sicJgt,
	Opcode.JLT:		sicJlt,
	Opcode.JSUB:	sicJsub,
	Opcode.LDA:		sicLda,
	Opcode.LDCH:	sicLdch,
	Opcode.LDL:		sicLdl,
	Opcode.LDS:		sicLds,
	Opcode.LDT:		sicLdt,
	Opcode.LDX:		sicLdx,
	Opcode.MUL:		sicMul,
	Opcode.OR:		sicOr,
	Opcode.RD:		sicRd,
	Opcode.RSUB:	sicRsub,
	Opcode.STA:		sicSta,
	Opcode.STCH:	sicStch,
	Opcode.STL:		sicStl,
	Opcode.STSW:	sicStsw,
	Opcode.STX:		sicStx,
	Opcode.SUB:		sicSub,
	Opcode.TD:		sicTd,
	Opcode.TIX:		sicTix,
	Opcode.WD:		sicWd,

	# SIC/XE specific instructions
	Opcode.ADDF:	sicxeAddf,
	Opcode.COMPF:	sicxeCompf,
	Opcode.DIVF:	sicxeDivf,
	Opcode.LDB:		sicxeLdb,
	Opcode.LDF:		sicxeLdf,
	Opcode.LPS:		sicxeLps,
	Opcode.MULF:	sicxeMulf,
	Opcode.SSK:		sicxeSsk,
	Opcode.STB:		sicxeStb,
	Opcode.STF:		sicxeStf,
	Opcode.STI:		sicxeSti,
	Opcode.STS:		sicxeSts,
	Opcode.STT:		sicxeStt,
	Opcode.SUBF:	sicxeSubf

}

# store/jump instructions need to replace simple addressing with immediate (like in sictools)
opcodeStoreJump: set[Opcode] = {
	Opcode.STA,
	Opcode.STB,
	Opcode.STCH,
	Opcode.STF,
	Opcode.STL,
	Opcode.STS,
	Opcode.STSW,
	Opcode.STT,
	Opcode.STX,
	Opcode.J,
	Opcode.JEQ,
	Opcode.JGT,
	Opcode.JLT,
	Opcode.JSUB
}
