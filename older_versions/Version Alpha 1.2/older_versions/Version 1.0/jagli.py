import os
import argparse

from jaglk import *
from jaglt import *
import jaglf

def runOn(tokens, stack):
	for tok in tokens:
		if isinstance(tok, JFunc):
			f = jaglf.FUNCTIONS[tok.v]
			stack = f(stack)
		else:
			stack.push(tok)
	return stack

def runCode(code):
	tokens = tokenize(code)
	s = Stack()
	return runOn(tokens, s)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="JAGL (Just A Golfing Language) Interpreter")
	parser.add_argument('filename', help='Filename', nargs='?', default=None)
	parser.add_argument('-v', '--version', action='version', version='%(prog)s Alpha V1.0')
	parser.add_argument('-i', '--inter', action='store_true', help='Run the interactive interpreter')
	parser.add_argument('-c', '--code', help='Execute code from the command line')
	args = parser.parse_args()

	try:
		try:
			if args.inter:
				print "JAGL Interpreter Alpha V1.0"
				s = Stack()
				while True:
					try:
						s = runOn(tokenize(raw_input(">")), s)
					except EOFError:
						break
			elif args.code:
				runCode(args.code)
			elif args.filename:
				if os.path.isfile(args.filename):
					with open(args.filename, "r") as f:
						data = f.read()
					runCode(data)
				else:
					print "Error: File not found"
			else:
				print "Usage: jagli.py [-h] [-i] [-c code] | filename"
		except Exception as e:
			Error(e, True)
	except KeyboardInterrupt:
		print "Exiting ..."