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
	parser.add_argument('filename', help='filename', nargs='?', default=None)
	parser.add_argument('-v', '--version', action='version', version='%(prog)s Alpha V1.1 Released Dec 18/2014')
	parser.add_argument('-i', '--inter', action='store_true', help='run the interactive interpreter')
	parser.add_argument('-c', '--code', help='execute code from the command line')
	parser.add_argument('-C', '--changelog',action='store_true', help='print changelog')
	args = parser.parse_args()

	if args.changelog:
		print """
  Changelog:

    Version 1.1:
      Added:
        'z' - Push space character (JNum(32))

        'Z' - Push line feed character (JNum(10))

        'Y':
          Arr, Any - Return an array of all indexes where an element appears
                     in an array

        Interpreter -C, changelog option

      Changed:
        Do and While no longer consume the test value to determine whether
        or not to continue looping

        Fixed dropif; it was dropping if the value was false instead of
        true

      Removed:
        Binary number syntax. May add back if actually needed somewhere in
        the future.

    Version 1.0:
      Initial release
"""			
		sys.exit(0)

	try:
		try:
			if args.inter:
				print "JAGL Interpreter Alpha V1.1 - Dec 18/2014"
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
				print "Usage: jagli.py [-h] [-C] [-i] [-c code] | filename"
		except Exception as e:
			Error(e, True)
	except KeyboardInterrupt:
		print "Exiting ..."