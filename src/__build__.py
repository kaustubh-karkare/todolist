#!/usr/bin/python

order = ["help","date","task","taskgroup"]

import argparse, datetime, os, subprocess, sys, threading

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) + os.sep

code_init = """#!/usr/bin/python
def define(scope):
	def actual(exports):
		for key in exports:
			scope[key] = exports[key]
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

def debounce(wait,collect=False):
	def decorator(fn):
		def debounced(*_args, **_kwargs):
			# javascript/arguments.caller
			self = debounced
			# cancel waiting thread
			if self.lock: self.thread.join()
			else: self.thread.cancel()
			# collect function arguments
			if not collect: self.args, self.kwargs = _args, _kwargs
			else: self.args.extend(_args), self.kwargs.update(_kwargs)
			# define and launch thread
			def wrapper():
				self.lock = True
				fn(*self.args, **self.kwargs)
				self.args, self.kwargs = [], {}
				self.lock = False
			self.thread = threading.Timer(wait, wrapper)
			self.thread.start()
		# initialize thread, lock & collections
		debounced.lock = False
		debounced.thread = threading.Timer(0, debounced)
		if collect: debounced.args, debounced.kwargs = [], {}
		return debounced
	return decorator

if __name__=="__main__":

	ap = argparse.ArgumentParser()
	ap.add_argument("target", help="The target file to which all code will be written.")
	ap.add_argument("--loop", action="store_true", help="Starts an infinite loop to continuously watch the source directory and rebuild when changes are detected.")
	args = ap.parse_args(sys.argv[1:])

	build(args.target) # at least once
	print now(), "Initial Build"

	if args.loop:

		import pyinotify

		events = "IN_CREATE IN_MODIFY IN_DELETE".split()

		@debounce(1,1)
		def handler(*events):
			if any(e.name.endswith(".py") for e in events):
				build(args.target)
				print now(), "Rebuilt", "("+", ".join(set(e.name for e in events))+")"

		mask = reduce( (lambda x,y: x|y), (getattr(pyinotify,i) for i in events) )

		wm = pyinotify.WatchManager()
		notifier = pyinotify.Notifier(wm, handler)
		wm.add_watch(__dir__, mask, rec=True)
		notifier.loop()