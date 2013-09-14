
import argparse, datetime, os, sys

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) + os.sep
order = ["help","date","task","taskgroup"]
modules = ["datetime","re"]

def build(target):
	target = open(target,"w")
	print >>target, "#!/usr/bin/python\n\nimport "+",".join(modules)+"\n"
	for name in order:
		fname = __dir__ + name + ".py"
		if not os.path.isfile(fname): continue
		with open(fname) as f:
			print >>target, f.read().split("\n#!eof\n",1)[0]
	target.close()

if __name__=="__main__":

	ap = argparse.ArgumentParser()
	ap.add_argument("--loop", action="store_true", help="Starts an infinite loop to continuously watch the source directory and rebuild when changes are detected.")
	ap.add_argument("target", help="The target file to which all code will be written.")
	args = ap.parse_args(sys.argv[1:])

	build(args.target) # at least once

	if args.loop:

		import pyinotify

		events = {
			"IN_CREATE": "creation",
			"IN_MODIFY": "modification",
			"IN_DELETE": "deletion",
		}

		def handler(event):
			if not event.name.endswith(".py"): return
			print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "#",
			print "Rebuilt due to", events[event.maskname], "of", event.name
			build(args.target)

		mask = reduce( (lambda x,y: x|y), (getattr(pyinotify,i) for i in events) )

		wm = pyinotify.WatchManager()
		notifier = pyinotify.Notifier(wm, handler)
		wm.add_watch(__dir__, mask, rec=True)
		notifier.loop()