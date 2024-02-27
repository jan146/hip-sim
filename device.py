import sys
from typing import BinaryIO
from random import random
from time import time

import logging
logger = logging.getLogger(__name__)

class Device:
	def test(self) -> bool:
		return True
	def read(self) -> bytes:
		return b'\x00'
	def write(self, val: bytes):
		pass
	def isInitialized(self) -> bool:	# default: device is initialized
		return True

# read randomized byte(s) from device
class Stdrng(BinaryIO):
	def read(self, n: int) -> bytes:
		return b"".join([int.to_bytes(int(random() * 256), length=1, byteorder="big", signed=False) for i in range(n)])
	def write(self, *args, **kvargs):
		pass

# write 0x01 to start timer and 0x02 to stop it
# read 24-bit time in milliseconds, starting from MSB to LSB
class Stdtimer(BinaryIO):

	timer: float = 0						# time counter in ms
	timerBytes: list[bytes] = [b"\x00"] * 3	# same but in bytes format

	def write(self, n: bytes):
		if n == b"\x01":				# start timer
			self.timer = time()
		elif n == b"\x02":				# stop timer
			self.timer = (time() - self.timer) * 1000.0
			self.timer %= 0x1000000
			self.timerBytes = [bytes([x]) for x in int.to_bytes(int(self.timer), length=3, byteorder="big", signed=False)]
	def read(self, n: int) -> bytes:
		if len(self.timerBytes) > 0:
			return self.timerBytes.pop(0)
		else:
			return b"\x00"

# used for stdin, stdrng
class InputDevice(Device):
	file: BinaryIO
	def __init__(self, fileName: str):
		if fileName == "stdin":
			self.file = sys.stdin.buffer
		elif fileName == "stdrng":
			self.file = Stdrng()
		else:
			self.file = open(fileName, "rb")
	def read(self) -> bytes:
		return self.readn(1)
	def readn(self, num: int) -> bytes:
		return self.file.read(num)

# used for stdout, stderr
class OutputDevice(Device):
	file: BinaryIO
	def __init__(self, fileName: str):
		if fileName == "stdout":
			self.file = sys.stdout.buffer
		elif fileName == "stderr":
			self.file = sys.stderr.buffer
		else:
			self.file = open(fileName, "wb")	# open file and clear content
			self.file = open(fileName, "ab")	# open for appending
	def write(self, val: bytes):
		self.file.write(val)
	def flush(self):
		self.file.flush()

# used for stdtimer and XX.dev files
class FileDevice(Device):
	file: BinaryIO
	initialized: bool = False
	def __init__(self, fileName: str):
		self.initialized = False
		if fileName == "stdtimer":
			self.file = Stdtimer()
			self.initialized = True
		else:
			try:
				self.file = open(fileName, "r+b")		# open file for R&W without truncating
				self.initialized = True
			except FileNotFoundError:
				logger.error("file not found (" + fileName + ")")
	def read(self) -> bytes:
		return self.readn(1)
	def readn(self, num: int) -> bytes:
		return self.file.read(num)
	def write(self, val: bytes):
		self.file.write(val)
	def flush(self):
		self.file.flush()
	def isInitialized(self) -> bool:
		return self.initialized
		
