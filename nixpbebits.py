class Nixbpe():

	# list holding the actual values
	bits: tuple[int, ...] = tuple([0] * 6)

	# use for pattern matching and such
	def getTuple(self) -> tuple[int, ...]:
		return self.bits

	# getters
	def getN(self) -> int:
		return self.bits[0]
	def getI(self) -> int:
		return self.bits[1]
	def getX(self) -> int:
		return self.bits[2]
	def getB(self) -> int:
		return self.bits[3]
	def getP(self) -> int:
		return self.bits[4]
	def getE(self) -> int:
		return self.bits[5]

	# setters
	def setN(self, val: int):
		self.bits = self.bits[:0] + (val,) + self.bits[1:]
	def setI(self, val: int):
		self.bits = self.bits[:1] + (val,) + self.bits[2:]
	def setX(self, val: int):
		self.bits = self.bits[:2] + (val,) + self.bits[3:]
	def setB(self, val: int):
		self.bits = self.bits[:3] + (val,) + self.bits[4:]
	def setP(self, val: int):
		self.bits = self.bits[:4] + (val,) + self.bits[5:]
	def setE(self, val: int):
		self.bits = self.bits[:5] + (val,) + self.bits[6:]
