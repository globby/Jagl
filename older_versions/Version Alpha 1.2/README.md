Jagl - Just A Golfing Language
====

About
----

Jagl is a stack based programming language inspired by [Golfscript][1] and [Pyth][2]. The underlying framework was designed to be easy to expand upon.

Following is a brief documentation. For a full reference of functions, refer to **Documentation V1.2.pdf**


Types
----
Jagl has four types: Numeric, Array, Block, and Function.

#### Numeric
Numeric types can contain either floating point or integer numbers, and have a variety of syntaxes:

**Decimal** - `1`, `1.0`, `-.4`, `2.`

**Scientific** - `1e6`, `1.8e-8`

**Octal** - `70o`

**Hexadecimal** - `8Fx`

#### Arrays
Arrays can contain any combination of types, and are created using normal brackets, with each item separated by a space (if needed to separate tokens for parsing). Example:

```(1 2 (3 4 5)(6 7) 8 "String" {2+})```

Strings are represented by an array of their ascii values. Unicode is not yet supported. Strings have a syntactic sugar for definition, using quotes (for a normal string) or ticks (for strings with escape sequences).

`"string\n" -> (115 116 114 105 110 103 92 110) or (s t r i n g \\ n)`

`'string\n' -> (115 116 114 105 110 103 10)     or (s t r i n g \n)`

#### Blocks
The Jagl Blocks are analogous with the code blocks found in Golfscript. They contain a certain order of tokens which can be evaluated at some other point, through the use of functions. Their definition is with curly brackets

`{2 4+}`

#### Functions
Functions are simply names which do a set of operations on the stack, or items on the stack. Some help with program flow, and many work differently depending on what types are at the top of the stack.

Files
----
**jaglt.py** - Contains the Jagl type classes (Numeric, Array, Block)

**jaglk.py** - Contains the tokenizer and supporting functions, and regexes

**jaglf.py** - Contains all of the functions currently defined

**jagli.py** - Contains the interactive interpreter, along with the runOn method (imported from the other scripts)

Using the Interpreter
----

To try out Jagl, download the repository and examples, and try them out. The help for the interpreter is as follows:

    usage: jagli.py [-h] [-v] [-i] [-c CODE] [filename]
    JAGL (Just A Golfing Language) Interpreter
    positional arguments:
      filename        Filename
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -i, --inter           run the interactive interpreter (repl)
      -c CODE, --code CODE  execute code from the command line
      -C, --changelog       print changelog

[1]: http://www.golfscript.com/golfscript/
[2]: https://github.com/isaacg1/pyth

Conclusion
----
Please note that the language is still in the Alpha stage, and may have bugs. If you encouter one, please open an issue on the github repo. Happy code-golfing!


Changelog
----
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
        4) The __repr__ method on types now more accurately represents the data
           encased in them   
        5) Added __add__ and __mul__ methods on types to accomodate sum and
           product
        6) Changed the output format of '#'
        7) Added MUCH better documentation

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