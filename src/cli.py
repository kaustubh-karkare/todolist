
import argparse, os, readline, sys
require date, taskfile, helptext

__dir__ = os.path.join(*os.path.split(__file__)[:-1]) \
	if os.path.basename(__file__)!=__file__ else "."

# Command Line Argument Validation

actions = "list add edit delete move pending done failed".split()
argerror = argparse.ArgumentTypeError
def action(z):
	(x, y) = z.split(":",1) if ":" in z else (z, None)
	if x in actions: return (x, y or "today")
	elif y is None: return ("list", x)
	else: raise Exception("Unknown Action")

def date(x): return Date("today") # development only

ap = argparse.ArgumentParser(description="A Command Line ToDoList Manager", add_help=False)
ap.add_argument("action", nargs="?", type=action, default="list")
ap.add_argument("data", nargs="*")
ap.add_argument("-h","--help", action="store_true", default=False)
ap.add_argument("-f","--file", default="./todolist.txt")
ap.add_argument("--date", type=date, default="today")
ap.add_argument("--nosave", action="store_true", default=False)

# User Interaction Functions

def confirm(msg="Are you sure?"):
	while True:
		x = raw_input(msg+" (yes/no) ")
		if x=="yes": return True
		elif x=="no": return False
	print
def prompt(prompt, prefill=""):
	readline.set_startup_hook(lambda: readline.insert_text(prefill))
	try:
		data = raw_input(prompt)
		print
		return data
	finally: readline.set_startup_hook()

# Convenience Functions

def __relocate(taskfile,task,name):
	if task.group:
		task.group.task_remove(task)
		taskfile.update(task.group)
	taskgroup = taskfile.group(name)
	if not taskgroup: return False
	taskgroup.task_add(task)
	task.group = taskgroup
	taskfile.update(taskgroup)
	return True

def __select(taskfile,name,args):
	taskgroup = taskfile.select(name,args.data)
	tasks = taskgroup.task_list()
	if len(tasks)==0:
		raise Exception("No Matching Task")
	if len(tasks)==1:
		return tasks[0]
	else:
		print taskgroup.tabulate(date=args.date, index=True)
		while True:
			index = prompt("Select Task by Index: ")
			try: task = tasks[int(index)]
			except ValueError, IndexError: continue
			return task

def __main():

	print

	args = ap.parse_args(sys.argv[1:])
	if args.help:
		print helptext
		sys.exit(0)

	taskfile = TaskFile(args.file,args.date)
	action, name = args.action
	line = " ".join(args.data)
	
	if action=="list":
		taskgroup = taskfile.select(name, args.data)
		print taskgroup.tabulate(date=args.date)

	elif action=="add":
		if line=="": raise Exception("Empty Task")
		
		task = Task(line,None,args.date)
		name = args.date.translate(name) or name
		if not __relocate(taskfile,task,name):
			raise Exception("Invalid Date")
		print task.group.tabulate(date=args.date)

		# in case of periodic tasks, is today included?
		temp = task.periodic(args.date, None)
		if temp:
			taskgroup = taskfile.group(args.date.str())
			temp.group = taskgroup
			taskgroup.task_add(temp)
			taskfile.update(taskgroup)

	else:

		task = __select(taskfile, name, args)
		if action in ("edit","delete","move"):
			print TaskGroup([task]).tabulate(date=args.date)

		if action=="edit":
			while True:
				line = prompt("Edit Task: ",str(task))
				if line!="": break
			task.update(line,args.date)
			taskfile.update(task.group)

		elif action=="delete":
			task.group.task_remove(task)
			taskfile.update(task.group)

		elif action=="move":
			while True:
				name = prompt("Enter Destination Date: ")
				try: group = taskfile.group(name)
				except: continue
				break
			__relocate(taskfile,task,group.name)

		elif action=="done":
			task.tag_remove("failed")
			task.tag_add("done")
			taskfile.update(task.group)

		elif action=="failed":
			task.tag_remove("done")
			task.tag_add("failed")
			taskfile.update(task.group)

		elif action=="pending":
			task.tag_remove("done")
			task.tag_remove("failed")

		else: raise Exception("Unknown Action")

		if action!="delete":
			print TaskGroup([task]).tabulate(date=args.date)
	
	if args.nosave:
		pass
	elif action=="list":
		taskfile.save()
	elif confirm():
		taskfile.save()
		print "Saved updates to file."
		print

def main():
	try:
		__main()
	except KeyboardInterrupt:
		print "^SIGINT\n"
		sys.exit(1)
	except Exception as e:
		print "Error:", e.message, "\n"

exports["main"] = main