from machine import Machine

from typing import TextIO

import logging
logger = logging.getLogger(__name__)

def headerRecord(objFile: TextIO, m: Machine):

	logger.info("reading header record")

	# header record starts with 'H'
	objFile.read(1)
	
	# name of program
	m.setProgName(objFile.read(6))
	logger.debug("set program name: " + m.getProgName())

	# starting address of program
	m.setCodeAddress(int(objFile.read(6), 16))
	logger.debug("set code address: " + hex(m.getCodeAddress()))

	# object program length
	m.setProgLength(int(objFile.read(6), 16))
	logger.debug("set program length: " + hex(m.getProgLength()))

def textRecord(objFile: TextIO, m: Machine):
	
	logger.info("reading text record")

	startAddress: int = int(objFile.read(6), 16)
	byteCount: int = int(objFile.read(2), 16)

	address: int = startAddress
	for i in range(byteCount):
		
		intRead: int = int(objFile.read(2), 16)
		byteRead: bytes = int.to_bytes(intRead, length=1, byteorder="big", signed=False)

		m.setByte(addr=address, val=byteRead)
		logger.debug("mem[{:06x}]={:s}".format(address, byteRead.hex()))
		
		address += 1

def endRecord(objFile: TextIO, m: Machine):
	
	logger.info("reading end record")

	# address of first executable instruction
	m.setProgStart(int(objFile.read(6), 16))
	logger.debug("set program start: " + hex(m.getProgStart()))

def modificationRecord(objFile: TextIO, m: Machine):
	
	logger.info("reading modification record")

	startAddress: int = int(objFile.read(6), 16)
	length: int = int(objFile.read(2), 16)
	
	# sictools already fixes all the addresses while assembling

def readRecords(objFile: TextIO, m: Machine):

	firstChar: str
	while (firstChar := objFile.read(1)) != "":
		match firstChar:
			case 'T':
				textRecord(objFile, m)
			case 'E':
				endRecord(objFile, m)
			case 'M':
				modificationRecord(objFile, m)
			case '\n' | '\r':
				readRecords(objFile, m)
			case _:
				logger.error("invalid/missing record format")
				exit(1)

def loadObj(objFile: TextIO, m: Machine):
	headerRecord(objFile, m)
	readRecords(objFile, m)
