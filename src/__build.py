
import argparse, copy, datetime, os, sys

# prevent creation of *.pyc & *.pyo files
sys.dont_write_bytecode = True

# obtain relative path to container directory
__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
	if os.path.basename(__file__)!=__file__ else "."

def __toposort(graph,preserve=True):
	# Topological Sort, graph = dict of lists
	if preserve: graph = copy.deepcopy(graph)
	result = []
	while graph: # not empty
		change = False
		for key in graph:
			if len(graph[key])==0:
				del graph[key]
				for key2 in graph:
					if key in graph[key2]:
						graph[key2].remove(key)
				result.append(key)
				change = True
				break
		if not change:
			raise Exception("Cyclic Dependency!")
	return result

__prefix = """#!/usr/bin/python
def define(scope):
	def actual(exports):
		scope.update(exports)
	return actual
define = define(vars())
"""

__suffix = """
if "main" in dir() and "__call__" in dir(main): main()
"""

def __build(dirpath,target):

	target, modules = open(target,"w"), []
	depends, code = {}, {}
	print >>target, __prefix,

	for fname in os.listdir(dirpath):
		fpath = os.path.join(dirpath,fname)
		# skip all hidden, non-python & non-existant files
		if fname.startswith("__") or \
			not fname.endswith(".py") or \
			not os.path.isfile(fpath):
			continue
		# for the require statement, which uses filenames (with extension)
		name = fname[:-3]

		with open(fpath) as f:
			# initialize the dependencies list
			depends[name] = []
			# wrap the file contents within a function
			code[name] = "def exports():\n\texports = {}\n"
			for line in f:
				# stop reading at pattern & skip blank & comment lines
				if line.startswith("#!eof"): break
				elif line.strip()=="": continue
				elif line.strip().startswith("#"): continue
				# remember imported external modules
				elif line.startswith("import "):
					modules.extend( i.strip() for i in line[7:].split(",") )
				# remember required internal modules
				elif line.startswith("require "):
					depends[name].extend( i.strip() for i in line[8:].split(",") )
				# prevent premature return of wrapper function
				elif line.startswith("return "):
					raise SyntaxError("'return' outside function")
				# prefix \t & suffix \n to each line
				else: code[name] += "\t"+line+("" if line.endswith("\n") else "\n")
			# update the global namespace with exports
			code[name] += "\treturn exports\ndefine(exports())\n"

	if len(modules): print >>target, "import" , ", ".join(set(modules))
	print >>target, "".join(code[name] for name in __toposort(depends,0)), __suffix
	target.close()

def __now():
	return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S #")

if __name__=="__main__":

	ap = argparse.ArgumentParser()
	ap.add_argument("target", help="The target file to which all code will be written.")
	ap.add_argument("--loop", action="store_true", help="Starts an infinite loop to continuously watch the source directory and rebuild when changes are detected.")
	args = ap.parse_args(sys.argv[1:])

	build = lambda: __build(__dir__, args.target)
	build() # at least once

	if args.loop:

		print __now(), "Initial Build"

		import __watch

		@__watch.debounce(1,1)
		def handler(*events):

			if any(e.path.endswith(".py") for e in events \
				if not os.path.basename(e.path).startswith("__")):

				build()
				files = (os.path.relpath(i,__dir__) for i in set(e.path for e in events))
				print __now(), "Rebuilt due to changes affecting", ", ".join(files)

		__watch.start(__dir__,"create modify delete".split(),handler)
