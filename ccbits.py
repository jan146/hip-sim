# enum for CC bits
from enum import Enum
class CCBits(Enum):
	GT = 0x80
	EQ = 0x00
	LT = 0x40
