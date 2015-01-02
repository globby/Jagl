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
	parser.add_argument('-v', '--version', action='version', version='%(prog)s Alpha V1.3 Released Jan 2/2015')
	parser.add_argument('-i', '--inter', action='store_true', help='run the interactive interpreter')
	parser.add_argument('-c', '--code', help='execute code from the command line')
	parser.add_argument('-C', '--changelog',action='store_true', help='print changelog')
	args = parser.parse_args()

	if args.changelog:
		print """
  Changelog:

    Version 1.3:
      Added:
        1) Additional functionality was added to 'n' when operating on arrays
        2) 'z' - Now performs a zipWith, using a temporary stack
        3) 'G' - Now encases the stack in an array
        4) Short circuit syntax (see documentation)

      Changed:
        1) The conditional value in if and ifelse is now the leftmost argument
        2) The conditional drop ('I') is now built into 'f'
        3) 'R', when operating with arrays, no longer consumes the array
        4) 'k' and 'K' replace 'z' and 'Z' respectively
        5) 'q' (min) and 'Q' (max) are now 'm', and 'M' respectively
        6) 'I' now functions as 'M' did (isNumeric)

      Removed:
        1) 'q' and 'Q' are now obsolete (see Changed #5)

    Version 1.2:
      Added:
        1) 'q' - Push minimum value of array
        2) 'Q' - Push maximum value of array
        3) 'b' - Push sum of array (more accurately, fold array with the '+'
                 function)
        4) 'B' - Push product of array (more accurately, fold array with the '*'
                 function)
        5) 'J' - Push sorted array

      Changed:
        1) '%' - If used on two arrays, now zips the arrays
        2) 'M' (isNumeric), 'N' (isAlphaNumeric), and 'O' (isWhitespace)
           now work on arrays as well (performing the function to
           every element in the array and returning the boolean ALL)
        3) 'C' - If used on an array, reverses the array
        4) 'r' - Now works on single integers
        5) The __repr__ method on types now more accurately represents the data
           encased in them   
        6) Added __add__ and __mul__ methods on types to accomodate sum and
           product
        7) Changed the output format of '#'
        8) Added MUCH better documentation

    Version 1.1:
      Added:
        1) 'z' - Push space character (JNum(32))
        2) 'Z' - Push line feed character (JNum(10))
        3) 'Y':
            Arr, Any - Push array of all indexes where an element appears
                       in an array

        4) Interpreter -C, changelog option

      Changed:
        1) Do and While no longer consume the test value to determine whether
           or not to continue looping

        2) Fixed dropif; it was dropping if the value was false instead of
           true

      Removed:
        1) Binary number syntax. May add back if actually needed somewhere in
           the future.

    Version 1.0:
      Initial release
"""			
		sys.exit(0)

	try:
		try:
			if args.inter:
				print "JAGL Interpreter Alpha V1.3 - Jan 2/2015"
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