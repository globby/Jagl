import sys
import math
import random
import itertools

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

''' Helper functions '''
def RFlatten(lst):
	if not lst:
		return lst
	if isinstance(lst[0], list):
		return RFlatten(lst[0]) + RFlatten(lst[1:])
	elif isinstance(lst[0], JArray):
		return RFlatten(lst[0].v) + RFlatten(lst[1:])
	return [lst[0]] + RFlatten(lst[1:])

def lr(stack):
	r = stack.pop()
	l = stack.pop()
	return l, r


''' JAGL Functions '''


FUNCTIONS = {}


#Num, Num: Numeric addition
#Arr, Arr: Array concatenation
#Arr, Any: Add arg2 to end of arg1
#Any, Arr: Add arg2 to beginning of array
def plus(stack):
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


#Num, Num: Numeric addition
#Arr, Arr: Remove all items in arg2 from arg1 (if arg1 contains the item)
def minus(stack):
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


#Num, Num: Numeric multiplication
#Arr, Num: Duplicate arg1 arg2 times, and then combine into a single list
#Num, Arr: Duplicate arg2 arg1 times, and encase in a list
#Blk, Num: Execute arg1 arg2 times
def asterisk(stack):
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


#Num, Num: Numeric division
#Arr, Blk: Map
def fslash(stack):
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


#Any, Any: Tests for value equality
def eq(stack):
	l, r = lr(stack)
	if type(l) == type(r):
		if l.v == r.v:
			stack.push(JNum(1))
		else:
			stack.push(JNum(0))
	else:
		stack.push(JNum(0))
	return stack


#Any, Any: Less than
def lt(stack):
	l, r = lr(stack)
	v = 1 if l.v < r.v else 0
	stack.push(JNum(v))
	return stack


#Any, Any: Greater than
def gt(stack):
	l, r = lr(stack)
	v = 1 if l.v>r.v else 0
	stack.push(JNum(v))
	return stack


#Num, Num: Raise arg1 to the arg2'th power
def caret(stack):
	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(l.v**r.v))
	else:
		stack.push([l, r])
	return stack


#Num, Num: Modulus
#Arr, Blk: Filter
#Arr, Arr: Zip
def percent(stack):
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
		stack.push(JArray(map(lambda x: JArray(x),zip(l.v, r.v))))
	else:
		stack.push([l, r])
	return stack


#Any, Any: Boolean AND
def and_(stack):
	l, r = lr(stack)
	stack.push(JNum(1) if l.v and r.v else JNum(0))
	return stack


#Any, Any: BOOLEAN OR
def or_(stack):
	l, r = lr(stack)
	stack.push(JNum(1) if l.v or r.v else JNum(0))
	return stack


#Any, Any, Any: Rotate top 3 items on stack once clockwise
def at(stack):
	top = stack.pop()
	sec = stack.pop()
	thrd = stack.pop()
	stack.push([top, thrd, sec])
	return stack


#Num: Bitwise NOT
#Arr: Evaluate string as Jagl code
#Blk: Execute block once
def tilde(stack):
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


#Arr, Num: Push Arr[Int]
#Arr, Num, Num: Push Arr[Int:Int]
def colon(stack):
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


#Arr, Any: Push index of match, or -1
def semicolon(stack):
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


#Num: Increment
#Arr: Rotate right
def sbracko(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(top.v+1))
	elif isinstance(top, JArray):
		stack.push(JArray([top.v[-1]]+top.v[:-1]))
	else:
		stack.push(top)
	return stack


#Num: Decrement
#Arr: Rotate left
def sbrackc(stack):
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


#Arr, Any: And arg2 between every value in arg1
def dollarsign(stack):
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


#Num: Absolute
#Arr: Boolean ANY
def a(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		v = any(bool(x.v) for x in top.v)
		stack.push(JNum(1) if v else JNum(0))
	elif isinstance(top, JNum):
		stack.push(JNum(abs(top.v)))
	else:
		stack.push(top)
	return stack


#Arr: Boolean ALL
def A(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		v = all(bool(x.v) for x in top.v)
		stack.push(JNum(1) if v else JNum(0))
	else:
		stack.push(top)
	return stack


#Arr: Sum of array
def b(stack):
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


#Arr: Product of array
def B(stack):
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


#Cycle stack one rotation counterclockwise
def c(stack):
	s = stack.s
	s = [s[-1]]+s[:-1]
	return Stack(s)


#Num: Cycle stack arg1 rotations
#Arr: Reverse array
def C(stack):
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


#Any: Duplicate
def d(stack):
	top = stack.pop()
	stack.push([top, top])
	return stack


#Drop an item from the stack
def D(stack):
	top = stack.pop()
	return stack


#Arr, Any: Pushes 1 if arg2 is in arg1, 0 otherwise
def e(stack):
	l, r = lr(stack)
	if isinstance(l, JArray):
		stack.push(JNum(1) if r in l.v else JNum(0))
	else:
		stack.push([l, r])
	return stack


#Arr: Flatten array
#Num: Convert to float
def E(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(RFlatten(top.v)))
	elif isinstance(top, JNum):
		stack.push(JNum(float(top.v)))
	else:
		stack.push(top)
	return stack


#Any, Blk: If arg1, do arg2
#Any, Any: If arg1, keep arg2
def f(stack):
	l, r = lr(stack)
	if isinstance(r, JBlock):
		if l.v:
			stack = runOn(r.v, stack)
	else:
		if l.v:
			stack.push(r)
	return stack


#Any, Blk, Blk: If arg1, run arg3, else run arg2
#Any, Any, Any: If arg1, keep arg3, else keep arg2
def F(stack):
	i = stack.pop()
	e = stack.pop()
	cnd = stack.pop()
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


#Num: Convert a number to its equivalent string representation
def g(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		tr = `top.v`
		if tr.endswith("L"):
			tr = tr[:-1]
		stack.push(JArray(map(lambda x: JNum(ord(x)),tr)))
	else:
		stack.push(top)
	return stack


#Num: Encase up to x items from stack in array
#Any: Encase whole stack in array
def G(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		v,out=top.v,[]
		while v and stack.s:
			out.append(stack.pop())
			v-=1
		stack.push(JArray(out[::-1]))
	else:
		out=[top]
		while stack.s:
			out.append(stack.s.pop())
		stack.push(JArray(out[::-1]))
	return stack


#Forcibly halt the program
def h(stack):
	sys.exit(0)


#Num: Convert 48-58 to 0-9
#Arr: Convert from string to number
def i(stack):
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


#Num: Checks if character is numeric
#Arr: Checks all characters in string are numeric
def I(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isdigit() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isdigit() else JNum(0))
	else:
		stack.push(top)
	return stack


#Arr: Remove duplicates from array
#Num: Convert to integer
def j(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(list(set(top.v))))
	elif isinstance(top, JNum):
		stack.push(JNum(int(top.v)))
	else:
		stack.push(top)
	return stack


#Arr: Sort array
def J(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(JArray(sorted(top.v)))
	else:
		stack.push(top)
	return stack


#Push space (32)
def k(stack):
	stack.push(JNum(32))
	return stack


#Push linefeed (10)
def K(stack):
	stack.push(JNum(10))
	return stack


#Arr: Length
#Blk: Length
#Num: Log e
def l(stack):
	top = stack.pop()
	if isinstance(top, JArray) or isinstance(top, JArray):
		stack.push([top, JNum(len(top.v))])
	elif isinstance(top, JNum):
		stack.push([top, JNum(float(math.log(top.v)))])
	else:
		stack.push(top)
	return stack


#Num, Num: arg1 log arg2
def L(stack):
	l, r = lr(stack)
	if isinstance(l, JNum) and isinstance(r, JNum):
		stack.push(JNum(float(math.log(l.v, r.v))))
	else:
		stack.push([l, r])
	return stack


#Num: Primality test
#Arr: Minimum of array
def m(stack):
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
	elif isinstance(top, JArray):
		stack.push(min(top.v))
	else:
		stack.push(top)
	return stack


#Arr: Maximum of array
def M(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		stack.push(max(top.v))
	else:
		stack.push(top)
	return stack


#Reverses the truth value
def n(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		new = JArray([JNum(17)]) if not top.v else JArray([])
	else:
		new = JNum(1) if top.v else JNum(0)
	stack.push(new)
	return stack


#Num: Checks if character is alphanumeric
#Arr: Checks if all characters in string are alphanumeric
def N(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isalnum() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isalnum() else JNum(0))
	else:
		stack.push(top)
	return stack


#Arr, Blk: Fold left with function
def o(stack):
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


#Num: Checks if character is whitespace
#Arr: Checks if all characters in string are whitespace
def O(stack):
	top = stack.pop()
	if isinstance(top, JNum):
		stack.push(JNum(1) if chr(top.v).isspace() else JNum(0))
	elif isinstance(top, JArray):
		stack.push(JNum(1) if ''.join(map(lambda x: chr(x.v), top.v)).isspace() else JNum(0))
	else:
		stack.push(top)
	return stack


#Num: Convert to character and output
#Arr: Convert to string and output
#Any: Write string representation
def p(stack):
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


#Any: Write string representation
def P(stack):
	top = stack.pop()
	trep = str(top)
	if isinstance(top, JNum) and trep.endswith("L"):
		sys.stdout.write(trep[:-1])
	else:
		sys.stdout.write(trep)
	return stack


#Num, Num: Range from arg1 to arg2
#     Num: Range up to arg1
#Arr, Blk: Fold right with arg2
def r(stack):
	r = stack.pop()
	if len(stack.s):
		l = stack.pop()
		if isinstance(l, JNum) and isinstance(r, JNum):
			stack.push(JArray(map(JNum,range(l.v, r.v))))
		elif isinstance(r, JNum):
			stack.push(l)
			stack.push(JArray(map(JNum, range(r.v))))
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
	else:
		if isinstance(r, JNum):
			stack.push(JArray(map(JNum,range(r.v))))
		else:
			stack.push(r)
	return stack


#Arr: Push a random element from arg1
#Num, Num: Push a random integer between arg1 and arg2
#Arr, Num: Push an array containing arg2 random items from arg1
def R(stack):
	r = stack.pop()
	if isinstance(r, JNum):
		l = stack.pop()
		if isinstance(l, JNum):
			stack.push(JNum(random.randint(l.v, r.v)))
		elif isinstance(l, JArray):
			newarr = []
			for _ in range(r.v):
				newarr.append(random.choice(l.v))
			stack.push(l)
			stack.push(JArray(newarr))
		else:
			stack.push([l, r])
	elif isinstance(r, JArray):
		stack.push(r)
		stack.push(random.choice(r.v))
	else:
		stack.push([l, r])
	return stack


#Any: Convert to string representation
def s(stack):
	top = stack.pop()
	stack.push(JArray(map(lambda x: JNum(ord(x)),`top.v`)))
	return stack


#Any, Any: Swap order of arg1 and arg2
def S(stack):
	l, r = lr(stack)
	stack.push([r, l])
	return stack


#Gets a character from stdin and pushes its ascii value
def t(stack):
	stack.push(JNum(ord(getch())))
	return stack


#Gets a line of input from stdin and pushes an array of ascii values
def T(stack):
	stack.push(JArray(map(lambda x: JNum(ord(x)),sys.stdin.readline()[:-1])))
	return stack


#Blk: Run block, pop a value, and if that value is true then continue
def u(stack):
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


#Arr: Push all elements from array to stack
def U(stack):
	top = stack.pop()
	if isinstance(top, JArray):
		for x in top.v:
			stack.push(x)
	else:
		stack.push(top)
	return stack


#Arr, Arr: Set intersection
def v(stack):
	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) | set(r.v)))))
	else:
		stack.push([l, r])
	return stack


#Arr, Arr: Set difference
def V(stack):
	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) - set(r.v)))))
	else:
		stack.push([l, r])
	return stack


#Blk: Pop value, if true then execute block and repeat
def w(stack):
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


#Arr, Arr: Set symmetric difference
def W(stack):
	l, r = lr(stack)
	if isinstance(l, JArray) and isinstance(r, JArray):
		stack.push(JArray(sorted(list(set(l.v) ^ set(r.v)))))
	else:
		stack.push([l, r])
	return stack


#Pushes the length of the stack
def x(stack):
	stack.push(JNum(len(stack.s)))
	return stack


#Clears the stack
def X(stack):
	stack.s = []
	return stack


#Arr, Any: Split array at occurrences of elem, and encase in an array
def y(stack):
	l, r = lr(stack)
	if isinstance(l, JArray):
		lv = l.v
		stack.push(JArray(map(JArray, [list(group) for k, group in itertools.groupby(lv, lambda x: x==r) if not k])))
	else:
		stack.push([l, r])
	return stack


#Arr, Any: Find all occurrences of arg2 in arg1
def Y(stack):
	l, r = lr(stack)
	if isinstance(l, JArray):
		stack.push(JArray([JNum(i) for i, v in enumerate(l.v) if v == r]))
	else:
		stack.push([l, r])
	return stack


#Arr, Arr, Blk: Zip with block
def z(stack):
	a2, bl = lr(stack)
	a = stack.pop()
	if isinstance(a, JArray) and isinstance(a2, JArray) and isinstance(bl, JBlock):
		tempstack = Stack()
		a_, a2_ = a.v, a2.v
		new = []
		while a_ or a2_:
			if a_:
				tempstack.push(a_.pop(0))
			if a2_:
				tempstack.push(a2_.pop(0))
			tempstack = runOn(bl.v, tempstack)
			if len(tempstack.s) == 1:
				new.append(tempstack.s[0])
			else:
				new.append(tempstack.s)
			tempstack.s=[]
		stack.push(JArray(new))
	else:
		stack.push([a,a2,bl])
	return stack


#Print stack for debugging
def pound(stack):
	s = stack.s
	print " ".join(map(lambda x: "%s< %s >" % (x.__class__.__name__, x), s))
	return stack


#Default value for undefined functions
def UNDEFINED(stack):
	return stack

FUNCTIONS = {
	"+":plus,
	"-":minus,
	"*":asterisk,
	"/":fslash,
	"=":eq,
	"<":lt,
	">":gt,
	"^":caret,
	"%":percent,
	"&":and_,
	"|":or_,
	"@":at,
	"~":tilde,
	":":colon,
	";":semicolon,
	"[":sbracko,
	"]":sbrackc,
	"$":dollarsign,
	"a":a,
	"A":A,
	"b":b,
	"B":B,
	"c":c,
	"C":C,
	"d":d,
	"D":D,
	"e":e,
	"E":E,
	"f":f,
	"F":F,
	"g":g,
	"G":G,
	"h":h,
	"H":UNDEFINED,
	"i":i,
	"I":I,
	"j":j,
	"J":J,
	"k":k,
	"K":K,
	"l":l,
	"L":L,
	"m":m,
	"M":M,
	"n":n,
	"N":N,
	"o":o,
	"O":O,
	"p":p,
	"P":P,
	"q":UNDEFINED,
	"Q":UNDEFINED,
	"r":r,
	"R":R,
	"s":s,
	"S":S,
	"t":t,
	"T":T,
	"u":u,
	"U":U,
	"v":v,
	"V":V,
	"w":w,
	"W":W,
	"x":x,
	"X":X,
	"y":y,
	"Y":Y,
	"z":z,
	"Z":UNDEFINED,
	"#":pound
}
