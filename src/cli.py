
import argparse, sys
require taskfile

def main():
	d = Date()
	f = TaskFile("todolist.txt",d)
	name = sys.argv[1] if len(sys.argv)>1 else "today"
	print f.select(name,sys.argv[2:],Date()).tabulate()
	f.save()

exports["main"] = main