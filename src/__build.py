
order = ["help","date","task","taskgroup"]

import argparse, datetime, os, sys
sys.dont_write_bytecode = True # prevent creation of *.pyc & *.pyo files

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) + os.sep

code_init = """#!/usr/bin/python
def define(scope):
	def actual(exports):
		scope.update(exports)
	return actual
define = define(vars())
"""

def build(target):
	target, modules, code = open(target,"w"), [], ""
	print >>target, code_init,
	for name in order:
		fname = __dir__ + name + ".py"
		if not os.path.isfile(fname): continue
		with open(fname) as f:
			# wrap the file contents within a function
			code += "def exports():\n\texports = {}\n"
			for line in f:
				# stop reading at pattern & skip blank lines
				if line.startswith("#!eof"): break
				elif line.strip()=="": continue
				# remember imported modules
				elif line.startswith("import "):
					modules.extend( i.strip() for i in line[7:].split(",") )
				# prevent premature return of wrapper function
				elif code.startswith("return "):
					raise SyntaxError("'return' outside function")
				# prefix \t & suffix \n to each line
				else: code += "\t"+line+("" if line.endswith("\n") else "\n")
			# update the global namespace with exports
			code += "\treturn exports\ndefine(exports())\n"
	if len(modules): print >>target, "import" , ", ".join(set(modules))
	print >>target, code
	target.close()

def now():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S #")

if __name__=="__main__":

	ap = argparse.ArgumentParser()
	ap.add_argument("target", help="The target file to which all code will be written.")
	ap.add_argument("--loop", action="store_true", help="Starts an infinite loop to continuously watch the source directory and rebuild when changes are detected.")
	args = ap.parse_args(sys.argv[1:])

	build(args.target) # at least once
	print now(), "Initial Build"

	if args.loop:

		import __watch as watch

		@watch.debounce(1,1)
		def handler(*events):

			if any(e.path.endswith(".py") for e in events \
				if not os.path.basename(e.path).startswith("__")):

				build(args.target)
				files = (os.path.relpath(i,__dir__) for i in set(e.path for e in events))
				print now(), "Rebuilt due to changes affecting", ", ".join(files)

		watch.start(__dir__,"create modify delete".split(),handler)
