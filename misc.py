from math import floor, log2

import logging
logger = logging.getLogger(__name__)

# conversion/casting methods
def bytes2int(val: bytes) -> int:
	return int.from_bytes(bytes=val, byteorder="big", signed=False)

def int2bytes(val: int, length: int) -> bytes:
	try:
		return int.to_bytes(val, length=length, byteorder="big", signed=False)
	except OverflowError:
		mask: int = 0x1000000 if length == 3 else (1 << (length * 8))
		val %= mask
		return int.to_bytes(val, length=length, byteorder="big", signed=False)

# bytes in ieee754 float48 to python float type
def bytes2float(val: list[bytes]) -> float:

	# check for zero
	for byte in val:
		if byte != b"\x00":
			break
	else:
		return 0

	s = val[0][0] & 0x80					# get 1st bit
	sign = -1 if s else 1					# check 1st bit
	
	e = val[0] + val[1]						# get first 2 bytes
	emask = 0b0111111111110000				# remove s and f
	e = int.from_bytes(e, "big") & emask	# extract exponent from first 2 bytes
	exponent = e >> 4						# skip lowest 4 bits (f)
	
	f = b''
	for i in range(1, 6):
		f = f + val[i]						# get last 5 bytes
	fmask = 0x0FFFFFFFFF					# clear top 4 bits (e)
	f = int.from_bytes(f, "big") & fmask
	fraction = 1.0 + f / float(1 << 36)
	return (sign * fraction * float(2 ** (exponent - 1024)))

# python float to bytes representation of ieee754 float48
def float2bytes(val: float) -> list[bytes]:

	if val == 0.0:
		return ([b"\x00"] * 6)
	
	sign = 1 if val < 0 else 0
	val = -val if sign else val
	
	exponent = floor(log2(val)) + 1024							# exponent + 1024
	fraction = val / float(2 ** (exponent - 1024))				# divide by real exponent
	fraction = fraction - 1.0									# subtract implied bit
	fraction = fraction * float(1 << 36)						# "shift" 36 bits
	
	# write to local list before accessing mem
	byteList: list[bytes] = [bytes(1)] * 6
	e = exponent << 4											# last 4 bits are in fraction
	e = e.to_bytes(length=2, byteorder="big", signed=False)
	byteList[0] = e[0:1]										# set first 2 bytes to exponent
	byteList[1] = e[1:2]
	
	if sign:													# set first bit to 1 if sign is true
		s = e[0] | 0x80
		byteList[0] = s.to_bytes(length=1, byteorder="big", signed=False)
	
	# store (shifter) fraction to last 5 bytes
	f = int(fraction).to_bytes(length=5, byteorder="big", signed=False)
	for i in range(5):
		byteList[i+1] = int.to_bytes(byteList[i+1][0] | f[i], length=1, byteorder="big", signed=False)
	
	return byteList

# convert uint(length*8) to signed int
def uns2sgn(val: int, length: int) -> int:
	return int.from_bytes(bytes=int2bytes(val, length=length), byteorder="big", signed=True)
	
def freq2clockPeriod(freq: int, clockPeriodPrev) -> float:
	clockPeriod: float
	if freq > 0:
		return (1.0 / freq)
	elif freq == 0:
		return 0
	else:
		logger.warn("invalid clock frequency (" + str(freq) + ")")
		return clockPeriodPrev
