import sys
import math
import random
import itertools

#
import time
#

import jaglk

from jaglt import *
from jagli import *

''' Getch, shamefully stolen '''
#Source: http://code.activestate.com/recipes/134892/
class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys
    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt
    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()


def RFlatten(lst):
	if not lst:
		return lst
	if isinstance(lst[0], list):
		return RFlatten(lst[0]) + RFlatten(lst[1:])
	elif isinstance(lst[0], JArray):
		return RFlatten(lst[0].v) + RFlatten(lst[1:])
	return [lst[0]] + RFlatten(lst[1:])


''' Functions '''

FUNCTIONS = {}

def lr(stack):

	'''
		Return top two values of stack
	'''

	r = stack.pop()
	l = stack.pop()
	return l, r

def add(stack):

	'''
		Num, Num: Addition
		Arr, Arr: Extend l with r
		Arr, Any: Add item to end of array
		Any, Arr: Add item to beginning of array
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v+r.v))
	elif isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(l.v+r.v))
	elif isinstance(l, JArray):
		stack.push(JArray(l.v+[r]))
	elif isinstance(r, JArray):
		stack.push(JArray([l]+r.v))
	else:
		stack.push([l, r])
	return stack

def sub(stack):

	'''
		Num, Num: Subtraction
		Arr, Arr: Remove all items in right array from left, if left contains them
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v-r.v))
	elif isinstance(l, JArray) and isinstance(r, JArray):
		items = l.v
		for i in r.v:
			if i in items:
				items.remove(i)
		stack.push(JArray(items))
	else:
		stack.push([l, r])
	return stack

def mult(stack):

	'''
		Num, Num: Multiply
		Arr, Num: Duplicate items in list r times (flatten into single list)
		Num, Arr: Duplicate list r times and encase in list
		Blk, Num: Execute block x times
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v*r.v))
	elif isinstance(l, JArray) and isinstance(r, JNum):
		newarr = reduce(list.__add__, [l.v for i in range(r.v)])
		stack.push(JArray(newarr))
	elif isinstance(l, JNum) and isinstance(r, JArray):
		newarr = [r for i in range(l.v)]
		stack.push(JArray(newarr))
	elif isinstance(l, JBlock) and isinstance(r, JNum):
		for x in range(r.v):
			stack = runOn(l.v, stack)
	else:
		stack.push([l, r])
	return stack

def prnt(stack):
	
	'''
		Any: Write string representation
	'''
	#For prnt and prntC, should it consume the value after printing?

	top = stack.pop()
	trep = str(top)
	if isinstance(top, JNum) and trep.endswith("L"):
		sys.stdout.write(trep[:-1])
	else:
		sys.stdout.write(trep)
	return stack

def prntC(stack):

	'''
		Num: Write character
		Arr: Write String
		Any: Write string representation
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		sys.stdout.write(chr(top.v))
	elif isinstance(top, JArray):
		try:
			string = ''.join(map(lambda x: chr(x.v), top.v))
		except Exception, e:
			Error("Can only convert JArray of JNum to string")
		else:
			sys.stdout.write(string)
	else:
		trep = `top.v`
		if isinstance(top, JNum) and trep.endswith("L"):
			sys.stdout.write(`top.v`[:-1])
		else:
			sys.stdout.write(`top.v`)
	return stack

def len_(stack):

	'''
		Arr: Len
		Blk: Len
		Num: Log e
	'''

	top = stack.pop()
	if isinstance(top, JArray) or isinstance(top, JArray):
		stack.push([top, JNum(len(top.v))])
	elif isinstance(top, JNum):
		stack.push([top, JNum(float(math.log(top.v)))])
	else:
		stack.push(top)
	return stack

def log(stack):

	'''
		Num, Num: l Log r
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(float(math.log(l.v, r.v))))
	else:
		stack.push([l, r])
	return stack

def mod(stack):

	'''
		Num, Num: Modulus
		Arr, Blk: Filter
		Arr, Arr: Zip
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v%r.v))
	elif isinstance(l, JArray) and isinstance(r, JBlock):
		newarr = []
		for item in l.v:
			stack.push(item)
			stack = runOn(r.v, stack)
			if stack.pop().v != 0:
				newarr.append(item)
		stack.push(JArray(newarr))
	elif isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(zip(l.v, r.v)))
	else:
		stack.push([l, r])
	return stack

def div(stack):

	'''
		Num, Num: Divide
		Arr, Blk: Map
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v/r.v))
	elif isinstance(l, JArray) and isinstance(r, JBlock):
		newarr = []
		for item in l.v:
			stack.push(item)
			stack = runOn(r.v, stack)
			newarr.append(stack.pop())
		stack.push(JArray(newarr))
	else:
		stack.push([l, r])
	return stack

def eq(stack):
	
	'''
		Any, Any: Tests Equality
	'''

	l, r = lr(stack)
	if type(l) == type(r):
		if l.v == r.v:
			stack.push(JNum(1))
		else:
			stack.push(JNum(0))
	else:
		stack.push(JNum(0))
	return stack

def lt(stack):

	'''
		Any, Any: Less than
	'''

	l, r = lr(stack)
	v = 1 if l.v < r.v else 0
	stack.push(JNum(v))
	return stack

def gt(stack):

	'''
		Any, Any: Greater than
	'''

	l, r = lr(stack)
	v = 1 if l.v>r.v else 0
	stack.push(JNum(v))
	return stack

def pow_(stack):

	'''
		Num, Num: To the power of
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v**r.v))
	else:
		stack.push([l, r])
	return stack

def range_(stack):

	'''
		Num, Num: Range
		Array, Block: Fold right
	'''

	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JArray(map(JNum,range(l.v, r.v))))
	elif isinstance(l, JArray) and isinstance(r, JBlock):
		arr = l.v[::-1]
		if arr:
			acc = arr[0]
			arr = arr[1:]
			for val in arr:
				stack.push([acc, val])
				stack = runOn(r.v, stack)
				acc = stack.pop()
			stack.push(acc)
		#Should JNum(0) be pushed if the array is empty?
	else:
		stack.push([l, r])
	return stack

def rand(stack):

	'''
			 Arr: Random element from array
		Num, Num: Randint in range
		Arr, Num: X random elements from array (encased in an array)
	'''

	r = stack.pop()
	if isinstance(r, JNum):
		l = stack.pop()
		if isinstance(l, JNum):
			stack.push(JNum(random.randint(l.v, r.v)))
		elif isinstance(l, JArray):
			newarr = []
			for _ in range(r.v):
				newarr.append(random.choice(l.v))
			stack.push(JArray(newarr))
		else:
			stack.push([l, r])
	elif isinstance(r, JArray):
		stack.push(random.choice(r.v))
	else:
		stack.push([l, r])
	return stack

def string(stack):

	'''
		Any: Convert to string representation
	'''

	top = stack.pop()
	stack.push(JArray(map(lambda x: JNum(ord(x)),`top.v`)))
	return stack

def ctoi(stack):

	'''
		Num: Convert ascii 48-58 to 0-9
		Arr: Convert from string to number
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		if 47 < top.v < 59:
			stack.push(JNum(top.v-48))
		else:
			stack.push(top)
	elif isinstance(top, JArray):
		try:
			num = chooseNumFormat("".join(map(lambda x: chr(x.v),top.v)))
		except:
			stack.push(top)											#Maybe want to push -1?
		else:
			stack.push(JNum(num))
	else:
		stack.push(top)
	return stack

def dup(stack):

	'''
		Any: Duplicate
	'''

	top = stack.pop()
	stack.push([top, top])
	return stack

def drop(stack):

	'''
		Any: Drop item
	'''
	top = stack.pop()
	return stack

def not_(stack):

	'''
		Any: Reverse truthy falsy value
	'''
	top = stack.pop()
	new = 1 if not top.v else 0
	stack.push(JNum(new))
	return stack

def swap(stack):

	'''
		Any, Any: Swap top two items
	'''

	l, r = lr(stack)
	stack.push([r, l])
	return stack

def do(stack):

	'''
		Blk: Do blk and then pop, if true then continue
	'''
	#For do and while, should it consume the conditional value?
	
	top = stack.pop()
	if isinstance(top, JBlock):
		while True:
			stack = runOn(top.v, stack)
			val = stack.pop()
			stack.push(val)
			if not val.v:
				break
	else:
		stack.push(top)
	return stack

def while_(stack):
	
	'''
		Blk: Pop value, if true then execute block
	'''

	top = stack.pop()
	if isinstance(top, JBlock):
		while True:
			val = stack.pop()
			stack.push(val)
			if not val.v:
				break
			stack = runOn(top.v, stack)
	else:
		stack.push(top)
	return stack

def cycle(stack):

	'''
		Cycle stack one rotation to the right
	'''

	s = stack.s
	s = [s[-1]]+s[:-1]
	return Stack(s)

def cycle_(stack):

	'''
		Num: Cycle stack x rotations
		Arr: Reverse array
	'''

	top = stack.pop()
	s = stack.s
	if isinstance(top, JNum):
		if top.v >= 0:
			for _ in range(top.v):
				s = [s[-1]]+s[:-1]
		else:
			for _ in range(top.v*-1):
				s = s[1:]+[s[0]]
	elif isinstance(top, JArray):
		stack.push(JArray(top.v[::-1]))
	else:
		s.append(top)
	return Stack(s)

def all_(stack):
	'''
		Arr: All
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		v = all(bool(x.v) for x in top.v)
		stack.push(JNum(1) if v else JNum(0))
	else:
		stack.push(top)
	return stack

def any_(stack):
	
	'''
		Arr: Any
		Num: Absolute
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		v = any(bool(x.v) for x in top.v)
		stack.push(JNum(1) if v else JNum(0))
	elif isinstance(top, JNum):
		stack.push(JNum(abs(top.v)))
	else:
		stack.push(top)
	return stack

def rot(stack):

	'''
		Any, Any, Any: Rotate top 3 items on stack to the right
	'''

	top = stack.pop()
	sec = stack.pop()
	thrd = stack.pop()
	stack.push([top, thrd, sec])
	return stack

def and_(stack):

	'''
		Any, Any: And
	'''

	l, r = lr(stack)
	stack.push(JNum(1) if l.v and r.v else JNum(0))
	return stack

def or_(stack):

	'''
		Any, Any: Or
	'''

	l, r = lr(stack)
	stack.push(JNum(1) if l.v or r.v else JNum(0))
	return stack

def dropif(stack):

	'''
		Any, Any: If right then keep
	'''

	l, r = lr(stack)
	if r.v:
		stack.push(l)
	return stack

def if_(stack):

	'''
		Blk, Any: If r, do block
	'''

	l, r = lr(stack)
	if isinstance(l, JBlock):
		if r.v:
			stack = runOn(l.v, stack)
	else:
		stack.push([l, r])
	return stack

def ifelse(stack):

	'''
		Blk, Blk, Any: If cnd, run r, else run l
		Any, Any, Any: If cnd, keep r, else keep l
	'''

	cnd = stack.pop()
	i = stack.pop()
	e = stack.pop()
	if isinstance(i, JBlock) and isinstance(e, JBlock):
		if cnd.v:
			stack = runOn(i.v, stack)
		else:
			stack = runOn(e.v, stack)
	else:
		if cnd.v:
			stack.push(i)
		else:
			stack.push(e)
	return stack

def elem(stack):

	'''
		Arr, Any: Elem in array
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		stack.push(JNum(1) if r in l.v else JNum(0))
	else:
		stack.push([l, r])
	return stack

def unfold(stack):

	'''
		Arr: Push all elements to stack (unfold, unpack, whatever)
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		for x in top.v:
			stack.push(x)
	else:
		stack.push(top)
	return stack

def isPrime(stack):

	'''
		Num: Pushes 1 if prime, 0 if not
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		i, prime = top.v, True
		if i > 0:
			if i <= 3:
				pass
			elif i%2==0 or i%3==0:
				prime = False
			for n in range(5, int(i**0.5)+1, 6):
				if i % n == 0 or i % (n+2) == 0:
					prime = False

		stack.push(JNum(1) if prime else JNum(0))
	else:
		stack.push(top)
	return stack

def left(stack):

	'''
		Arr, Blk: Fold left
	'''

	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance (r, JBlock):
		arr = l.v
		if arr:
			acc = arr[0]
			arr = arr[1:]
			for val in arr:
				stack.push([acc, val])
				stack = runOn(r.v, stack)
				acc = stack.pop()
			stack.push(acc)
	else:
		stack.push([l, r])
	return stack

def lenstack(stack):

	'''
		Pushes length of stack
	'''
	stack.push(JNum(len(stack.s)))
	return stack

def intersection(stack):
	
	'''
		Arr, Arr: Set intersection
	'''

	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) | set(r.v)))))
	else:
		stack.push([l, r])
	return stack

def difference(stack):

	'''
		Arr, Arr: Set difference
	'''

	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) - set(r.v)))))
	else:
		stack.push([l, r])
	return stack

def symdifference(stack):

	'''
		Arr, Arr: Set symmetric difference
	'''

	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) ^ set(r.v)))))
	else:
		stack.push([l, r])
	return stack

def tilde(stack):

	'''
		Num: Bitwise not
		Arr: Evaluate string
		Blk: Run block
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(~top.v))
	elif isinstance(top, JArray):
		string = ""
		for item in top.v:
			if not isinstance(item, JNum):
				stack.push(top)
				return stack
			string += chr(item.v)
		tokens = jaglk.tokenize(string)
		stack = runOn(tokens, stack)
	elif isinstance(top, JBlock):
		stack = runOn(top.v, stack)
	else:
		stack.push(top)
	return stack

def getChar(stack):
	
	'''
		Gets a character and pushes its ascii value
	'''

	stack.push(JNum(ord(getch())))
	return stack

def getLine(stack):
	
	'''
		Gets a line of text and pushes as an array of ascii values
	'''

	stack.push(JArray(map(lambda x: JNum(ord(x)),sys.stdin.readline()[:-1])))		#Should this keep the newline?
	return stack

def inc(stack):
	
	'''
		Num: Increment
		Arr: Rotate right
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(top.v+1))
	elif isinstance(top, JArray):
		stack.push(JArray([top.v[-1]]+top.v[:-1]))
	else:
		stack.push(top)
	return stack


def dec(stack):

	'''
		Num: Decrement
		Arr: Rotate left
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(top.v-1))
	elif isinstance(top, JArray):
		new = top.v[1:]
		new += [top.v[0]] if top.v else []
		stack.push(JArray(new))
	else:
		stack.push(top)
	return stack

def clearstack(stack):

	'''
		Clears the stack
	'''

	stack.s = []
	return stack

def isalphanum(stack):
	
	'''
		Num: Checks if char is alphanumeric
		Arr: Checks if string is alphanumeric
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isalnum() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isalnum() else JNum(0))
	else:
		stack.push(top)
	return stack

def isnum(stack):
	
	'''
		Num: Checks if char is numeric
		Arr: Checks if string is numeric
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isdigit() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isdigit() else JNum(0))
	else:
		stack.push(top)
	return stack


def iswhitespace(stack):

	'''
		Num: Checks if char is whitespace
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isspace() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isspace() else JNum(0))
	else:
		stack.push(top)
	return stack

def splitAt(stack):

	'''
		Arr, Any: Split at occurrences of elem
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		lv = l.v
		stack.push(JArray(map(JArray, [list(group) for k, group in itertools.groupby(lv, lambda x: x==r) if not k])))
	else:
		stack.push([l, r])
	return stack

def flatten(stack):

	'''
		Arr: Flatten
		Num: Converts to float
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(RFlatten(top.v)))
	elif isinstance(top, JNum):
		stack.push(JNum(float(top.v)))
	else:
		stack.push(top)
	return stack


def itos(stack):

	'''
		Num: Number to its string representation
	'''

	top = stack.pop()
	if isinstance(top, JNum):
		tr = `top.v`
		if tr.endswith("L"):
			tr = tr[:-1]
		stack.push(JArray(map(lambda x: JNum(ord(x)),tr)))
	else:
		stack.push(top)
	return stack

def halt(stack):

	'''
		Force quit the program
	'''

	sys.exit(0)

def slice_(stack):

	'''
		Arr, Num: 		Push Arr[Int]
		Arr, Num, Num: 	Push Arr[Int:Int]
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		stack.push(JArray([l.v[r.v]]))
	elif isinstance(l, JNum):
		arr = stack.pop()
		if isinstance(arr, JArray):
			stack.push(JArray(arr.v[l.v:r.v]))
		else:
			stack.push([arr, l, r])
	else:
		stack.push([l, r])
	return stack

def remdups(stack):

	'''
		Arr: Remove duplicates, JArray(list(set(stack.pop().v)))
		Num: Convert to integer
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(list(set(top.v))))
	elif isinstance(top, JNum):
		stack.push(JNum(int(top.v)))
	else:
		stack.push(top)
	return stack

def weave(stack):

	'''
		Arr, Any: Add the any value between every value in array
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		new = []
		for e in l.v:
			new.append(e)
			new.append(r)
		new.pop()
		stack.push(new)
	else:
		stack.push([l, r])
	return stack

def index(stack):

	'''
		Arr, Any: Push index of match, or -1
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		try:
			idx = l.v.index(r)
		except ValueError:
			idx = -1
		stack.push(JNum(idx))
	else:
		stack.push([l, r])
	return stack

def space(stack):

	'''
		Push the space character (32)
	'''

	stack.push(JNum(32))
	return stack

def linefeed(stack):

	'''
		Push the line feed character (10)
	'''

	stack.push(JNum(10))
	return stack

def findall(stack):

	'''
		Arr, Any: Find all occurrences of Any in Arr
	'''

	l, r = lr(stack)
	if isinstance(l, JArray):
		stack.push(JArray([JNum(i) for i, v in enumerate(l.v) if v == r]))
	else:
		stack.push([l, r])
	return stack

def min_(stack):

	'''
		Arr: Minimum
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(min(top.v)))
	else:
		stack.push(top)
	return stack

def max_(stack):

	'''
		Arr: Maximum
	'''
	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(max(top.v)))
	else:
		stack.push(top)
	return stack

def sorted_(stack):
	
	'''
		Arr: Sorted array
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(sorted(top.v)))
	else:
		stack.push(top)
	return stack

def sum_(stack):
	
	'''
		Arr: Sum of array (hacky solution)
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		try:
			string = " ".join(map(lambda x: str(x), top.v))
			string += "+"*(len(top.v)-1)
			stack = runOn(jaglk.tokenize(string), stack)
		except:
			stack.push(JNum(-1))									#Should it push -1?
	else:
		stack.push(top)
	return stack

def product_(stack):
	
	'''
		Arr: Product of array
	'''

	top = stack.pop()
	if isinstance(top, JArray):
		try:
			string = " ".join(map(lambda x: str(x), top.v))
			string += "*"*(len(top.v)-1)
			stack = runOn(jaglk.tokenize(string), stack)
		except:
			stack.push(JNum(-1))									#Should it push -1?
	else:
		stack.push(top)
	return stack

def UNDEFINED(stack):
	return stack

def debug(stack):
	s = stack.s
	print " ".join(map(lambda x: "%s< %s >" % (x.__class__.__name__, x), s))
	return stack

FUNCTIONS = {
	"+":add,
	"-":sub,
	"*":mult,
	"/":div,
	"=":eq,
	"<":lt,
	">":gt,
	"^":pow_,
	"%":mod,
	"&":and_,
	"|":or_,
	"@":rot,
	"~":tilde,
	":":slice_,
	";":index,
	"[":inc,
	"]":dec,
	"$":weave,
	"a":any_,
	"A":all_,
	"b":sum_,
	"B":product_,
	"c":cycle,
	"C":cycle_,
	"d":dup,
	"D":drop,
	"e":elem,
	"E":flatten,
	"f":if_,
	"F":ifelse,
	"g":itos,
	"G":UNDEFINED,
	"h":halt,
	"H":UNDEFINED,
	"i":ctoi,
	"I":dropif,
	"j":remdups,
	"J":sorted_,
	"k":UNDEFINED,
	"K":UNDEFINED,
	"l":len_,
	"L":log,
	"m":isPrime,
	"M":isnum,
	"n":not_,
	"N":isalphanum,
	"o":left,
	"O":iswhitespace,
	"p":prntC,
	"P":prnt,
	"q":min_,
	"Q":max_,
	"r":range_,
	"R":rand,
	"s":string,
	"S":swap,
	"t":getChar,
	"T":getLine,
	"u":do,
	"U":unfold,
	"v":intersection,
	"V":difference,
	"w":while_,
	"W":symdifference,
	"x":lenstack,
	"X":clearstack,
	"y":splitAt,
	"Y":findall,
	"z":space,
	"Z":linefeed,
	"#":debug
}
