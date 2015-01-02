import re
import sys

def chooseNumFormat(num):
	if "." in num:
		return float(num)
	return int(num)

''' Types '''
class JType:
	def __init__(self, val):
		self.make(val)
	def make(self, val):
		self.v = val
	def __eq__(self, other):
		return other.v == self.v
	def __lt__(self, other):
		if isinstance(other, JType):
			return self.v < other.v
		return self.v < other
	def __gt__(self, other):
		if isinstance(other, JType):
			return self.v > other.v
		return self.v > other
	def __add__(self, other):
		if isinstance(other, JType):
			return self.v + other.v
		return self.v + other
	def __mul__(self, other):
		if isinstance(other, JType):
			return self.v * other.v
		return self.v * other
	def __hash__(self):
		return hash(self.v)
	def __repr__(self):
		return `self.v`

class JNum(JType):
	def make(self, val):
		if isinstance(val, str):
			if "e" in val:
				l, r = val.split("e")
				self.v = chooseNumFormat(l) * (10 ** int(r))
			elif val.endswith("o"):
				self.v = int(val[:-1], 8)
			elif val.endswith("h"):
				self.v = int(val[:-1], 16)
			elif val.endswith("b"):
				self.v = int(val)
			else:
				self.v = chooseNumFormat(val)
		else:
			self.v = val
		#Maybe add 0AFr39 or whatever for radix

class JArray(JType):
	def __repr__(self):
		return '('+" ".join(map(str, self.v))+')'
class JBlock(JType):
	def __repr__(self):
		return '{'+''.join(map(lambda x: str(x), self.v))+'}'
class JFunc(JType):pass
class EStr(JType):pass

def Error(string, exit=False):
	print "Error: %s" % string
	if exit:
		sys.exit(-1)

class Stack:
	def __init__(self, s=[]):
		self.s = s[:]
	def push(self, val):
		if val:
			if isinstance(val, list):
				self.s.extend(val)
			else:
				self.s.append(val)
	def pop(self):
		if self.s:
			return self.s.pop()
		else:
			Error("Pop from empty stack", True)