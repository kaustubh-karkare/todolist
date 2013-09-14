
order = ["help","date","task","taskgroup"]

import argparse, datetime, os, subprocess, sys

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
			code += "def exports():\n\texports = {}\n"
			for line in f:
				if line.startswith("#!eof"): break
				elif line.strip()=="": continue
				elif line.startswith("import "):
					modules.extend( i.strip() for i in line[7:].split(",") )
				else: code += "\t"+line+("" if line.endswith("\n") else "\n")
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

	print now(), "Initial Build ...",
	build(args.target) # at least once
	print "done."

	if args.loop:

		import pyinotify

		events = {
			"IN_CREATE": "creation",
			"IN_MODIFY": "modification",
			"IN_DELETE": "deletion",
		}

		def handler(event):
			if not event.name.endswith(".py"): return
			print now(), "Rebuilding due to", events[event.maskname],
			print "of", event.name, "...",
			build(args.target)
			print "done."

		mask = reduce( (lambda x,y: x|y), (getattr(pyinotify,i) for i in events) )

		wm = pyinotify.WatchManager()
		notifier = pyinotify.Notifier(wm, handler)
		wm.add_watch(__dir__, mask, rec=True)
		notifier.loop()