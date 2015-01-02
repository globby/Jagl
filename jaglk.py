import re

from jaglt import *
from jaglf import *

''' Regexes '''
JRE_Num = [
	re.compile(r"[0-8]+o"), 									#Octal
	re.compile(r"[\dA-F]+x"), 									#Hex
	re.compile(r"(?:-?\d+(?:\.(?:\d+)?)?|\.\d+|-?\d+)e-?\d+"), 	#Scientific
	re.compile(r"-?\d+(?:\.(?:\d+)?)?|-?\.\d+"), 				#Decimal
]

JRE_Str  = re.compile(r'"(?:[^\\"]|\\.)*"')						#String syntactic sugar
JRE_EStr = re.compile(r"'(?:[^\\/]|\\.)*'")						#Escaped string syntactic sugar


''' Preprocessor for shorthands '''
def preprocess(string):
	string = re.sub(r'([^\s\d\}orfuwF/%z])([orfuwF/%z])(?=([^"\\]*(\\.|"([^"\\]*\\.)*[^"\\]*"))*[^"]*$)(?=([^\'\\]*(\\.|\'([^\'\\]*\\.)*[^\'\\]*\'))*[^\']*$)', r"{\1}\2", string)							#Shorthand for one function map
	
	return string


''' Make a bracket map for array '''
def makeOuterMap(string, start, end, escape=None):
	if string:
		q, m = [], []
		lst = None
		for i, x in enumerate(string):
			if (escape and lst != escape) or not escape:
				if x == start:
					q.append(i)
				elif x == end:
					if len(q) == 1:
						m.append((q.pop(), i))
					else:
						q.pop()
			lst = x
		return m
	else:
		return []

''' Level Classification '''
def classifyLevel(string):
	c = []
	lists = map(lambda x: (x[0], x[1], JArray), makeOuterMap(string, "(", ")"))					#Extend with arrays
	lists.extend(map(lambda x: (x[0], x[1], JBlock), makeOuterMap(string, "{", "}")))			#Extend with blocks
	lists.extend(map(lambda x: (x.start(), x.end(), str) , JRE_Str.finditer(string)))			#Extend with strings
	lists.extend(map(lambda x: (x.start(), x.end(), EStr), JRE_EStr.finditer(string)))
	c.extend(lists)
	ints = []
	for r in JRE_Num:
		matches = map(lambda x: (x.start(), x.end(), JNum) ,list(r.finditer(string)))			#Get matches for int type
		matches = filter(lambda x: not any(y[0] <= x[0] < y[1] for y in ints), matches)			#Filter out overlapping int matches
		ints.extend(matches)
	c.extend(ints)
	symbols = [True for i in range(len(string))]												#Make a map to detect symbols
	for s, e, _ in c:																			#Filter out all already detected types
		if _ in [JArray, JBlock]:
			e = e + 1
		for x in range(s, e):
			symbols[x] = False
	for i, v in enumerate(string):																#Filter out all whitespace
		if re.match(r"\s", v):
			symbols[i] = False
	for i, s in enumerate(symbols):																#Make everything a symbol
		if s:
			c.append((i, i+1, JFunc))
	c = filter(lambda x: not any(y[0] < x[0] < y[1] for y in lists), c)							#Filter out any elements in arrays or blocks
	return sorted(c)

''' Recursively (possibly) create array '''
def makeArray(string):
	inner = string[1:]
	lev = classifyLevel(inner)
	arr = []
	for s, e, clss in lev:
		if clss == JNum:
			arr.append(JNum(inner[s:e]))
		elif clss == JFunc:
			arr.append(JFunc(inner[s:e]))
		elif clss in [JArray, JBlock]:
			arr.append(makeArray(inner[s:e]))
		elif clss == str:
			arr.append(JArray(map(lambda x: JNum(ord(x)), inner[s+1:e-1])))
		elif clss == EStr:
			arr.append(JArray(map(lambda x: JNum(ord(x)), inner[s+1:e-1].decode("string_escape"))))
	if string[0] == "(":
		return JArray(arr)
	return JBlock(arr)

''' Tokenizer '''
def tokenize(string):
	string = preprocess(string)
	il = classifyLevel(string)
	tokens = []
	for s, e, clss in il:
		if clss == JNum:
			tokens.append(JNum(string[s:e]))
		elif clss == JFunc:
			tokens.append(JFunc(string[s:e]))
		elif clss in [JArray, JBlock]:
			tokens.append(makeArray(string[s:e]))
		elif clss == str:
			tokens.append(JArray(map(lambda x: JNum(ord(x)), string[s+1:e-1])))
		elif clss == EStr:
			tokens.append(JArray(map(lambda x: JNum(ord(x)), string[s+1:e-1].decode("string_escape"))))
	return tokens